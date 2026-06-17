import collections
import inspect
import typing
import warnings

import kungfu
from typing_extensions import ForwardRef

from nodnod.error import NodeBuildError
from nodnod.utils.call import call_with_context
from nodnod.utils.injection import get_injection_type
from nodnod.utils.is_type import is_type
from nodnod.utils.misc import reverse_dict
from nodnod.utils.resolve_signature import resolve_signature

if typing.TYPE_CHECKING:
    from nodnod.interface.composable import Composable
    from nodnod.value import Value

type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | "Node[T]" | typing.Awaitable[T] | Generator[T]
type Queue = list[type[Node]]

type Injection[T] = typing.Annotated[T, "injection"]
type InjectionHook = typing.Callable[["type[Node]", str, typing.Any], kungfu.Pulse[str]]

FORWARD_REF_REQUESTS = collections.defaultdict[str, list["type[Node]"]](list)
INITIALIZED_FORWARD_REFS: dict[str, typing.Any] = {}


@classmethod
def dummy_compose(cls: type[typing.Any]) -> typing.NoReturn:
    raise RuntimeError(f"`{cls.__name__}` does not provide `__compose__`. Maybe it should be abstract=True?")


def initialize_forward_refs(
    forward_refs: dict[str, typing.Any],
    *,
    is_from_function: bool = False,
    own_node: "type[Node] | None" = None,
) -> None:
    from nodnod.interface.node_from_function import ExternalDependency

    # Iterate a snapshot and consume requests selectively: building a function node must not
    # drain (and mis-mark as external) forward-ref requests that belong to unrelated, still
    # pending class nodes. `own_node`, when provided, is the function node being built; only its
    # own requests may be marked external — foreign co-requesters are preserved.
    for type_name in list(FORWARD_REF_REQUESTS):
        requesters = FORWARD_REF_REQUESTS.get(type_name)
        if requesters is None:
            continue

        if type_name in forward_refs:
            FORWARD_REF_REQUESTS.pop(type_name)
            INITIALIZED_FORWARD_REFS[type_name] = forward_refs[type_name]

            for dependency in requesters:
                dependency.__init_subclass__()
            continue

        if not is_from_function:
            # A class node cannot have external dependencies, so an unresolved ref is an error.
            raise LookupError(f"Dependency `{type_name}` not found")

        if own_node is not None and own_node not in requesters:
            # A foreign pending class request during a function build: leave it untouched so it
            # can still resolve when its real type is later defined.
            continue

        # The ref belongs to the function being built (likely a TYPE_CHECKING-only type taken as
        # an external). Mark it external; the owning function node is re-initialized (with its
        # injection hooks) by create_node_from_function. Remove only this function's own request,
        # preserving any foreign class co-requesters waiting on the same name.
        INITIALIZED_FORWARD_REFS.setdefault(type_name, ExternalDependency(type_name))
        if own_node is not None:
            requesters.remove(own_node)
            if not requesters:
                FORWARD_REF_REQUESTS.pop(type_name, None)
        else:
            FORWARD_REF_REQUESTS.pop(type_name, None)


def is_injection(obj: typing.Any, /) -> bool:
    return (
        is_type(obj, Injection)
        or (isinstance(obj, typing._AnnotatedAlias) and obj.__metadata__ == ("injection",))  # type: ignore
    )


class Scalar:
    annotation: typing.Any
    composable: "Composable"

    def __init__(self, annotation: typing.Any, composable: typing.Any) -> None:
        from nodnod.interface.composable import Composable

        if not is_type(composable, Composable):
            raise TypeError(f"Second argument of `Scalar` must be a `Composable`, got `{composable!r}`.")

        self.annotation = annotation
        self.composable = composable

    def __class_getitem__(cls, items: tuple[typing.Any, ...], /) -> typing.Self:
        if not isinstance(items, tuple) or len(items) != 2:
            raise TypeError(f"Expected 2 items (annotation and composable like), got `{items!r}`.")
        return cls(*items)


class Node[T = typing.Any, Root = typing.Any]:
    __type__: typing.Any = None  # type: ignore
    __dependencies__: set[type["Node"]] = None  # type: ignore
    __injections__: set[typing.Any] = None  # type: ignore
    __map__: typing.Mapping[typing.Any, type["Node"]] = None  # type: ignore

    __initialize__: typing.Callable[[set["Value"]], ComposeResponse[T]] = None  # type: ignore
    __compose__: typing.Callable[..., ComposeResponse[T]] = dummy_compose
    __compose_names_by_type__: dict[typing.Any, str] = None  # type: ignore

    def __init_subclass__(  # noqa: PLR0915
        cls,
        abstract: bool = False,
        injection_hooks: tuple[InjectionHook, ...] = (),
    ) -> None:
        from nodnod.builder.build_queue import build_queue
        from nodnod.error import NodeError
        from nodnod.interface.composable import Composable
        from nodnod.interface.create_result_node import create_result_node, is_result
        from nodnod.interface.generic import create_type_arg_node
        from nodnod.interface.option_node import create_option_node, is_option
        from nodnod.interface.union_node import create_union_node, is_union
        from nodnod.utils.create_node import create_node_from_composable

        if not abstract and not cls.__initialize__:
            # Resolve dependecies via __compose__ signature
            bound_class = cls.__compose__.__self__ if hasattr(cls.__compose__, "__self__") else cls
            signature = resolve_signature(
                cls.__compose__,
                bound_class=type(bound_class) if not isinstance(bound_class, type) else bound_class,
                ignore_bound_parameters=True,
            )
            all_args = signature.merge()

            # Annotated `*args` / `**kwargs` cannot be wired as dependencies. They were
            # silently dropped before, so fail loudly instead of building a broken node.
            for var_param in (signature.var_positional, signature.var_keyword):
                if var_param is not None and var_param.annotation not in (typing.Any, inspect.Parameter.empty):
                    raise NodeBuildError(
                        f"`{cls.__name__}.__compose__` annotates `{var_param.name}` "
                        f"(`*args`/`**kwargs`), which cannot be wired as a dependency. "
                        "Declare each dependency as an explicit parameter.",
                    )

            has_forward_refs_requests = False

            # Search for forward refs and form requests to initialize node when forward ref node is initialized
            # or fill forward refs if node is being initialized

            for name, dep_type in all_args.items():
                if isinstance(dep_type, typing.ForwardRef):
                    forward_arg = dep_type.__forward_arg__

                    if (initialized_ref := INITIALIZED_FORWARD_REFS.get(forward_arg)):
                        all_args[name] = initialized_ref
                        continue

                    if forward_arg == cls.__name__:
                        # Self-referential forward ref: resolve it to this class so it surfaces
                        # as a clear circular-dependency error during graph validation, instead
                        # of parking a request that nothing can ever resolve (leaving the node
                        # permanently uninitialized).
                        all_args[name] = cls
                        continue

                    FORWARD_REF_REQUESTS[forward_arg].append(cls)
                    has_forward_refs_requests = True

            # If there are forward refs requests, return early to request forward refs to be initialized
            if has_forward_refs_requests:
                return

            # Dependencies are all types from __compose__ signature
            dependency_nodes = set[type[Node]]()
            injected_types = set[type[typing.Any]]()

            cls.__map__ = {  # type: ignore
                dep_type: node if is_type(node, Node) else create_node_from_composable(node)
                for dep_type, node in cls.__map__.items()
                if is_type(node, Composable)
            } if cls.__map__ is not None else {}

            for dep_name, dep_type in all_args.copy().items():
                all_args[dep_name] = dep_type = cls.__map__.get(dep_type, dep_type)

                if isinstance(dep_type, typing.TypeAliasType):
                    dep_type = all_args[dep_name] = dep_type.__value__

                if isinstance(dep_type, Scalar):
                    dep_type = all_args[dep_name] = dep_type.composable

                if is_type(dep_type, Node):
                    dependency_nodes.add(dep_type)
                elif is_type(dep_type, Composable):
                    all_args[dep_name] = dep_type = typing.get_origin(dep_type) or dep_type
                    dependency_nodes.add(create_node_from_composable(dep_type))  # type: ignore
                elif is_union(dep_type):
                    dependency_nodes.add(create_union_node(dep_type))  # type: ignore
                elif is_option(dep_type):
                    dependency_nodes.add(create_option_node(dep_type))  # type: ignore
                elif is_result(dep_type):
                    dependency_nodes.add(create_result_node(dep_type))  # type: ignore
                elif is_type(dep_type, type) or is_type(dep_type, tuple):
                    args = typing.get_args(dep_type)
                    if not args:
                        raise NodeBuildError(f"Expected `type` or `tuple` with type argument, got `{dep_type!r}`.")

                    if is_type(dep_type, type):
                        if is_type(type(args[0]), typing.TypeVar):
                            type_arg_node = create_type_arg_node(cls, args[0], dep_type)  # type: ignore
                        else:
                            raise NotImplementedError("Only `type` with type var is supported.")

                    elif is_type(dep_type, tuple):
                        if (
                            is_type(type(args[0]), typing._UnpackGenericAlias)  # type: ignore
                            and (unpack_args := typing.get_args(args[0]))
                            and is_type(type(unpack_args[0]), typing.TypeVarTuple)
                        ):
                            type_arg_node = create_type_arg_node(cls, unpack_args[0], dep_type)  # type: ignore
                        else:
                            raise NotImplementedError("Only `typing.Unpack` with type var tuple is supported.")

                    dependency_nodes.add(type_arg_node)  # type: ignore
                else:
                    is_processed_by_hook = False
                    for hook in injection_hooks:
                        if hook(cls, dep_name, dep_type):
                            is_processed_by_hook = True
                            break

                    if not is_processed_by_hook:
                        if is_injection(dep_type):
                            dep_type = get_injection_type(dep_type, owner=cls.__compose__)
                            # Write the unwrapped type back so `__compose_names_by_type__`
                            # (built from `all_args`) is keyed by the same type as the boxed
                            # Value at compose time, instead of by the `Injection[T]` wrapper.
                            all_args[dep_name] = dep_type

                        # Unresolved ForwardRef
                        if isinstance(dep_type, str | ForwardRef):
                            # NOTE: Might it be worth implementing a way that resolves these ForwardRef's?
                            # Resolve in runtime via helper function like `get_subnodes`.
                            raise LookupError(
                                f"Unresolved dependency for `{dep_name}` of `{cls.__name__}`, "
                                "it looks like a `ForwardRef` that could not be resolved.",
                            )

                        injected_types.add(dep_type)  # type: ignore

            if cls.__compose_names_by_type__ is None:
                # Two parameters resolving to the same dependency/injection type silently
                # collapse in reverse_dict (one parameter name is lost), failing confusingly at
                # compose time. Detect it at definition time. External (by-name) parameters of a
                # function node are addressed by name, not type, so they are exempt.
                externals = getattr(cls, "__externals__", frozenset())
                seen_types: dict[typing.Any, str] = {}
                for arg_name, arg_type in all_args.items():
                    if arg_name in externals:
                        continue
                    if arg_type in seen_types:
                        raise NodeBuildError(
                            f"`{cls.__name__}.__compose__` has parameters `{seen_types[arg_type]}` "
                            f"and `{arg_name}` that resolve to the same dependency type "
                            f"`{getattr(arg_type, '__name__', arg_type)!r}`; a node cannot depend "
                            "on the same type under two parameter names.",
                        )
                    seen_types[arg_type] = arg_name

                cls.__compose_names_by_type__ = reverse_dict(all_args)

            if cls.__dependencies__ is None:
                cls.__dependencies__ = dependency_nodes

            if cls.__injections__ is None:
                cls.__injections__ = injected_types

            if cls.__initialize__ is None:
                # If not set, prepare the dependencies distribution
                cls.__initialize__ = (
                    kungfu.F[set["Value"]]()
                    .then(
                        lambda values: (
                            {
                                cls.__compose_names_by_type__[value.cls]: value.unbox()
                                for value in values
                                if value.cls in cls.__compose_names_by_type__
                            }
                        ),
                    ).then(
                        lambda context:
                            call_with_context(cls.__compose__, context)
                            .map_err(lambda name: NodeError(f"Name `{name}` was not found."))
                            .unwrap(),
                    )
                )

            if cls.__type__ is None:
                cls.__type__ = cls

            setattr(cls, "__traverse__", build_queue(cls, []))  # type: ignore

            # If a *different* class is already registered under this name and something is
            # actively waiting on a bare-string forward ref to it, the registry (keyed only by
            # __name__) would silently wire the wrong node — warn about the ambiguity.
            existing = INITIALIZED_FORWARD_REFS.get(cls.__name__)
            if existing is not None and existing is not cls and cls.__name__ in FORWARD_REF_REQUESTS:
                warnings.warn(
                    f"Two different Node classes are registered under the name `{cls.__name__}`; "
                    f"a string forward reference to `{cls.__name__}` is ambiguous and may resolve "
                    "to the wrong node. Import the type directly or rename to disambiguate.",
                    RuntimeWarning,
                    stacklevel=3,
                )

            INITIALIZED_FORWARD_REFS[cls.__name__] = cls

            # Initialize nodes that requested node as forward ref
            for request in FORWARD_REF_REQUESTS.pop(cls.__name__, []):
                request.__init_subclass__()

    def __repr__(self) -> str:
        return f"<node `{type(self).__name__}`>"


__all__ = ("Scalar", "Injection", "Node", "Queue", "dummy_compose", "is_injection", "initialize_forward_refs")
