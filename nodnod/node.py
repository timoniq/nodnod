import collections
import typing

import kungfu
from typing_extensions import ForwardRef

from nodnod.error import NodeBuildError
from nodnod.utils.call import call_with_context
from nodnod.utils.is_type import is_type
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature

if typing.TYPE_CHECKING:
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]
type Queue = list[type[Node]]

type Injection[T] = typing.Annotated[T, ...]
type InjectionHook = typing.Callable[["type[Node]", str, typing.Any], kungfu.Pulse[str]]

FORWARD_REF_REQUESTS = collections.defaultdict[str, list["type[Node]"]](list)
INITIALIZED_FORWARD_REFS: dict[str, typing.Any] = {}

ExternalDependency = typing.NewType("ExternalDependency", str)


@classmethod
def dummy_compose(cls: type[typing.Any]) -> typing.NoReturn:
    raise RuntimeError(f"`{cls.__name__}` does not provide `__compose__`. Maybe it should be abstract=True?")


class Node[T = typing.Any, Root = typing.Any]:
    __type__: typing.Any = None  # type: ignore
    __dependencies__: set[type["Node"]] = None  # type: ignore
    __injections__: set[typing.Any] = None  # type: ignore

    __initialize__: typing.Callable[[set["Value"]], ComposeResponse[T]] = None  # type: ignore
    __compose__: typing.Callable[..., ComposeResponse[T]] = dummy_compose

    def __init_subclass__(  # noqa: PLR0915
        cls,
        abstract: bool = False,
        injection_hooks: tuple[InjectionHook, ...] = (),
    ) -> None:
        from nodnod.builder.build_queue import build_queue
        from nodnod.interface.composable import Composable
        from nodnod.interface.create_result_node import create_result_node
        from nodnod.interface.generic import create_type_arg_node
        from nodnod.interface.option_node import create_option_node
        from nodnod.interface.union_node import create_union_node, is_union
        from nodnod.utils.create_node import create_node_from_composable

        if not abstract and not cls.__initialize__:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(
                cls.__compose__,
                bound_class=getattr(cls.__compose__, "__self__", cls),
                ignore_bound_parameters=True,
            )
            all_args = signature.merge()
            has_forward_refs_requests = False

            # Search for forward refs and form requests to initialize node when forward ref node is initialized
            # or fill forward refs if node is being initialized

            for name, dep_type in all_args.items():
                if isinstance(dep_type, typing.ForwardRef):
                    if (ann := INITIALIZED_FORWARD_REFS.get(dep_type.__forward_arg__)):
                        all_args[name] = ann
                        continue

                    FORWARD_REF_REQUESTS[dep_type.__forward_arg__].append(cls)
                    has_forward_refs_requests = True

            # If there are forward refs requests, return early to request forward refs to be initialized
            if has_forward_refs_requests:
                return

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type[typing.Any]]()

            for dep_name, dep_type in all_args.copy().items():
                if isinstance(dep_type, typing.TypeAliasType):
                    dep_type = all_args[dep_name] = dep_type.__value__

                if is_type(dep_type, Node):
                    dependency_nodes.add(dep_type)
                elif is_type(dep_type, Composable):
                    all_args[dep_name] = typing.get_origin(dep_type) or dep_type
                    dependency_nodes.add(create_node_from_composable(typing.cast("type[Composable]", all_args[dep_name])))
                elif is_union(dep_type):
                    dependency_nodes.add(create_union_node(dep_type))
                elif is_type(dep_type, kungfu.Option):
                    dependency_nodes.add(create_option_node(dep_type))
                elif is_type(dep_type, kungfu.Result):
                    dependency_nodes.add(create_result_node(dep_type))
                elif is_type(dep_type, type) or is_type(dep_type, tuple):
                    args = typing.get_args(dep_type)
                    if not args:
                        raise NodeBuildError(f"Expected `type` or `tuple` with type argument, got `{dep_type!r}`.")

                    if is_type(dep_type, type):
                        if is_type(type(args[0]), typing.TypeVar):
                            type_arg_node = create_type_arg_node(cls, args[0], dep_type)
                        else:
                            raise NotImplementedError("Only `type` with type var is supported.")

                    elif is_type(dep_type, tuple):
                        if (
                            is_type(type(args[0]), typing._UnpackGenericAlias)  # type: ignore
                            and (unpack_args := typing.get_args(args[0]))
                            and is_type(type(unpack_args[0]), typing.TypeVarTuple)
                        ):
                            type_arg_node = create_type_arg_node(cls, unpack_args[0], dep_type)
                        else:
                            raise NotImplementedError("Only `typing.Unpack` with type var tuple is supported.")

                    dependency_nodes.add(type_arg_node)
                else:
                    is_processed_by_hook = False
                    for hook in injection_hooks:
                        if hook(cls, dep_name, dep_type):
                            is_processed_by_hook = True
                            break

                    if not is_processed_by_hook:
                        if is_type(dep_type, Injection):
                            dep_type = typing.get_args(dep_type)[0]

                        # Unresolved ForwardRef
                        if isinstance(dep_type, str | ForwardRef):
                            # NOTE: Might it be worth implementing a way that resolves these ForwardRef's?
                            # Resolve in runtime via helper function like `get_subnodes`.
                            raise LookupError(
                                f"Unresolved dependency for `{dep_name}` of `{cls.__name__}`, "
                                "it looks like a `ForwardRef` that could not be resolved.",
                            )

                        injected_types.add(dep_type)

            if cls.__dependencies__ is None:
                cls.__dependencies__ = dependency_nodes

            if cls.__injections__ is None:
                cls.__injections__ = injected_types

            if cls.__initialize__ is None:
                # If not set, prepare the dependencies distribution
                kwargs_names_by_type = reverse_dict(all_args)

                cls.__initialize__ = (
                    kungfu.F[set["Value"]]()
                    .then(
                        lambda values: (
                            {
                                kwargs_names_by_type[value.cls]: value.unbox()
                                for value in values
                                if value.cls in kwargs_names_by_type
                            }
                        ),
                    ).then(
                        lambda context: call_with_context(cls.__compose__, context),
                    )
                )

            if cls.__type__ is None:
                cls.__type__ = cls

            setattr(cls, "__traverse__", build_queue(cls, []))

            INITIALIZED_FORWARD_REFS[cls.__name__] = cls

            # Initialize nodes that requested node as forward ref
            for request in FORWARD_REF_REQUESTS.pop(cls.__name__, []):
                request.__init_subclass__()

    def __repr__(self) -> str:
        return f"<node `{type(self).__name__}`>"


def initialize_forward_refs(
    forward_refs: dict[str, typing.Any],
    *,
    is_from_function: bool = False,
) -> None:
    while FORWARD_REF_REQUESTS:
        type_name, forward_ref_request = FORWARD_REF_REQUESTS.popitem()

        if type_name in forward_refs:
            INITIALIZED_FORWARD_REFS[type_name] = forward_refs[type_name]

            for dependency in forward_ref_request:
                dependency.__init_subclass__()
        elif is_from_function:
            # Mark it as ExternalDependency because this is a ForwardRef to a type that could not be found among
            # nodes or in the modules from globals. Probably it is defined inside a TYPE_CHECKING block.
            INITIALIZED_FORWARD_REFS[type_name] = ExternalDependency(type_name)
        else:
            # Otherwise, the node cannot have external dependencies, so it should raise an error
            raise LookupError(f"Dependency `{type_name}` not found")


__all__ = ("Injection", "Node", "Queue")
