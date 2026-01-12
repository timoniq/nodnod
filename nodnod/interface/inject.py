from __future__ import annotations

import typing

from nodnod.interface.node_from_function import Externals

if typing.TYPE_CHECKING:
    from nodnod.scope import Scope

    type ExternalName = str
    type ExternalValue = typing.Any
    type InternalType = typing.Any
    type InternalValue = typing.Any


def inject_externals(
    scope: Scope,
    externals: typing.Mapping[ExternalName, ExternalValue],
) -> None:
    inject_internals(scope, {Externals: Externals(externals)})


def inject_internals(
    scope: Scope,
    internals: typing.Mapping[InternalType, InternalValue],
) -> None:
    for internal_type, internal_value in internals.items():
        scope.inject(internal_type, internal_value)


__all__ = ("inject_externals", "inject_internals")
