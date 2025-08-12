import typing

import fntypes

from nodnod.utils.is_type import is_type
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature
from nodnod.utils.type_args import get_type_args, get_type_parameters

if typing.TYPE_CHECKING:
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]

TYPEVARS_TYPES: typing.Final = frozenset((typing.TypeVar, typing.ParamSpec, typing.TypeVarTuple))


@classmethod
def dummy_compose[Cls](cls: type[Cls]) -> Cls:
    return cls()


class Node[T = typing.Any]:    
    __dependencies__: set[type["Node"]] = None # type: ignore
    __injections__: set[type[typing.Any]] = None # type: ignore
    __initialize__: typing.Callable[[set["Value[typing.Any]"]], ComposeResponse[T]] = None # type: ignore
    __type__: type[typing.Any] = None  # type: ignore
    __compose__: typing.Callable[..., ComposeResponse[T]] = dummy_compose

    def __init_subclass__(cls, abstract: bool = False) -> None:
        from nodnod.builder.build_queue import build_queue
        from nodnod.interface.create_result_node import create_result_node
        from nodnod.interface.generic import is_generic_node
        from nodnod.interface.option_node import create_option_node
        from nodnod.interface.union_node import create_union_node, is_union
        from nodnod.utils.create_node import create_node

        if not abstract and not cls.__initialize__:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(cls.__compose__, ignore_bound_parameters=True)

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type]()

            for dep_type in signature.get_all_types():
                if is_type(dep_type, Node):
                    dependency_nodes.add(dep_type)
                elif is_union(dep_type):
                    dependency_nodes.add(create_union_node(dep_type))
                elif is_type(dep_type, fntypes.Option):
                    dependency_nodes.add(create_option_node(dep_type))
                elif is_type(dep_type, fntypes.Result):
                    dependency_nodes.add(create_result_node(dep_type))
                elif is_type(dep_type, type) and is_type(type_arg := get_type_args(dep_type).unwrap()[0], TYPEVARS_TYPES):
                    type_arg_node = create_node(
                        name=f"TypeArgNode:{type_arg.__name__}",
                        base_node=Node,
                        bases=(),
                        namespace=dict(
                            __type__=dep_type,
                            __initialize__=lambda values: get_type_parameters(cls)[type_arg]
                        )
                    )
                    dependency_nodes.add(type_arg_node)
                else:
                    injected_types.add(dep_type)

            if cls.__dependencies__ is None:
                cls.__dependencies__ = dependency_nodes

            if cls.__injections__ is None:
                cls.__injections__ = injected_types

            if cls.__initialize__ is None:
                # If not set, prepare the dependencies distribution
                kwargs_names_by_type = reverse_dict(signature.kwargs | signature.args)

                cls.__initialize__ = (
                    fntypes.F[set["Value[typing.Any]"]]()
                    .then(
                        lambda values: (
                            {
                                kwargs_names_by_type[value.cls]: value.unbox() 
                                for value in values 
                                if value.cls in kwargs_names_by_type
                            }
                        )
                    ).then(
                        lambda params: cls.__compose__(**params)
                    )
                )
            
            if cls.__type__ is None:
                cls.__type__ = cls

            setattr(cls, "__traverse__", build_queue(cls, []))
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__}>"


type Queue = list[type[Node]]


__all__ = ("Node", "Queue")
