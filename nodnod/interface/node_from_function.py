import typing

import kungfu
from typing_extensions import ForwardRef

from nodnod.builder.build_queue import build_queue
from nodnod.error import NodeBuildError, NodeError
from nodnod.interface.composable import Composable
from nodnod.interface.is_node import is_node
from nodnod.node import FORWARD_REF_REQUESTS, ComposeResponse, Node, initialize_forward_refs, is_injection
from nodnod.utils.call import call_with_context
from nodnod.utils.create_node import create_node, create_node_from_composable
from nodnod.utils.injection import get_injection_type
from nodnod.utils.is_type import is_type
from nodnod.value import Value

type LikeNode = typing.Any

NODE_NAMESPACE: typing.Final = frozenset({k for k in Node.__dict__ if k not in type(Node).__dict__})


def collect_externals_and_names_hook(
    node: type[Node],
    dep_name: str,
    dep_type: typing.Any,
) -> kungfu.Pulse[str]:
    if is_injection(dep_type):
        if not hasattr(node, "__internals__"):
            setattr(node, "__internals__", {})

        getattr(node, "__internals__")[dep_name] = get_injection_type(dep_type, owner=node.__compose__)
        return kungfu.Ok()

    if not hasattr(node, "__externals__"):
        setattr(node, "__externals__", set())

    getattr(node, "__externals__").add(dep_name)
    return kungfu.Ok()


@classmethod
def initialize_node_with_externals(cls: type[Node], values: set[Value]) -> ComposeResponse[typing.Any]:
    externals: typing.Iterable[str] = getattr(cls, "__externals__", ())
    names: typing.Mapping[typing.Any, str] = getattr(cls, "__names__", {})
    compose_kwargs: dict[str, typing.Any] = {}
    externals_value: Externals = Externals()

    for value in values:
        if value.cls is Externals:
            externals_value = value.value
        elif value.cls in names:
            compose_kwargs[names[value.cls]] = value.value

    for external_name in externals:
        if external_name in externals_value:
            compose_kwargs[external_name] = externals_value[external_name]

    return (
        call_with_context(cls.__compose__, compose_kwargs)
        .map_err(
            lambda name: NodeError(
                f"Name `{name}` was not found. Inject it through one of "
                "`Injection[T]` or `Externals`, or, if it is a `Node` "
                "dependency, check its type.",
            )
        )
        .unwrap()
    )


def _normalize_dependencies(dependencies: typing.Mapping[str, LikeNode] | None) -> dict[str, typing.Any]:
    normalized: dict[str, typing.Any] = {}
    for dep_name, dep in (dependencies or {}).items():
        if is_node(dep):
            normalized[dep_name] = dep
        elif is_type(dep, Composable):
            normalized[dep_name] = create_node_from_composable(dep)
        else:
            # Do not silently drop a non-Composable dependency (which would make the parameter
            # quietly become an external); the user's explicit intent should fail loudly.
            raise NodeBuildError(
                f"Dependency `{dep_name}` passed to `create_node_from_function` must be a `Node` "
                f"or a `Composable` (a class with `__compose__`), got `{dep!r}`.",
            )
    return normalized


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
        raise TypeError(f"`func` must be kind of function, got `{repr(func if isinstance(func, type) else type(func))}`.")

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
        injection_hooks=(collect_externals_and_names_hook,),
    )
    # Pass the new node as `own_node` so only ITS forward-ref requests may be marked external;
    # a foreign class node waiting on the same name (collision) is preserved and resolves later.
    if forward_refs is not None:
        initialize_forward_refs(forward_refs, is_from_function=True, own_node=node)
    else:
        initialize_forward_refs(getattr(func, "__globals__", {}), is_from_function=True, own_node=node)

    if node.__compose_names_by_type__ is None:
        node.__init_subclass__(injection_hooks=(collect_externals_and_names_hook,))

    dependencies = _normalize_dependencies(dependencies)
    names = _NameDict()
    externals: set[str] = getattr(node, "__externals__", set())
    internals: dict[str, typing.Any] = getattr(node, "__internals__", {})

    for dep_type, dep_name in node.__compose_names_by_type__.items():
        if dep_name in dependencies:
            # Replace the dependency wired for this parameter.

            new_dependency = dependencies[dep_name]
            if is_node(dep_type):
                old_dependency = next(
                    (dep for dep in node.__dependencies__ if dep_type in (dep, dep.__type__)),
                    None,
                )
            else:
                # The original annotation was a Composable: node.py already synthesized a node
                # for it and added it to __dependencies__. Locate that synthesized node so it is
                # removed too, otherwise the replaced dependency lingers as a broken orphan.
                synthesized = create_node_from_composable(dep_type) if is_type(dep_type, Composable) else None
                old_dependency = synthesized if synthesized in node.__dependencies__ else None

            if old_dependency is not None:
                node.__dependencies__.remove(old_dependency)

            if dep_name in internals:
                del internals[dep_name]

            if dep_name in externals:
                externals.remove(dep_name)

            node.__dependencies__.add(new_dependency)
            names[new_dependency.__type__] = dep_name
            continue

        if dep_name in internals:
            # Add an internal dependency (aka `Injection[T]`)
            names[internals[dep_name]] = dep_name

        elif dep_name not in externals:
            # Add a composable dependency
            names[dep_type] = dep_name

        # Otherwise, the dependency is external, i.e., already collected
        # using `collect_externals_and_names_hook`.

    if hasattr(node, "__internals__"):
        delattr(node, "__internals__")

    setattr(node, "__externals__", externals)
    # Only require an Externals value when the function actually has external parameters, so a
    # node with no externals (e.g. a zero-arg function) composes via compose_one without an
    # explicitly injected empty Externals.
    injections: set[typing.Any] = {*internals.values()}
    if externals:
        injections.add(Externals)
    setattr(node, "__injections__", injections)
    setattr(node, "__names__", names)
    setattr(node, "__traverse__", build_queue(node, list()))
    setattr(node, "__initialize__", initialize_node_with_externals)
    return node


class Externals(dict[str, typing.Any]):
    pass


class ExternalDependency:
    def __init__(self, name: str) -> None:
        self.name = name

    def __str__(self) -> str:
        return self.name

    def __hash__(self) -> int:
        return hash(self.name)


class _NameDict(dict[typing.Any, str]):
    def __getitem__(self, key: typing.Any, /) -> str:
        if key in self:
            return super().__getitem__(key)

        if isinstance(key, ForwardRef) and (name := self.get(key.__forward_arg__)):
            return name

        raise KeyError(key)


__all__ = ("Externals", "create_node_from_function")
