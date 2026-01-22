from nodnod.utils.is_type import is_type


def test_is_type_with_tuple():
    result = is_type(list, (str, list, int))
    assert result is True

    result = is_type(dict, (str, list, int))
    assert result is False

    result = is_type(str, ())
    assert result is False


def test_is_type_different_type_args():
    result = is_type(list[int], list[str])
    assert result is False

    result = is_type(list[int], list[int])
    assert result is True

    result = is_type(dict[str, list[int]], dict[str, list[int]])
    assert result is True

    result = is_type(dict[str, list[int]], dict[str, list[str]])
    assert result is False


def test_is_type_with_inheritance():
    class Parent:
        pass

    class Child(Parent):
        pass

    result = is_type(Child, Parent)
    assert result is True

    result = is_type(Parent, Child)
    assert result is False


def test_is_type_basic_cases():
    assert is_type(int, int) is True
    assert is_type(str, str) is True

    assert is_type(int, str) is False

    assert is_type(list[int], list) is True
    assert is_type(list, list[int]) is False
