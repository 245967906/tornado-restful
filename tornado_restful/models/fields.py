from enum import IntEnum
from typing import Any

from passlib.hash import pbkdf2_sha256
from peewee import (
    OP,
    AutoField,
    BareField,
    BigAutoField,
    BigBitField,
    BigIntegerField,
    BinaryUUIDField,
    BitField,
    BlobField,
    BooleanField,
    CharField,
    DateField,
    DateTimeField,
    DecimalField,
    DoubleField,
    Expression,
    Field,
    FixedCharField,
    FloatField,
    ForeignKeyField,
    IdentityField,
    IntegerField,
    IPField,
    ManyToManyField,
    MetaField,
    PrimaryKeyField,
    SmallIntegerField,
    TextField,
    TimeField,
    TimestampField,
    UUIDField,
    VirtualField,
)

from tornado_restful.shortcuts import decrypt, encrypt

__all__ = [
    "AutoField",
    "BareField",
    "BigAutoField",
    "BigBitField",
    "BigIntegerField",
    "BinaryUUIDField",
    "BitField",
    "BlobField",
    "BooleanField",
    "CharField",
    "DateField",
    "DateTimeField",
    "DecimalField",
    "DoubleField",
    "Field",
    "FixedCharField",
    "FloatField",
    "ForeignKeyField",
    "IPField",
    "IdentityField",
    "IntegerField",
    "ManyToManyField",
    "MetaField",
    "PrimaryKeyField",
    "SmallIntegerField",
    "TextField",
    "TimeField",
    "TimestampField",
    "UUIDField",
    "VirtualField",
    "AESField",
    "BooleanField",
    "EnumField",
    "PasswordField",
]


class AESField(CharField):
    def db_value(self, value: str) -> str:
        return encrypt(value)

    def python_value(self, value: str) -> str:
        return decrypt(value)


class BooleanField(BooleanField):
    def is_true(self) -> bool:
        return Expression(self, OP.EQ, True)

    def is_false(self) -> bool:
        return Expression(self, OP.EQ, False)


class EnumField(IntegerField):
    def __init__(self, choices: IntEnum, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, **kwargs)
        self._choices = choices

    def db_value(self, value: int) -> int:
        if value not in [e.value for e in self._choices]:
            raise ValueError(
                "An invalid enumeration value has been specified."
            )
        return value


class PasswordField(CharField):
    def db_value(self, value: str) -> str:
        return pbkdf2_sha256.hash(value)
