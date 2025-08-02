import typing

import fntypes

from nodnod.interface.either import Either
from nodnod.node import ComposeResponse, Node
from nodnod.utils.create_node import create_node

CASE_MARK: typing.Final = "IS_CASE"


def case[Cls, R, **P](case_method: typing.Callable[typing.Concatenate[Cls, P], R], /) -> typing.Callable[P, R]:
    if isinstance(case_method, classmethod):
        func = case_method.__func__
    else:
        func = case_method
        case_method = classmethod(case_method)  # type: ignore

    setattr(func, CASE_MARK, True)
    return case_method  # type: ignore


def collect_cases(node_class: type[typing.Any]) -> list[typing.Callable[..., ComposeResponse[typing.Any]]]:
    cases = []
    for item in node_class.__dict__.values():
        if isinstance(item, classmethod) and getattr(item.__func__, CASE_MARK, None) is True:
            cases.append(item)
    return cases


class PolymorphicNode[T](Either, abstract=True):
    __either__: tuple[type[T], ...]
    concurrent = False

    @classmethod
    def __compose__(cls, node: fntypes.Variative) -> T:
        result = node.v
        if cls.is_scalar:
            return result.value
        return result


class polymorphic[T]:  # noqa: N801
    POLYMORPHIC_NODE_CLS = PolymorphicNode

    def __new__(cls, node_class: type[typing.Any]) -> type[PolymorphicNode[T]]:
        case_nodes: list[type[Node[typing.Any]]] = []

        for case in collect_cases(node_class):
            node = create_node(
                name=node_class.__name__ + ":" + case.__name__,
                base_node=Node,
                bases=(node_class,),
                namespace=dict(__compose__=case, __module__=node_class.__module__),
            )
            case_nodes.append(node)

        return create_node(
            name=node_class.__name__,
            base_node=cls.POLYMORPHIC_NODE_CLS,
            bases=tuple(),
            namespace=dict(__either__=tuple(case_nodes)),
        )


__all__ = ("PolymorphicNode", "polymorphic", "case", "collect_cases")
