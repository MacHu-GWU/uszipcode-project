#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provide utility functions for select operation.
"""

from sqlalchemy import select, func, Column

try:
    from ..pkg.prettytable import from_db_cursor
except:  # pragma: no cover
    from sqlalchemy_mate.pkg.prettytable import from_db_cursor


def count_row(engine, table):
    """
    Return number of rows in a table.

    Example::

        >>> count_row(engine, table_user)
        3

    **中文文档**

    返回一个表中的行数。
    """
    return engine.execute(table.count()).fetchone()[0]


def select_all(engine, table):
    """
    Select everything from a table.

    Example::

        >>> list(select_all(engine, table_user))
        [(1, "Alice"), (2, "Bob"), (3, "Cathy")]

    **中文文档**

    选取所有数据。
    """
    s = select([table])
    return engine.execute(s)


def select_single_column(engine, column):
    """
    Select data from single column.

    Example::

        >>> select_single_column(engine, table_user.c.id)
        [1, 2, 3]

        >>> select_single_column(engine, table_user.c.name)
        ["Alice", "Bob", "Cathy"]
    """
    s = select([column])
    return column.name, [row[0] for row in engine.execute(s)]


def select_many_column(engine, *columns):
    """
    Select data from multiple columns.

    Example::

        >>> select_many_column(engine, table_user.c.id, table_user.c.name)


    :param columns: list of sqlalchemy.Column instance

    :returns headers: headers
    :returns data: list of row

    **中文文档**

    返回多列中的数据。
    """
    if isinstance(columns[0], Column):
        pass
    elif isinstance(columns[0], (list, tuple)):
        columns = columns[0]
    s = select(columns)
    headers = [str(column) for column in columns]
    data = [tuple(row) for row in engine.execute(s)]
    return headers, data


def select_distinct_column(engine, *columns):
    """
    Select distinct column(columns).

    :returns: if single column, return list, if multiple column, return matrix.

    **中文文档**

    distinct语句的语法糖函数。
    """
    if isinstance(columns[0], Column):
        pass
    elif isinstance(columns[0], (list, tuple)):  # pragma: no cover
        columns = columns[0]
    s = select(columns).distinct()
    if len(columns) == 1:
        return [row[0] for row in engine.execute(s)]
    else:
        return [tuple(row) for row in engine.execute(s)]


def select_random(engine, table_or_columns, limit=5):
    """
    Randomly select some rows from table.
    """
    s = select(table_or_columns).order_by(func.random()).limit(limit)
    return engine.execute(s).fetchall()
