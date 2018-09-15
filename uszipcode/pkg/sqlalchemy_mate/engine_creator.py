#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
This module provides functionary interface to create engine.
"""

from sqlalchemy import create_engine


def preprocess_driver(driver=None):
    if driver is None:
        return ""
    else:
        return "+%s" % driver


def preprocess_port(port=None):
    if port is None:
        return ""
    else:
        return ":%s" % port


template = "{dialect}{driver}://{username}:{password}@{host}{port}/{database}"


def format_url(dialect, driver, username, password, host, port, database):
    return template.format(
        dialect=dialect,
        driver=preprocess_driver(driver),
        username=username,
        password=password,
        host=host,
        port=preprocess_port(port),
        database=database,
    )


# sqlite

def _create_sqlite(path=":memory:"):
    return "sqlite:///{path}".format(path=path)


def create_sqlite(path=":memory:", **kwargs):  # pragma: no cover
    """
    create an engine connected to a sqlite database. By default, use in memory
    database.
    """
    return create_engine(_create_sqlite(path), **kwargs)


# postgresql

def _create_postgresql(username, password, host, port, database):
    return format_url(
        "postgresql", None, username, password, host, port, database,
    )


def create_postgresql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using psycopg2.
    """
    return create_engine(
        _create_postgresql(username, password, host, port, database),
        **kwargs
    )


def _create_postgresql_psycopg2(username, password, host, port, database):
    return format_url(
        "postgresql", "psycopg2", username, password, host, port, database,
    )


def create_postgresql_psycopg2(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using psycopg2.
    """
    return create_engine(
        _create_postgresql_psycopg2(username, password, host, port, database),
        **kwargs
    )


def _create_postgresql_pg8000(username, password, host, port, database):
    return format_url(
        "postgresql", "pg8000", username, password, host, port, database,
    )


def create_postgresql_pg8000(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using pg8000.
    """
    return create_engine(
        _create_postgresql_pg8000(username, password, host, port, database),
        **kwargs
    )


def _create_postgresql_pygresql(username, password, host, port, database):
    return format_url(
        "postgresql", "pygresql", username, password, host, port, database,
    )


def create_postgresql_pygresql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using pygresql.
    """
    return create_engine(
        _create_postgresql_pygresql(username, password, host, port, database),
        **kwargs
    )


def _create_postgresql_psycopg2cffi(username, password, host, port, database):
    return format_url(
        "postgresql", "psycopg2cffi", username, password, host, port, database,
    )


def create_postgresql_psycopg2cffi(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using psycopg2cffi.
    """
    return create_engine(
        _create_postgresql_psycopg2cffi(
            username, password, host, port, database),
        **kwargs
    )


def _create_postgresql_pypostgresql(username, password, host, port, database):
    return format_url(
        "postgresql", "pypostgresql", username, password, host, port, database,
    )


def create_postgresql_pypostgresql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a postgresql database using pypostgresql.
    """
    return create_engine(
        _create_postgresql_pypostgresql(
            username, password, host, port, database),
        **kwargs
    )


# mysql

def _create_mysql(username, password, host, port, database):
    return format_url(
        "mysql", None, username, password, host, port, database,
    )


def create_mysql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using mysqldb.
    """
    return create_engine(
        _create_mysql(username, password, host, port, database),
        **kwargs
    )


def _create_mysql_mysqldb(username, password, host, port, database):
    return format_url(
        "mysql", "mysqldb", username, password, host, port, database,
    )


def create_mysql_mysqldb(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using mysqldb.
    """
    return create_engine(
        _create_mysql_mysqldb(username, password, host, port, database),
        **kwargs
    )


def _create_mysql_mysqlconnector(username, password, host, port, database):
    return format_url(
        "mysql", "mysqlconnector", username, password, host, port, database,
    )


def create_mysql_mysqlconnector(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using mysqlconnector.
    """
    return create_engine(
        _create_mysql_mysqlconnector(username, password, host, port, database),
        **kwargs
    )


def _create_mysql_oursql(username, password, host, port, database):
    return format_url(
        "mysql", "oursql", username, password, host, port, database,
    )


def create_mysql_oursql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using oursql.
    """
    return create_engine(
        _create_mysql_oursql(username, password, host, port, database),
        **kwargs
    )


def _create_mysql_pymysql(username, password, host, port, database):
    return format_url(
        "mysql", "pymysql", username, password, host, port, database,
    )


def create_mysql_pymysql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using pymysql.
    """
    return create_engine(
        _create_mysql_pymysql(username, password, host, port, database),
        **kwargs
    )


def _create_mysql_cymysql(username, password, host, port, database):
    return format_url(
        "mysql", "cymysql", username, password, host, port, database,
    )


def create_mysql_cymysql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mysql database using cymysql.
    """
    return create_engine(
        _create_mysql_cymysql(username, password, host, port, database),
        **kwargs
    )


# oracle

def _create_oracle(username, password, host, port, database):
    return format_url(
        "oracle", None, username, password, host, port, database,
    )


def create_oracle(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a oracle database using cx_oracle.
    """
    return create_engine(
        _create_oracle(username, password, host, port, database),
        **kwargs
    )


def _create_oracle_cx_oracle(username, password, host, port, database):
    return format_url(
        "oracle", "cx_oracle", username, password, host, port, database,
    )


def create_oracle_cx_oracle(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a oracle database using cx_oracle.
    """
    return create_engine(
        _create_oracle_cx_oracle(username, password, host, port, database),
        **kwargs
    )


# mssql

def _create_mssql_pyodbc(username, password, host, port, database):
    return format_url(
        "mssql", "pyodbc", username, password, host, port, database,
    )


def create_mssql_pyodbc(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mssql database using pyodbc.
    """
    return create_engine(
        _create_mssql_pyodbc(username, password, host, port, database),
        **kwargs
    )


def _create_mssql_pymssql(username, password, host, port, database):
    return format_url(
        "mssql", "pymssql", username, password, host, port, database,
    )


def create_mssql_pymssql(username, password, host, port, database, **kwargs):  # pragma: no cover
    """
    create an engine connected to a mssql database using pymssql.
    """
    return create_engine(
        _create_mssql_pymssql(username, password, host, port, database),
        **kwargs
    )
