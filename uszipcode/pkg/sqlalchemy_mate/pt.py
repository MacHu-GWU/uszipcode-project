#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Pretty Table support.
"""

from sqlalchemy import select, Table
from sqlalchemy.orm import sessionmaker, Query
from sqlalchemy.ext.declarative.api import DeclarativeMeta
from sqlalchemy.sql.selectable import Select
from sqlalchemy.engine.result import ResultProxy

try:
    from .utils import execute_query_return_result_proxy
    from .pkg.prettytable import from_db_cursor, PrettyTable
except:  # pragma: no cover
    from sqlalchemy_mate.utils import execute_query_return_result_proxy
    from sqlalchemy_mate.pkg.prettytable import from_db_cursor, PrettyTable


def from_sql(sql, engine, limit=None):
    """
    Create a :class:`prettytable.PrettyTable` from :class:`sqlalchemy.select`.

    :param sql: a ``sqlalchemy.sql.selectable.Select`` object.
    :param engine: an ``sqlalchemy.engine.base.Engine`` object.
    :param limit: int, limit rows to return.

    **中文文档**

    将sqlalchemy的sql expression query结果放入prettytable中.

    .. note::

        注意, from_db_cursor是从原生的数据库游标通过调用fetchall()方法来获取数据。
        而sqlalchemy返回的是ResultProxy类。所以我们需要从中获取游标
        至于为什么不能直接使用 from_db_cursor(engine.execute(sql).cursor) 的语法
        我也不知道为什么.
    """
    if limit is not None:
        sql = sql.limit(limit)
    result_proxy = engine.execute(sql)
    return from_db_cursor(result_proxy.cursor)


def from_query(query, engine=None, limit=None):
    """
    Execute an ORM style query, and return the result in
    :class:`prettytable.PrettyTable`.

    :param query: an ``sqlalchemy.orm.Query`` object.
    :param engine: an ``sqlalchemy.engine.base.Engine`` object.
    :param limit: int, limit rows to return.

    :return: a ``prettytable.PrettyTable`` object

    **中文文档**

    将通过ORM的查询结果中的数据放入prettytable中.
    """
    if limit is not None:
        query = query.limit(limit)
    result_proxy = execute_query_return_result_proxy(query)
    return from_db_cursor(result_proxy.cursor)


def from_table(table, engine, limit=None):
    """
    Select data in a database table and put into prettytable.

    Create a :class:`prettytable.PrettyTable` from :class:`sqlalchemy.Table`.

    **中文文档**

    将数据表中的数据放入prettytable中.
    """
    sql = select([table])
    if limit is not None:
        sql = sql.limit(limit)
    result_proxy = engine.execute(sql)
    return from_db_cursor(result_proxy.cursor)


def from_object(orm_class, engine, limit=None):
    """
    Select data from the table defined by a ORM class, and put into prettytable

    :param orm_class: an orm class inherit from
        ``sqlalchemy.ext.declarative.declarative_base()``
    :param engine: an ``sqlalchemy.engine.base.Engine`` object.
    :param limit: int, limit rows to return.

    **中文文档**

    将数据对象的数据放入prettytable中.
    """
    Session = sessionmaker(bind=engine)
    ses = Session()
    query = ses.query(orm_class)
    if limit is not None:
        query = query.limit(limit)
    result_proxy = execute_query_return_result_proxy(query)
    ses.close()
    return from_db_cursor(result_proxy.cursor)


def from_resultproxy(result_proxy):
    """
    Construct a Prettytable from ``ResultProxy``.

    :param result_proxy: a ``sqlalchemy.engine.result.ResultProxy`` object.
    """
    return from_db_cursor(result_proxy.cursor)


def from_data(data):
    """
    Construct a Prettytable from list of rows.
    """
    if len(data) == 0:  # pragma: no cover
        return None
    else:
        ptable = PrettyTable()
        ptable.field_names = data[0].keys()
        for row in data:
            ptable.add_row(row)
        return ptable


def from_everything(everything, engine, limit=None):
    """
    Construct a Prettytable from any kinds of sqlalchemy query.
    """
    if isinstance(everything, Table):
        return from_table(everything, engine, limit=limit)

    if type(everything) is DeclarativeMeta:
        return from_object(everything, engine, limit=limit)

    if isinstance(everything, Query):
        return from_query(everything, engine, limit=limit)

    if isinstance(everything, Select):
        return from_sql(everything, engine, limit=limit)

    if isinstance(everything, ResultProxy):
        return from_resultproxy(everything)

    if isinstance(everything, list):
        return from_data(everything)
