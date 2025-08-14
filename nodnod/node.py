import typing

import fntypes
import collections

from nodnod.error import NodeBuildError
from nodnod.utils.is_type import is_type
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature

if typing.TYPE_CHECKING:
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]
type Queue = list[type[Node]]


@classmethod
def dummy_compose[Cls](cls: type[Cls]) -> Cls:
    return cls()


FORWARD_REF_REQUESTS = collections.defaultdict(list["type[Node]"])
INITIALIZED_FORWARD_REFS = {}

class Node[T = typing.Any]:    
    __dependencies__: set[type["Node"]] = None # type: ignore
    __injections__: set[type[typing.Any]] = None # type: ignore
    __initialize__: typing.Callable[[set["Value[typing.Any]"]], ComposeResponse[T]] = None # type: ignore
    __type__: type[typing.Any] = None  # type: ignore
    __compose__: typing.Callable[..., ComposeResponse[T]] = dummy_compose

    def __init_subclass__(
        cls, 
        abstract: bool = False,
    ) -> None:
        from nodnod.builder.build_queue import build_queue
        from nodnod.interface.create_result_node import create_result_node
        from nodnod.interface.generic import create_type_arg_node
        from nodnod.interface.option_node import create_option_node
        from nodnod.interface.union_node import create_union_node, is_union

        if not abstract and not cls.__initialize__:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(cls.__compose__, ignore_bound_parameters=True)
            all_args = signature.args | signature.kwargs

            # Search for forward refs and form requests to initialize node when forward ref node is initialized
            # or fill forward refs if node is being initialized
            for name, dep_type in all_args.items():
                if isinstance(dep_type, typing.ForwardRef):
                    if (ref := INITIALIZED_FORWARD_REFS.get(dep_type.__forward_arg__)):
                        all_args[name] = ref
                        continue
                    FORWARD_REF_REQUESTS[dep_type.__forward_arg__].append(cls)
                    return
                
            all_args = typing.cast(dict[str, type], all_args)

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type]()

            for dep_type in all_args.values():
                if is_type(dep_type, Node):
                    dependency_nodes.add(dep_type)
                elif is_union(dep_type):
                    dependency_nodes.add(create_union_node(dep_type))
                elif is_type(dep_type, fntypes.Option):
                    dependency_nodes.add(create_option_node(dep_type))
                elif is_type(dep_type, fntypes.Result):
                    dependency_nodes.add(create_result_node(dep_type))
                elif is_type(dep_type, type):
                    args = typing.get_args(dep_type)
                    if not args:
                        raise NodeBuildError(f"Expected `type` with type argument, got `{dep_type!r}`.")
                    
                    if is_type(type(args[0]), typing.TypeVar):
                        type_arg_node = create_type_arg_node(cls, args[0], dep_type)
                    else:
                        raise NotImplementedError("Only type with type var is supported.")

                    dependency_nodes.add(type_arg_node)
                else:
                    injected_types.add(dep_type)

            if cls.__dependencies__ is None:
                cls.__dependencies__ = dependency_nodes

            if cls.__injections__ is None:
                cls.__injections__ = injected_types

            if cls.__initialize__ is None:
                # If not set, prepare the dependencies distribution
                kwargs_names_by_type = reverse_dict(all_args)

                cls.__initialize__ = (
                    fntypes.F[set["Value[typing.Any]"]]()
                    .then(
                        lambda values: (
                            {
                                kwargs_names_by_type[value.cls]: value.unbox() 
                                for value in values 
                                if value.cls in kwargs_names_by_type
                            }
                        ),
                    ).then(
                        lambda params: cls.__compose__(**params),
                    )
                )
            
            if cls.__type__ is None:
                cls.__type__ = cls

            setattr(cls, "__traverse__", build_queue(cls, []))

            # Initialize nodes that requested node as forward ref
            for request in FORWARD_REF_REQUESTS.pop(cls.__name__, []):
                INITIALIZED_FORWARD_REFS[cls.__name__] = cls
                request.__init_subclass__()
    
    def __repr__(self) -> str:
        return f"<node {type(self).__name__}>"


__all__ = ("Node", "Queue")
