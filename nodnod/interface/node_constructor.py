import typing

from nodnod.node import InjectionHook, Node


class _Constructor(Node, abstract=True):
    __construct__: typing.Callable[[], typing.Any]
    __type__ = typing.Self

    @classmethod
    def __compose__(cls) -> typing.Any:
        return cls.__construct__()  # type: ignore


class NodeConstructor(Node, abstract=True):
    __constructor__: type[_Constructor] | None = None

    @classmethod
    def __construct__(cls, *args: typing.Any) -> typing.Self:
        raise NotImplementedError("`__construct__` method must be implemented.")

    def __init_subclass__(
        cls,
        abstract: bool = False,
        injection_hooks: tuple[InjectionHook, ...] = (),
    ) -> None:
        super().__init_subclass__(injection_hooks=injection_hooks)

        if not abstract and cls.__constructor__ is None:
            cls.__constructor__ = constructor = type(
                f"Constructor:{cls.__name__}",
                (_Constructor,),
                dict(__construct__=cls.__construct__, __module__=__name__),
            )
            cls.__dependencies__.add(constructor)
            cls.__injections__ ^= {typing.Self, constructor}

    def __class_getitem__(cls, item: typing.Any | tuple[typing.Any, ...], /) -> typing.Any:
        items = (item,) if not isinstance(item, tuple) else item
        args_str = ", ".join(str(item) for item in items)
        constructor = type(
            f"Constructor:{cls.__name__}[{args_str}]",
            (_Constructor,),
            dict(__construct__=lambda: cls.__construct__(*items), __module__=__name__),
        )
        dependencies: set[typing.Any] = {constructor}
        injections: set[typing.Any] = {constructor}

        if cls.__constructor__ is not None:
            dependencies.add(cls.__constructor__)
            injections.add(cls.__constructor__)

        if typing.Self in cls.__injections__:
            injections.add(typing.Self)

        node = type(
            f"{cls.__name__}[{args_str}]",
            (cls,),
            dict(
                __module__=cls.__module__,
                __constructor__=constructor,
                __dependencies__=cls.__dependencies__ ^ dependencies,
                __injections__=cls.__injections__ ^ injections,
            ),
            abstract=True,
        )
        setattr(node, "__type__", node)
        return node


__all__ = ("NodeConstructor",)
