import typing
from nodnod.node import Node, Injection, is_type, InjectionHook
from nodnod.agent.event_loop.agent import EventLoopAgent, Agent
from nodnod.value import Value
from nodnod.scope import Scope
from nodnod.utils.create_node import create_node
from nodnod.utils.resolve_signature import resolve_signature
from nodnod.utils.misc import reverse_dict
import fntypes


def collect_externals_hook(node: type[Node], dep_name: str, dep_type: type[typing.Any]) -> fntypes.Pulse[str]:
    if is_type(dep_type, Injection):
        return fntypes.Error("Injection is internal")
    
    if not hasattr(node, "__externals__"):
        setattr(node, "__externals__", [])
    
    getattr(node, "__externals__").append(dep_name)
    return fntypes.Ok()


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
        if external_name in externals:
            compose_kwargs[external_name] = externals_value[external_name]
    
    return cls.__compose__(**compose_kwargs)


def create_node_from_function(
    func: typing.Callable[..., typing.Any], 
) -> type[Node]:
    node = create_node(
        f"Node:{func.__name__}",
        Node,
        bases=(),
        namespace={"__compose__": func, "__module__": func.__module__},
        injection_hooks=(collect_externals_hook,),
    )
    node.__injections__.add(Externals)
    node.__initialize__ = initialize_node_with_externals  # type: ignore

    names = {}

    for dep_type, dep_name in reverse_dict(resolve_signature(func).merge()).items():
        if is_type(dep_type, Injection):
            dep_type = typing.get_args(dep_type)[0]
        names[dep_type] = dep_name

    setattr(node, "__names__", names)
    return node


def create_agent_from_node[T: Agent](node: type[Node], agent_cls: type[T] = EventLoopAgent) -> T:
    return agent_cls.build({node})


def inject_externals(
    scope: Scope, 
    externals: dict[str, typing.Any],
) -> None:
    scope.inject(Externals, Externals(externals))


__all__ = ("create_node_from_function", "create_agent_from_node", "inject_externals")
