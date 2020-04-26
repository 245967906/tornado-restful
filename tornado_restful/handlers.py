from __future__ import annotations

import json
import traceback
from asyncio import Future
from types import TracebackType
from typing import (
    Any,
    Awaitable,
    Optional,
    Tuple,
    Type,
    Union,
)

import tornado.web

from tornado_restful import status
from tornado_restful.conf import settings
from tornado_restful.exceptions import APIException, BadRequestError
from tornado_restful.i18n import I18n


class APIHandler(tornado.web.RequestHandler):
    def initialize(self, **kwargs: Any) -> None:
        if "method_map" in kwargs:
            method_map = kwargs["method_map"]
            for method, action in method_map.items():
                handler = getattr(self, action)
                setattr(self, method, handler)

    def prepare(self) -> Optional[Awaitable[None]]:
        self.request.data = self._parse_request_body()
        self.request.token = self._parse_request_token()

    def options(self, *args: str, **kwargs: str) -> Future[None]:
        self.set_status(status.HTTP_204_NO_CONTENT)
        return self.finish()

    def set_default_headers(self) -> None:
        self.set_header("Access-Control-Allow-Origin", "*")
        self.set_header("Access-Control-Allow-Headers", "*")
        self.set_header(
            "Access-Control-Allow-Methods",
            "GET, POST, PUT, PATCH, DELETE, HEAD, OPTIONS"
        )

    def write(self, chunk: Union[str, bytes, dict]) -> None:
        if isinstance(chunk, dict):
            chunk = json.dumps(chunk, ensure_ascii=False, indent=2)
            chunk = chunk.replace("</", "<\\/") + "\n"
            self.set_header("Content-Type", "application/json; charset=UTF-8")
        super().write(chunk)

    def write_error(self, status_code: int, **kwargs: Any) -> Future[None]:
        if "exc_info" in kwargs:
            typ, value, tb = kwargs["exc_info"]
            if issubclass(typ, APIException):
                data = {"message": value.message, "detail": value.detail}
                self.set_status(value.status_code)
                return self.finish(data)
            else:
                if self.settings.get("serve_traceback"):
                    self.set_header("Content-Type", "text/plain")
                    for line in traceback.format_exception(
                        *kwargs["exc_info"]
                    ):
                        self.write(line)
        return self.finish()

    @property
    async def current_user(self) -> Any:
        if not hasattr(self, "_current_user"):
            self._current_user = await self.get_current_user()
        return self._current_user

    async def get_current_user(self) -> Any:
        """Override to determine the current user from.

        This method should be a coroutine.
        """
        return None

    def get_user_locale(self, default: str = "en") -> str:
        if "Accept-Language" in self.request.headers:
            languages = self.request.headers["Accept-Language"].split(",")
            locales = []
            for language in languages:
                parts = language.strip().split(";")
                if len(parts) > 1 and parts[1].startswith("q="):
                    try:
                        score = float(parts[1][2:])
                    except (ValueError, TypeError):
                        score = 0.0
                else:
                    score = 1.0
                locales.append((parts[0], score))
            if locales:
                locales.sort(key=lambda pair: pair[1], reverse=True)
                codes = [l[0] for l in locales]
                return codes[0]
        return default

    def log_exception(
        self,
        typ: Optional[Type[BaseException]],
        value: Optional[BaseException],
        tb: Optional[TracebackType],
    ) -> None:
        if issubclass(typ, APIException):
            self.set_status(value.status_code)
            return
        super().log_exception(typ, value, tb)

    def paginate(self) -> Tuple[int, int]:
        limit = self.get_query_argument("limit", settings.page_size)
        offset = self.get_query_argument("offset", 0)
        try:
            limit, offset = int(limit), int(offset)
        except ValueError:
            raise BadRequestError
        return min(settings.page_size, limit), offset

    @property
    def i18n(self) -> I18n:
        if not hasattr(self, "_i18n"):
            self._i18n = I18n(self.locale)
        return self._i18n

    def _parse_request_body(self):
        content_type = self.request.headers.get("Content-Type")
        if not content_type == "application/json":
            return None
        try:
            request_body = self.request.body.decode("utf-8")
            request_data = json.loads(request_body)
        except json.JSONDecodeError:
            raise BadRequestError
        return request_data

    def _parse_request_token(self) -> Optional[str]:
        if "Authorization" in self.request.headers:
            auth_header = self.request.headers["Authorization"]
            if auth_header.startswith(settings.jwt_auth_header_prefix):
                try:
                    _, token = auth_header.split()
                    return token
                except (AttributeError, ValueError):
                    return None
        return None


class NotFoundHandler(tornado.web.RequestHandler):
    def prepare(self) -> Optional[Awaitable[None]]:
        self.set_status(status.HTTP_404_NOT_FOUND)
        if self.settings.get("debug"):
            routes = [
                x.regex.pattern for x in self.application.wildcard_router.rules
            ]
            self.write(json.dumps(sorted(routes), indent=2))
            self.write("\n")
        return self.finish()
