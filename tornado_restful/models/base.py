import peewee
import peewee_async

from tornado_restful.conf import settings

database = peewee_async.MySQLDatabase(
    host=settings.mysql_host,
    port=settings.mysql_port,
    user=settings.mysql_username,
    password=settings.mysql_password,
    database=settings.mysql_dbname,
)
database.set_allow_sync(False)

db = peewee_async.Manager(database)


class Model(peewee.Model):
    class Meta:
        database = database
