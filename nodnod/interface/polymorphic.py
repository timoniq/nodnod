from nodnod.node import Node
from nodnod.interface.either import Either
from nodnod.utils.prepare_values import prepare_value
import fntypes
import typing
import types


CASE_MARK = "IS_CASE"

def case[Cls, R, **P](case_method: typing.Callable[typing.Concatenate[Cls, P], R]) -> typing.Callable[P, R]:
    setattr(case_method, CASE_MARK, True)
    return classmethod(case_method)  # type: ignore


def collect_cases(node_class: type) -> list[typing.Callable]:
    cases = []
    for item in node_class.__dict__.values():
        if getattr(getattr(item, "__func__", None), CASE_MARK, None):
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


class polymorphic[T]: # noqa: N801
    POLYMORPHIC_NODE_CLS = PolymorphicNode

    def __new__(cls, node_class: type) -> type[PolymorphicNode[T]]:
        cases = collect_cases(node_class)

        case_nodes = []

        for case in cases:
            node = type(
                node_class.__name__ + ":" + case.__name__, 
                tuple(types.resolve_bases([node_class, Node])),
                dict(__compose__=case),
            )
            case_nodes.append(node)
                
        return type(
            node_class.__name__,
            tuple(types.resolve_bases([cls.POLYMORPHIC_NODE_CLS])),
            dict(__either__=tuple(case_nodes))
        )
