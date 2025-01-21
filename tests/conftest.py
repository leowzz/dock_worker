#!/usr/bin/env python3
# -*- coding:utf-8 -*-

import pytest


@pytest.fixture(scope="session")
def db():
    from dock_worker.core.db import init_db, get_db
    init_db()
    with get_db() as db:
        yield db
