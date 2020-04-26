from inspect import isawaitable
from typing import Any, Union

from marshmallow import (
    EXCLUDE,
    INCLUDE,
    RAISE,
    SchemaOpts,
    ValidationError,
    fields,
    missing,
    post_dump,
    post_load,
    pprint,
    pre_dump,
    pre_load,
    validate,
    validates,
    validates_schema,
)
from marshmallow.schema import BaseSchema
from marshmallow.schema import SchemaMeta as _SchemaMeta

from tornado_restful.models import Model
from tornado_restful.exceptions import BadRequestError

__all__ = [
    "EXCLUDE",
    "INCLUDE",
    "RAISE",
    "SchemaOpts",
    "Serializer",
    "ValidationError",
    "fields",
    "missing",
    "post_dump",
    "post_load",
    "pprint",
    "pre_dump",
    "pre_load",
    "validate",
    "validates",
    "validates_schema",
]


class SchemaMeta(_SchemaMeta):
    inherited_options = [
        "fields", "additional", "include", "exclude", "dateformat",
        "datetimeformat", "render_module", "ordered", "index_errors",
        "load_only", "dump_only", "unknown", "register"
    ]

    def __new__(mcs, name, bases, attrs):
        meta = attrs.get("Meta", type("Meta", (), {}))
        for option in mcs.inherited_options:
            if not hasattr(meta, option):
                for base in bases:
                    if hasattr(base, "Meta") and hasattr(base.Meta, option):
                        setattr(meta, option, getattr(base.Meta, option))
                        break
        attrs["Meta"] = meta
        return super().__new__(mcs, name, bases, attrs)


class Serializer(BaseSchema, metaclass=SchemaMeta):
    class Meta:
        ordered = True
        unknown = EXCLUDE

    def __init__(
        self,
        instance: Model = None,
        data: Union[list, dict] = None,
        context: dict = None,
        **kwargs: Any,
    ) -> None:
        self.instance = instance
        if data is not None:
            self.initial_data = data
        super().__init__(context=context, **kwargs)

    def is_valid(self, raise_exception: bool = False) -> bool:
        assert hasattr(self, "initial_data"), (
            "Cannot call `.is_valid()` as no `data=` keyword argument was "
            "passed when instantiating the serializer instance."
        )
        try:
            self._validated_data = self.load(self.initial_data)
        except ValidationError as e:
            self._errors = e.messages
        else:
            self._errors = {}
        if self._errors and raise_exception:
            raise BadRequestError(detail=self._errors)
        return not bool(self._errors)

    async def save(self) -> Model:
        assert hasattr(
            self, "_errors"
        ), "You must call `.is_valid()` before accessing `.save()`."
        assert not self.errors, (
            "You cannot call `.save()` on a serializer with invalid data."
        )
        if self.instance is None:
            instance = self.create(self.validated_data)
            assert instance is not None, (
                "`create()` did not return an object instance."
            )
        else:
            instance = self.update(self.instance, self.validated_data)
            assert instance is not None, (
                "`update()` did not return an object instance."
            )
        self.instance = await instance if isawaitable(instance) else instance
        return self.instance

    def create(self, validated_data: Union[list, dict]) -> Model:
        raise NotImplementedError("`create` must be implemented.")

    def update(
        self, instance: Model, validated_data: Union[list, dict]
    ) -> Model:
        raise NotImplementedError("`update` must be implemented.")

    @property
    def data(self) -> Union[list, dict]:
        if (
            hasattr(self, "initial_data")
            and not hasattr(self, "_validated_data")
        ):
            raise AssertionError(
                "When a serializer is passed a `data` keyword argument you "
                "must call `.is_valid()` before attempting to access the "
                "serialized `.data` representation.\n"
                "You should either call `.is_valid()` first, "
                "or access `.initial_data` instead."
            )
        if not hasattr(self, "_data"):
            has_error = bool(getattr(self, "_errors", None))
            if self.instance is not None and not has_error:
                self._data = self.dump(self.instance)
            elif hasattr(self, "_validated_data") and not has_error:
                self._data = self._validated_data
            else:
                self._data = None
        return self._data

    @property
    def errors(self) -> dict:
        assert hasattr(
            self, "_errors"
        ), "You must call `.is_valid()` before accessing `.errors`."
        return self._errors

    @property
    def validated_data(self) -> Union[list, dict]:
        assert hasattr(
            self, "_validated_data"
        ), "You must call `.is_valid()` before accessing `.validated_data`."
        return self._validated_data
