from __future__ import absolute_import

import six
import zlib
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql.base import ischema_names

json = None
try:
    import anyjson as json
except ImportError:
    import json as json

try:
    from sqlalchemy.dialects.postgresql import JSON

    has_postgres_json = True
except ImportError:
    class PostgresJSONType(sa.types.UserDefinedType):
        """
        Text search vector type for postgresql.
        """

        def get_col_spec(self):
            return 'json'

    ischema_names['json'] = PostgresJSONType
    has_postgres_json = False


class CompressedJSONType(sa.types.TypeDecorator):
    """
    JSONType offers way of saving JSON data structures to database. On
    PostgreSQL the underlying implementation of this data type is 'json' while
    on other databases its simply 'text'.

    ::


        from sqlalchemy_utils import JSONType


        class Product(Base):
            __tablename__ = 'product'
            id = sa.Column(sa.Integer, autoincrement=True)
            name = sa.Column(sa.Unicode(50))
            details = sa.Column(JSONType)


        product = Product()
        product.details = {
            'color': 'red',
            'type': 'car',
            'max-speed': '400 mph'
        }
        session.commit()
    """
    impl = sa.LargeBinary

    def __init__(self, *args, **kwargs):
        super(CompressedJSONType, self).__init__(*args, **kwargs)

    def load_dialect_impl(self, dialect):
        if dialect.name == 'postgresql':
            # Use the native JSON type.
            if has_postgres_json:
                return dialect.type_descriptor(JSON())
            else:
                return dialect.type_descriptor(PostgresJSONType())
        else:
            return dialect.type_descriptor(self.impl)

    def process_bind_param(self, value, dialect):
        if dialect.name == 'postgresql' and has_postgres_json:
            return value
        if value is not None:
            value = six.binary_type(zlib.compress(
                json.dumps(value).encode("utf-8")))
        return value

    def process_result_value(self, value, dialect):
        if dialect.name == 'postgresql':
            return value
        if value is not None:
            value = json.loads(zlib.decompress(value).decode("utf-8"))
        return value


if __name__ == "__main__":
    from sqlalchemy import MetaData, Table, Column, Integer, select
    from uszipcode.packages.sqlalchemy_mate import engine_creator

    engine = engine_creator.create_sqlite()
    metadata = MetaData()
    t_user = Table(
        "user", metadata,
        Column("id", Integer),
        Column("profile", CompressedJSONType),
    )
    metadata.create_all(engine)

    engine.execute(t_user.insert(), {"id": 1, "profile": {
                   "lastname": "John", "firstname": "David"}})
    user_data = engine.execute(select([t_user])).fetchone()
    assert user_data["profile"] == {"lastname": "John", "firstname": "David"}
