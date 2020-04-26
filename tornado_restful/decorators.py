import functools
from typing import (
    Any,
    Awaitable,
    Callable,
    Optional,
)

from tornado_restful.exceptions import UnauthorizedError
from tornado_restful.handlers import APIHandler


# yapf: disable
def authenticated(
    method: Callable[..., Optional[Awaitable[None]]]
) -> Callable[..., Optional[Awaitable[None]]]:
    @functools.wraps(method)
    async def wrapper(
        self: APIHandler, *args: Any, **kwargs: Any
    ) -> Optional[Awaitable[None]]:
        current_user = await self.current_user
        if not current_user:
            raise UnauthorizedError
        return await method(self, *args, **kwargs)

    return wrapper
