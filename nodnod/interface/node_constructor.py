import typing

from nodnod.node import ComposeResponse, InjectionHook, Node
from nodnod.utils.call import call_with_context
from nodnod.value import Value


def initialize_node_constructor(
    compose: typing.Callable[[dict[str, typing.Any]], ComposeResponse],
    names_by_type: dict[typing.Any, str],
    values: set[Value],
) -> ComposeResponse:
    return compose({names_by_type[value.cls]: value.value for value in values if value.cls in names_by_type})


class NodeConstructor(Node, abstract=True):
    def __init_subclass__(
        cls,
        abstract: bool = False,
        injection_hooks: tuple[InjectionHook, ...] = (),
    ) -> None:
        super().__init_subclass__(injection_hooks=injection_hooks)

        if not abstract:
            cls.__initialize__ = lambda values: initialize_node_constructor(
                lambda context: call_with_context(cls().__compose__, context),
                cls.__compose_names_by_type__,
                values,
            )

    def __class_getitem__(cls, item: typing.Any | tuple[typing.Any, ...], /) -> typing.Any:
        items = (item,) if not isinstance(item, tuple) else item
        node = type(
            f"{cls.__name__}[{", ".join(str(item) for item in items)}]",
            (cls,),
            dict(
                __module__=cls.__module__,
                __initialize__=lambda values: initialize_node_constructor(
                    lambda context: call_with_context(cls(*items).__compose__, context),
                    cls.__compose_names_by_type__,
                    values,
                ),
            ),
            abstract=True,
        )
        setattr(node, "__type__", node)
        return node


__all__ = ("NodeConstructor",)
