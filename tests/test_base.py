#!/usr/bin/env python3
# -*- coding:utf-8 -*-
from dock_worker.core.db import Jobs


def test_main(db):
    new_job = Jobs(source="source", target="target")
    db.add(new_job)
    new_from_db = db.query(Jobs).order_by(Jobs.id.desc()).first()
    assert new_from_db.id == new_job.id
    db.delete(new_from_db)
