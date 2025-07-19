class Box[T]:
    def __init__(self, value: T):
        self.value = value
    
    def unbox(self) -> T:
        return self.value
