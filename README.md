Tornado REST framework
-------

[![pypi-version]][pypi]


## Table of Contents
- [Intro](#intro)
- [Installation](#installation)
- [Quick Start](#quick-start)
- [User Guide](#user-guide)
- [License](#license)


## Intro

Tornado REST framework is a powerful and flexible toolkit for building Web APIs.

Some reasons you might want to use Tornado REST framework:
* Identity authentication based on JWT.
* An easy way of determining the URL rules automatically.
* Asynchronous interface for [peewee ORM][peewee] based on [peewee-async].
* Serialization support based on [marshmallow].
* I18n support based on JSON translation files. 


## Installation

Install tornado-restful with pip:
``` sh
$ pip install tornado-restful
```


## Quick Start
Let's take a look at a quick example of using Tornado REST framework to build a simple model-backed API for accessing users.

Setting up a new project:

```
.
├── handlers
│   └── user.py
├── models
│   └── user.py
├── routers
│   └── user.py
├── serializers
│   └── user.py
├── app.py
├── settings.py
```

When you use Tornado REST framework, you have to tell it which settings you’re using. Do this by using an environment variable: TORNADO_SETTINGS_MODULE.

The value of TORNADO_SETTINGS_MODULE should be in Python path syntax, e.g. foo.settings. Note that the settings module should be on the Python import search path.

``` sh
$ export TORNADO_SETTINGS_MODULE=settings
```

Add the following to your settings.py:

``` python
# settings.py
import os

BASE_DIR = os.path.dirname(__file__)

debug = True
secret_key = "******"

routers_path = os.path.join(BASE_DIR, "routers")
api_prefix = "/api"
trailing_slash = False

mysql_host = "127.0.0.1"
mysql_port = 3306
mysql_username = "root"
mysql_password = "******"
mysql_dbname = ""
```

Creating a model to work with:

``` python
# models/user.py
from tornado_restful import models


class User(models.Model):
    name = models.CharField(max_length=20, unique=True)
    email = models.CharField(max_length=30, unique=True)
```

Creating a serializer class:

``` python
# serializers/user.py
from tornado_restful.models import db
from tornado_restful.serializers import Serializer, fields, validate

from models.user import User


class UserSerializer(Serializer):
    id = fields.Int(dump_only=True)
    name = fields.Str(
        required=True,
        validate=[
            validate.Length(min=2, max=20),
            validate.Regexp("^[a-zA-Z][a-zA-Z0-9_-]*$")
        ],
    )
    email = fields.Email(required=True, validate=validate.Length(max=30))

    async def create(self, validated_data):
        return await db.create(User, **validated_data)

    async def update(self, instance, validated_data):
        instance.email = validated_data.get("email", instance.email)
        await db.update(instance)
        return instance
```


Writing a tornado handlers using our serializer:

``` python
# handlers/user.py
from tornado_restful import status
from tornado_restful.exceptions import NotFoundError
from tornado_restful.handlers import APIHandler

from models.user import User
from serializers.user import UserSerializer


class UserHandler(APIHandler):
    async def list(self):
        limit, offset = self.paginate()
        async with self.application.db.atomic():
            users = await self.application.db.execute(
                User.select().limit(limit).offset(offset)
            )
            total = await self.application.db.count(User.select())
        serializer = UserSerializer(users, many=True)
        self.set_status(status.HTTP_200_OK)
        return self.finish({"total": total, "results": serializer.data})

    async def retrieve(self, pk):
        user = await self.get_object(pk)
        serializer = UserSerializer(user)
        self.set_status(status.HTTP_200_OK)
        return self.finish(serializer.data)

    async def create(self):
        serializer = UserSerializer(data=self.request.data)
        serializer.is_valid(raise_exception=True)
        await serializer.save()
        self.set_status(status.HTTP_201_CREATED)
        return self.finish(serializer.data)

    async def partial_update(self, pk):
        user = await self.get_object(pk)
        serializer = UserSerializer(user, self.request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        await serializer.save()
        self.set_status(status.HTTP_200_OK)
        return self.finish(serializer.data)

    async def destroy(self, pk):
        user = await self.get_object(pk)
        await self.application.db.delete(user)
        self.set_status(status.HTTP_204_NO_CONTENT)
        return self.finish()

    async def get_object(self, pk):
        try:
            user = await self.application.db.get(User, name=pk)
        except User.DoesNotExist:
            raise NotFoundError
        return user
```

Then we need to wire these handlers up. Add the following to your routers/user.py:

``` python
# routers/user.py
from tornado_restful.routers import NestedRouter

from handlers.user import UserHandler

router = NestedRouter()
router.register(r"users", UserHandler)
```

Let's provide an entry file for our project:

``` python
# app.py
import tornado.ioloop
import tornado.web

from tornado_restful.conf import settings
from tornado_restful.handlers import NotFoundHandler
from tornado_restful.models import db
from tornado_restful.shortcuts import get_routes


def runserver():
    app = tornado.web.Application(
        handlers=get_routes(),
        debug=settings.debug,
        default_handler_class=NotFoundHandler,
    )
    app.db = db
    app.listen(8888)
    tornado.ioloop.IOLoop.current().start()


if __name__ == "__main__":
    runserver()
```

Finally, we can start up the Tornado's web server:

``` sh
$ python app.py
```

Now we can testing our API，before that we need to create the user table:

``` python
>>> from tornado_restful.models import database
>>> from models.user import User
>>> database.set_allow_sync(True)
>>> User.create_table()
```


In another terminal window, we can test our API using curl.


``` sh
# create user
$ curl -si -XPOST http://127.0.0.1:8888/api/users \
-H 'Content-Type:application/json' \
-d '{"name": "foo", "email": "foo@gmail.com"}'
HTTP/1.1 201 Created
...

{
  "id": 1,
  "name": "foo",
  "email": "foo@gmail.com"
}
```

``` sh
# create user with the wrong parameters
$ curl -si -XPOST http://127.0.0.1:8888/api/users \
-H 'Content-Type:application/json' \
-d '{"name": "", "email": ""}'
HTTP/1.1 400 Bad Request
...

{
  "message": "Bad Request",
  "detail": {
    "name": [
      "Length must be between 2 and 20.",
      "String does not match expected pattern."
    ],
    "email": [
      "Not a valid email address."
    ]
  }
}
```

``` sh
# list all users:
$ curl -si -XGET http://127.0.0.1:8888/api/users
HTTP/1.1 200 OK
...

{
  "total": 1,
  "results": [
    {
      "id": 1,
      "name": "foo",
      "email": "foo@gmail.com"
    }
  ]
}
```
 
``` sh
# with pagination
$ curl -si -XGET http://127.0.0.1:8888/api/users\?limit\=1\&offset\=1
HTTP/1.1 200 OK
...

{
  "total": 1,
  "results": []
}
```

``` sh
# get user detail
$ curl -si -XGET http://127.0.0.1:8888/api/users/foo
HTTP/1.1 200 OK
...

{
  "id": 1,
  "name": "foo",
  "email": "foo@gmail.com"
}
```

``` sh
# update user info
$ curl -si -XPATCH http://127.0.0.1:8888/api/users/foo \
-H 'Content-Type:application/json' \
-d '{"email": "bar@gmail.com"}'
HTTP/1.1 200 OK
...

{
  "id": 1,
  "name": "foo",
  "email": "bar@gmail.com"
}
```

``` sh
# delete user
$ curl -si -XDELETE "http://127.0.0.1:8888/api/users/foo"
HTTP/1.1 204 No Content
...
```


## User Guide

Full documentation for the project is available at [here][document].


## License

GPL v3 licensed. See the bundled [LICENSE][license] file for more details.


[pypi-version]: http://img.shields.io/pypi/v/tornado-restful.svg
[pypi]: https://pypi.org/project/tornado-restful
[peewee]: https://github.com/coleifer/peewee
[peewee-async]: https://github.com/05bit/peewee-async
[marshmallow]: https://github.com/marshmallow-code/marshmallow
[license]: https://github.com/245967906/tornado-restful/blob/master/LICENSE
[document]: https://github.com/245967906/tornado-restful/wiki
