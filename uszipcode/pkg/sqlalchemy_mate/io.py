#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database data/Local File I/O module.
"""

import os
from sqlalchemy import select


def sql_to_csv(sql, engine, filepath, chunksize=1000, overwrite=False):
    """
    Export sql result to csv file.

    :param sql: :class:`sqlalchemy.sql.selectable.Select` instance.
    :param engine: :class:`sqlalchemy.engine.base.Engine`.
    :param filepath: file path.
    :param chunksize: number of rows write to csv each time.
    :param overwrite: bool, if True, avoid to overite existing file.

    **中文文档**

    将执行sql的结果中的所有数据, 以生成器的方式(一次只使用一小部分内存), 将
    整个结果写入csv文件。
    """
    if overwrite:  # pragma: no cover
        if os.path.exists(filepath):
            raise Exception("'%s' already exists!" % filepath)

    import pandas as pd

    columns = [str(column.name) for column in sql.columns]
    with open(filepath, "w") as f:
        # write header
        df = pd.DataFrame([], columns=columns)
        df.to_csv(f, header=True, index=False)

        # iterate big database table
        result_proxy = engine.execute(sql)
        while True:
            data = result_proxy.fetchmany(chunksize)
            if len(data) == 0:
                break
            else:
                df = pd.DataFrame(data, columns=columns)
                df.to_csv(f, header=False, index=False)


def table_to_csv(table, engine, filepath, chunksize=1000, overwrite=False):
    """
    Export entire table to a csv file.

    :param table: :class:`sqlalchemy.Table` instance.
    :param engine: :class:`sqlalchemy.engine.base.Engine`.
    :param filepath: file path.
    :param chunksize: number of rows write to csv each time.
    :param overwrite: bool, if True, avoid to overite existing file.

    **中文文档**

    将整个表中的所有数据, 写入csv文件。
    """
    sql = select([table])
    sql_to_csv(sql, engine, filepath, chunksize)
