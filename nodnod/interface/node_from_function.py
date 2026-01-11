import typing

import kungfu

from nodnod.agent.event_loop.agent import Agent, EventLoopAgent
from nodnod.node import Injection, Node, initialize_forward_refs, is_type
from nodnod.scope import Scope
from nodnod.utils.call import call_with_context
from nodnod.utils.create_node import create_node
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature
from nodnod.value import Value


def collect_externals_hook(node: type[Node], dep_name: str, dep_type: type[typing.Any]) -> kungfu.Pulse[str]:
    if is_type(dep_type, Injection):
        return kungfu.Error("Injection is internal")

    if not hasattr(node, "__externals__"):
        setattr(node, "__externals__", [])

    getattr(node, "__externals__").append(dep_name)
    return kungfu.Ok()


class Externals(dict[str, typing.Any]):
    pass


@classmethod
def initialize_node_with_externals(cls, values: set[Value[typing.Any]]) -> typing.Any:
    externals = getattr(cls, "__externals__", {})
    names = getattr(cls, "__names__", {})
    compose_kwargs = {}

    externals_value: Externals = Externals()

    for value in values:
        if value.cls is Externals:
            externals_value = value.value
        else:
            compose_kwargs[names[value.cls]] = value.value

    for external_name in externals:
        if external_name in externals_value:
            compose_kwargs[external_name] = externals_value[external_name]

    return call_with_context(cls.__compose__, compose_kwargs)


class _NameDict(dict[typing.Any, str]):
    def __getitem__(self, key: typing.Any) -> str:
        if key in self:
            return super().__getitem__(key)

        if (name := self.get(key.__name__)) or (name := self.get(repr(key))):
            return name

        raise KeyError(key)


def create_node_from_function(
    func: typing.Callable[..., typing.Any],
    *,
    forward_refs: dict[str, typing.Any] | None = None,
    dependencies: typing.Mapping[str, type[Node]] | None = None,
    module: str | None = None,
) -> type[Node]:
    node = create_node(
        f"Node:{func.__name__}",
        Node,
        bases=(),
        namespace={"__compose__": func, "__module__": module or func.__module__},
        injection_hooks=(collect_externals_hook,),
    )

    if forward_refs is not None:
        initialize_forward_refs(forward_refs, is_from_function=True)
    else:
        initialize_forward_refs(getattr(func, "__globals__", {}), is_from_function=True)

    if node.__injections__ is None:
        node.__init_subclass__(injection_hooks=(collect_externals_hook,))

    node.__injections__.add(Externals)

    sig_annotations = reverse_dict(resolve_signature(func).merge())
    names = _NameDict()

    for dep_type, dep_name in sig_annotations.items():
        if is_type(dep_type, Injection):
            dep_type = typing.get_args(dep_type)[0]

        if isinstance(dep_type, typing.ForwardRef):
            dep_type = dep_type.__forward_arg__

        names[dep_type] = dep_name

    if dependencies and node.__dependencies__:
        reversed_names = reverse_dict(names)

        for dep_type in node.__dependencies__:
            if (
                hasattr(dep_type, "__type__")
                and dep_type.__type__ in sig_annotations
                and sig_annotations[dep_type.__type__] in dependencies
            ):
                node.__dependencies__.remove(dep_type)
                node.__dependencies__.add(dependencies[sig_annotations[dep_type.__type__]])
                names.pop(reversed_names[sig_annotations[dep_type.__type__]], None)
                names[dependencies[sig_annotations[dep_type.__type__]].__type__] = sig_annotations[dep_type.__type__]

    node.__initialize__ = initialize_node_with_externals  # type: ignore
    setattr(node, "__names__", names)
    return node


def create_agent_from_node[T: Agent](node: type[Node], agent_cls: type[T] = EventLoopAgent) -> T:
    return agent_cls.build({node})


def inject_externals(
    scope: Scope,
    externals: dict[str, typing.Any],
) -> None:
    scope.inject(Externals, Externals(externals))


__all__ = ("create_agent_from_node", "create_node_from_function", "inject_externals")
