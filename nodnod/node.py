from nodnod.utils.resolve_signature import resolve_signature
from nodnod.utils.misc import reverse_dict
import fntypes
import typing


if typing.TYPE_CHECKING:
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]


class Node[T = typing.Any]:    
    __dependencies__: set[type["Node"]] = None # type: ignore
    __injected_types__: set[type] = None # type: ignore
    __bound_compose__: typing.Callable[[set["Value"]], ComposeResponse[T]] = None # type: ignore

    def __init_subclass__(cls, abstract: bool = False) -> None:
        from nodnod.builder.build_queue import build_queue

        if not abstract:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(cls.__compose__, ignore_bound_parameters=True)

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type]()

            for dep_type in signature.get_all_types():
                if issubclass(dep_type, Node):
                    dependency_nodes.add(dep_type)
                else:
                    injected_types.add(dep_type)

            if cls.__dependencies__ is None:
                cls.__dependencies__ = dependency_nodes

            if cls.__injected_types__ is None:
                cls.__injected_types__ = injected_types

            if cls.__bound_compose__ is None:
                # If not set, prepare the dependencies distribution
                kwargs_names_by_type = reverse_dict(signature.kwargs | signature.args)

                cls.__bound_compose__ = (
                    fntypes.F[set["Value"]]()
                    .then(
                        lambda values: (
                            [],
                            {kwargs_names_by_type[value.node_cls]: value.__unbox__() for value in values if value.node_cls in kwargs_names_by_type}
                        )
                    ).then(
                        lambda params: cls.__compose__(*params[0], **params[1])
                    )
                )
            
            setattr(cls, "__traverse__", build_queue(cls, []))
    
    @classmethod
    def __compose__(cls, *args, **kwargs) -> ComposeResponse[T]:
        ...
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__}>"


type Queue = list[type[Node]]
