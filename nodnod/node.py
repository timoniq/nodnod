from nodnod.box import Box
from nodnod.utils.generator import generator_asend, generator_send
from nodnod.utils.aio import awaitable_noop
from nodnod.utils.resolve_signature import resolve_signature
from nodnod.utils.misc import reverse_dict
import fntypes
import typing
import types


type Generator[T] = typing.Generator[T, None, None] | typing.AsyncGenerator[T, None]
type ComposeResponse[T] = T | typing.Awaitable[T] | Generator[T]


class Node[T]:
    __dependencies__: set[type["Node"]] = None # type: ignore
    __bound_compose__: typing.Callable[[set["Node"]], ComposeResponse[T]] = None # type: ignore
    __traverse__: list[type["Node"]] = None # type: ignore

    def __init__(self, value: T, generator: Generator[T] | None = None):
        self.value = value
        self.generator = generator

    def __init_subclass__(cls, abstract: bool = False) -> None:
        from nodnod.builder.build_queue import build_queue
        
        if not abstract:
            # Resolve dependecies via __compose__ signature
            signature = resolve_signature(cls.__compose__, ignore_bound_parameters=True)

            if cls.__dependencies__ is None:
                # Dependencies are all types from __compose__ signature
                cls.__dependencies__ = signature.get_all_types()

            if cls.__bound_compose__ is None:
                # If not set, prepare the dependencies distribution
                kwargs_names_by_type = reverse_dict(signature.kwargs)

                cls.__bound_compose__ = (
                    fntypes.F[set["Node"]]()
                    .then(
                        lambda nodes: (
                            [node for node in nodes if type(node) in signature.args.values()],
                            {kwargs_names_by_type[type(node)]: node for node in nodes if type(node) in kwargs_names_by_type}
                        )
                    ).then(
                        lambda params: cls.__compose__(*params[0], **params[1])
                    )
                )
            
            cls.__traverse__ = build_queue(cls, [])
    
    @classmethod
    def __compose__(cls, *args, **kwargs) -> ComposeResponse[T]:
        ...
    
    def __box__(self) -> Box[T]:
        return Box(self.value)
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__} = {self.value}>"

    def close(self) -> typing.Awaitable[typing.Any]:
        if self.generator is None:
            return awaitable_noop()
        
        if isinstance(self.generator, types.AsyncGeneratorType):
            result = generator_asend(self.generator)
            self.generator = None
            return result
        
        elif isinstance(self.generator, types.GeneratorType):
            generator_send(self.generator)
        
        self.generator = None
        return awaitable_noop()


type Queue = list[type[Node]]
