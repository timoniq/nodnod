import asyncio
import dataclasses
import datetime
import typing

import kungfu

from nodnod import (
    EventLoopAgent,
    Externals,
    NodeError,
    Scope,
    create_agent_from_node,
    create_node_from_function,
    inject_externals,
    scalar_node,
)
from nodnod.interface.compose_one import compose_one


@dataclasses.dataclass
class User:
    id: int
    email: kungfu.Option[str]
    last_active: datetime.datetime


@scalar_node
class UserId:
    @classmethod
    def __compose__(cls, user: User) -> int:
        return user.id


@scalar_node
class Email(str):
    def validate_email(self):
        if "@" not in self:
            raise NodeError("Email is in wrong format")

    @classmethod
    def __compose__(cls, user: User) -> str:
        email = cls(user.email.expect(NodeError("User has no email")))
        email.validate_email()
        return email


@dataclasses.dataclass
class UserSource:
    user: User

    @classmethod
    def __compose__(cls, user: User) -> typing.Self:
        return cls(user)


@scalar_node
class EmailProvider:
    @classmethod
    def __compose__(cls, email: Email) -> str:
        _, provider = email.split("@", 1)
        if not provider:
            raise NodeError("Email has no provider")
        return provider


@scalar_node
class SinceActive:
    @classmethod
    def __compose__(cls, user: User) -> datetime.timedelta:
        return datetime.datetime.now() - user.last_active


async def handler(email_provider: EmailProvider, boba: str, lol: str, since_active: SinceActive, user: UserSource):
    print(email_provider, boba, lol, since_active, user.user)
    return "handler result"


async def main():
    # Compile time
    handler_node = create_node_from_function(handler)
    agent = create_agent_from_node(handler_node, EventLoopAgent)

    user = User(1, kungfu.Some("lol@skibidi.org"), datetime.datetime.now())

    # Run time
    async with Scope() as scope:
        scope.inject(User, user)
        inject_externals(scope, {"boba": "ahah", "lol": "omg"})
        await agent.run(scope, {})

    print(
        await compose_one(
            SinceActive,
            {User: User(2, kungfu.Nothing(), datetime.datetime.now())},
        )
    )

    print(
        await compose_one(
            create_node_from_function(handler),
            {User: user, Externals: {"boba": "tea", "lol": "0"}},
        )
    )


asyncio.run(main())
