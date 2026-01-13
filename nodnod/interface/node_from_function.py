import typing

import kungfu
from typing_extensions import ForwardRef

from nodnod.builder.build_queue import build_queue
from nodnod.error import NodeError
from nodnod.interface.is_node import is_node
from nodnod.node import ComposeResponse, Injection, Node, initialize_forward_refs, is_type
from nodnod.utils.call import call_with_context
from nodnod.utils.create_node import create_node
from nodnod.utils.injection import get_injection_type
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature
from nodnod.value import Value

type LikeNode = typing.Any

NODE_NAMESPACE: typing.Final = frozenset({k for k in Node.__dict__ if k not in type(Node).__dict__})


def collect_externals_hook(
    node: type[Node],
    dep_name: str,
    dep_type: typing.Any,
) -> kungfu.Pulse[str]:
    if is_type(dep_type, Injection):
        return kungfu.Error("Injection is internal.")

    if not hasattr(node, "__externals__"):
        setattr(node, "__externals__", set())

    getattr(node, "__externals__").add(dep_name)
    return kungfu.Ok()


@classmethod
def initialize_node_with_externals(cls: type[Node], values: set[Value]) -> ComposeResponse[typing.Any]:
    externals: typing.Iterable[str] = getattr(cls, "__externals__", ())
    names: dict[typing.Any, str] = getattr(cls, "__names__", {})
    compose_kwargs: dict[str, typing.Any] = {}
    externals_value: Externals = Externals()

    for value in values:
        if value.cls is Externals:
            externals_value = value.value
        else:
            compose_kwargs[names[value.cls]] = value.value

    for external_name in externals:
        if external_name in externals_value:
            compose_kwargs[external_name] = externals_value[external_name]

    try:
        return call_with_context(cls.__compose__, compose_kwargs)
    except KeyError as error:
        raise NodeError(
            f"`{error.args[0]}` was not found in the externals. Inject it through `Externals`, "
            "or, if it is a `Node` dependency, check its type.",
        ) from None


def create_node_from_function(
    func: typing.Callable[..., typing.Any],
    *,
    forward_refs: dict[str, typing.Any] | None = None,
    dependencies: typing.Mapping[str, LikeNode] | None = None,
    module: str | None = None,
    bases: tuple[typing.Any, ...] = (),
    namespace: typing.Mapping[str, typing.Any] | None = None,
    prohibit_intersaction_with_node_namespace: bool = True,
) -> type[Node]:
    if not callable(func):
        raise TypeError(f"`func` must be kind of function, got `{type(func)}`.")

    node_name = (
        getattr(func.__code__, "co_qualname", None)
        if hasattr(func, "__code__")
        else getattr(func, "__qualname__", None)
    )
    namespace = dict(namespace) if namespace else {}

    if prohibit_intersaction_with_node_namespace:
        namespace = {k: v for k, v in namespace.items() if k not in NODE_NAMESPACE}

    node = create_node(
        f"Node:{node_name or getattr(func, '__name__', '<function>')}",
        Node,
        bases=bases,
        namespace={"__compose__": func, "__module__": module or getattr(func, "__module__", "<module>")} | namespace,
        injection_hooks=(collect_externals_hook,),
        is_from_function=True,
    )

    if forward_refs is not None:
        initialize_forward_refs(forward_refs, is_from_function=True)
    else:
        initialize_forward_refs(getattr(func, "__globals__", {}), is_from_function=True)

    if node.__injections__ is None:
        node.__init_subclass__(injection_hooks=(collect_externals_hook,), is_from_function=True)

    node.__injections__.add(Externals)

    sig_annotations = reverse_dict(resolve_signature(func).merge())
    names = _NameDict()
    dependencies = {dep_name: dep for dep_name, dep in dependencies.items() if is_node(dep)} if dependencies else {}
    externals: set[str] = getattr(node, "__externals__", set())

    for dep_type, dep_name in sig_annotations.items():
        if dep_name in dependencies:
            new_dependency = dependencies[dep_name]
            old_dependency = next((dep for dep in node.__dependencies__ if dep.__type__ is dep_type), None)

            if old_dependency is not None:
                node.__dependencies__.remove(old_dependency)

            if dep_name in externals:
                externals.remove(dep_name)

            node.__dependencies__.add(new_dependency)
            names[new_dependency.__type__] = dep_name
            continue

        if is_type(dep_type, Injection):
            dep_type = get_injection_type(dep_type, owner=func)

        if isinstance(dep_type, ForwardRef):
            dep_type = dep_type.__forward_arg__

        names[dep_type] = dep_name

    setattr(node, "__names__", names)
    setattr(node, "__traverse__", build_queue(node, list()))
    setattr(node, "__initialize__", initialize_node_with_externals)
    return node


class Externals(dict[str, typing.Any]):
    pass


class _NameDict(dict[typing.Any, str]):
    def __getitem__(self, key: typing.Any, /) -> str:
        if key in self:
            return super().__getitem__(key)

        if isinstance(key, ForwardRef) and (name := self.get(key.__forward_arg__)):
            return name

        raise KeyError(key)


__all__ = ("Externals", "create_node_from_function")
