import itertools
import os
import re
from collections import namedtuple
from typing import (
    Any,
    Iterable,
    List,
    Union,
)

import tornado.web
from inflection import singularize

Route = namedtuple("Route", ("detail", "mapping"))
RouteRule = namedtuple("RouteRule", ("pattern", "handler", "kwargs", "name"))


class Router:
    def __init__(
        self, api_prefix: str = "/", trailing_slash: bool = False
    ) -> None:
        self.api_prefix = api_prefix
        self.trailing_slash = trailing_slash
        self.registry = []

    def register(
        self,
        pattern: str,
        handler: Any,
        kwargs: dict = None,
        name: str = None,
    ) -> None:
        self.registry.append((pattern, handler, kwargs, name))

    def get_rules(self) -> List[RouteRule]:
        raise NotImplementedError("`get_rules` must be overridden.")

    @property
    def rules(self) -> List[tornado.web.url]:
        self._rules = []
        for pattern, handler, kwargs, name in self.get_rules():
            trailing_slash = "/" if self.trailing_slash else ""
            pattern = os.path.join(
                self.api_prefix, pattern.strip("/")
            ) + trailing_slash
            self._rules.append(tornado.web.url(pattern, handler, kwargs, name))
        return self._rules


class GenericRouter(Router):
    def get_rules(self) -> List[RouteRule]:
        rules = []
        for pattern, handler, kwargs, name in self.registry:
            rules.append(RouteRule(pattern, handler, kwargs, name))
        return rules


class NestedRouter(Router):
    routes = [
        Route(
            detail=False,
            mapping={
                "get": "list",
                "post": "create"
            },
        ),
        Route(
            detail=True,
            mapping={
                "get": "retrieve",
                "put": "update",
                "patch": "partial_update",
                "delete": "destroy"
            },
        )
    ]

    def register(
        self,
        resources: Union[str, Iterable[str]],
        handler: Any,
        kwargs: dict = None,
        name: str = None,
    ) -> None:
        if isinstance(resources, str):
            resources = (resources, )
        for resource in resources:
            if not re.match(r"^[a-zA-Z0-9_-]+$", resource):
                raise AssertionError(f"Invalid resource name `{resource}`.")
        super().register(resources, handler, kwargs, name)

    def get_rules(self) -> List[RouteRule]:
        rules = []
        for resources, handler, kwargs, name in self.registry:
            kwargs = {} if not isinstance(kwargs, dict) else kwargs
            regexs = self.get_lookup_regexs(resources, handler)
            zipped = zip(resources, regexs)
            flat = tuple(itertools.chain.from_iterable(zipped))
            standalone = getattr(handler, "standalone", False)
            for route in self.routes:
                method_map = self.get_method_map(handler, route.mapping)
                if not method_map:
                    continue
                if standalone and not route.detail:
                    continue
                pattern = "/".join(
                    flat if route.detail and not standalone else flat[:-1]
                )
                kwargs.update(method_map=method_map)
                rules.append(RouteRule(pattern, handler, kwargs.copy(), name))
        return rules

    def get_lookup_regexs(
        self,
        resources: Iterable[str],
        handler: Any,
    ) -> List[str]:
        base_regex = "(?P<{lookup_url_kwarg}>{lookup_value_regex})"
        lookup_url_kwarg = getattr(handler, "lookup_url_kwarg", "pk")
        lookup_value_regex = getattr(handler, "lookup_value_regex", "[^/.]+")
        lookup_url_kwargs = getattr(handler, "lookup_url_kwargs", None)
        lookup_value_regexs = getattr(handler, "lookup_value_regexs", None)
        if not lookup_url_kwargs:
            if len(resources) == 1:
                lookup_url_kwargs = (lookup_url_kwarg, )
            else:
                lookup_url_kwargs = (
                    singularize(x) + "_" + lookup_url_kwarg for x in resources
                )
                lookup_url_kwargs = tuple(lookup_url_kwargs)
        if not lookup_value_regexs:
            lookup_value_regexs = (lookup_value_regex, ) * len(resources)
        if not len(lookup_url_kwargs) == len(lookup_value_regexs):
            raise AssertionError(
                "Attribute `lookup_url_kwargs` and `lookup_value_regexs` "
                "have different lengths."
            )
        lookup_regexs = []
        for kwarg, regex in zip(lookup_url_kwargs, lookup_value_regexs):
            lookup_regex = base_regex.format(
                lookup_url_kwarg=kwarg,
                lookup_value_regex=regex,
            )
            lookup_regexs.append(lookup_regex)
        return lookup_regexs

    def get_method_map(self, handler: Any, mapping: dict) -> dict:
        method_map = {}
        for method, action in mapping.items():
            if hasattr(handler, action):
                method_map[method] = action
        return method_map
