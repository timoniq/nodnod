import typing


def reverse_dict[Key: typing.Hashable, Value: typing.Hashable](dct: dict[Key, Value]) -> dict[Value, Key]:
    return {v: k for k, v in dct.items()}


__all__ = ("reverse_dict",)
