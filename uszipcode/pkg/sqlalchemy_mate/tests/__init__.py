#!/usr/bin/env python
# -*- coding: utf-8 -*-

from sqlalchemy import create_engine, MetaData, Table, Column
from sqlalchemy import String, Integer
from sqlalchemy.ext.declarative import declarative_base

engine = create_engine("sqlite:///:memory:")
metadata = MetaData()

t_smart_insert = Table(
    "smart_insert", metadata,
    Column("id", Integer, primary_key=True),
)

t_user = Table(
    "user", metadata,
    Column("user_id", Integer, primary_key=True),
    Column("name", String),
)

t_inv = Table(
    "inventory", metadata,
    Column("store_id", Integer, primary_key=True),
    Column("item_id", Integer, primary_key=True),
)

metadata.create_all(engine)


def insert_t_user():
    engine.execute(t_user.delete())

    data = [{"user_id": 1, "name": "Alice"},
            {"user_id": 2, "name": "Bob"},
            {"user_id": 3, "name": "Cathy"}]
    engine.execute(t_user.insert(), data)


insert_t_user()


def insert_t_inv():
    data = [{"store_id": 1, "item_id": 1},
            {"store_id": 1, "item_id": 2},
            {"store_id": 2, "item_id": 1},
            {"store_id": 2, "item_id": 2}]
    engine.execute(t_inv.insert(), data)


insert_t_inv()

Base = declarative_base()


class User(Base):
    __tablename__ = "user"
    user_id = Column(Integer, primary_key=True)
    name = Column(String)


class Inventory(Base):
    __tablename__ = "inventory"
    store_id = Column(Integer, primary_key=True)
    item_id = Column(Integer, primary_key=True)
