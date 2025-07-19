from nodnod.box import Box


class Node[T]:
    def __init__(self, value: T):
        self.value = value
    
    @classmethod
    def __compose__(cls, *args, **kwargs) -> T:
        ...
    
    def __box__(self) -> Box[T]:
        return Box(self.value)
    
    @classmethod
    def __dependencies__(cls) -> set[type["Node"]]:
        return set()
    
    def __repr__(self) -> str:
        return f"<node {self.__class__.__name__} = {self.value}>"


type Queue = set[type[Node]]
