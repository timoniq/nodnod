import typing

import fntypes

from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature

if typing.TYPE_CHECKING:
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]

@classmethod
def dummy_compose[Cls](cls: type[Cls]) -> Cls:
    return cls()


class Node[T = typing.Any]:    
    __dependencies__: set[type["Node"]] = None # type: ignore
    __injections__: set[type] = None # type: ignore
    __initialize__: typing.Callable[[set["Value"]], ComposeResponse[T]] = None # type: ignore
    __type__: type = None  # type: ignore
    __compose__: typing.Callable[..., ComposeResponse[T]] = dummy_compose

    def __init_subclass__(cls, abstract: bool = False) -> None:
        from nodnod.builder.build_queue import build_queue
        from nodnod.interface.is_node import is_node
        from nodnod.interface.option_node import create_option_node
        from nodnod.interface.union_node import create_union_node, is_union
        from nodnod.interface.create_result_node import create_result_node

        if not abstract and not cls.__initialize__:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(cls.__compose__, ignore_bound_parameters=True)

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type]()

            for dep_type in signature.get_all_types():
                dep_origin_type = typing.get_origin(dep_type) or dep_type

                if is_node(dep_origin_type):
                    dependency_nodes.add(dep_origin_type)
                elif is_union(dep_origin_type):
                    dependency_nodes.add(create_union_node(dep_type))
                elif dep_origin_type is fntypes.Option:
                    dependency_nodes.add(create_option_node(dep_type))
                elif dep_origin_type is fntypes.Result:
                    dependency_nodes.add(create_result_node(dep_type))
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
                    fntypes.F[set["Value"]]()
                    .then(
                        lambda values: (
                            print(values) or [],
                            {kwargs_names_by_type[value.cls]: value.__unbox__() for value in values if value.cls in kwargs_names_by_type}
                        )
                    ).then(
                        lambda params: cls.__compose__(*params[0], **params[1])
                    )
                )
            
            if cls.__type__ is None:
                cls.__type__ = cls
            
            setattr(cls, "__traverse__", build_queue(cls, []))
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__}>"


type Queue = list[type[Node]]


__all__ = ("Node", "Queue")
