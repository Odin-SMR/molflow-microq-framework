import json
import random
from datetime import datetime

from sqlalchemy import select, and_, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import (
    Column, TIMESTAMP as DateTime, String, Text, Integer, Float)

from flask import g

from uservice.database.basesqldb import SqlDB

Base = declarative_base()


def get_db():
    if not hasattr(g, 'project_database'):
        g.project_database = ProjectsDB()
    return g.project_database


class Project(Base):

    __tablename__ = 'projects'

    # TODO: encoding
    # TODO: Throw exception if string too long to fit in column:
    # http://stackoverflow.com/questions/2317081/sqlalchemy-maximum-column-length
    # Set when created, not possible to update
    id = Column(String(64), primary_key=True)
    created_timestamp = Column(DateTime(), default=datetime.utcnow, index=True)
    created_by_user = Column(String(32), index=True)

    # Set and updated by users
    name = Column(String(128))
    processing_image_url = Column(String(512))
    environment = Column(Text)
    deadline = Column(DateTime(), index=True)

    # Internal
    last_added_timestamp = Column(DateTime(), index=True)
    nr_added = Column(Integer, default=0)
    last_claimed_timestamp = Column(DateTime(), index=True)
    nr_claimed = Column(Integer, default=0)
    nr_finished = Column(Integer, default=0)
    nr_failed = Column(Integer, default=0)
    processing_time = Column(Float, default=0)


class ProjectsDB(object):

    # These fields are stored as json strings in the database:
    JSON_FIELDS = ['environment']

    UPDATED_BY_USER = set([
        'environment', 'deadline', 'name', 'processing_image_url'])

    INCREMENTAL_FIELDS = set([
        'nr_added', 'nr_claimed', 'nr_finished', 'nr_failed',
        'processing_time'])

    # Use this when calculting project prio when no jobs have been processed.
    # Use a relativly high value so that we get at least one job processed,
    # then we'll get a more correct estimation next time.
    DEFAULT_MEAN_PROCESSING_TIME = 3600

    def __init__(self):
        self.db = SqlDB(Project)

    def get_prio_project(self):
        """Randomly select a project based on their prio score"""
        projects = self.get_prio_scores()

        total = sum((score for _, score in projects))
        rand = random.uniform(0, total)
        upto = 0
        for project, score in projects:
            if upto + score >= rand:
                return project
            upto += score
        assert False, "Shouldn't get here"

    def get_prio_scores(self):
        """Return project id and prio score for all projects.

        prio = "nr jobs left to do" * "mean time for each job" /
                  "time to deadline"
        """
        # TODO: Do the prio calc as an sql query?
        projects = self.get_projects(fields=[
            'id', 'nr_added', 'nr_claimed', 'nr_finished', 'nr_failed',
            'processing_time', 'deadline'], only_active=True)

        now = datetime.utcnow()
        return [(p['id'], self.calc_prio_score(p, now)) for p in projects]

    @staticmethod
    def calc_prio_score(project_data, now):
        p = project_data
        if p['nr_added'] <= p['nr_claimed']:
            return 0
        if not p['deadline']:
            return 1
        if not p['processing_time'] or not (
                p['nr_finished'] or p['nr_failed']):
            mean_processing_time = ProjectsDB.DEFAULT_MEAN_PROCESSING_TIME
        else:
            mean_processing_time = p['processing_time'] / (
                p['nr_finished'] + p['nr_failed'])
        numerator = (p['nr_added'] - p['nr_claimed']) * mean_processing_time
        if p['deadline'] < now:
            return numerator
        return numerator / (p['deadline'] - now).total_seconds()

    def get_projects(self, match=None, limit=None, fields=None,
                     only_active=False):
        """Yield projects as dicts"""
        expressions = []
        if match:
            for k, v in match.items():
                expressions.append(self.db.model.__table__.c[k] == v)
        if only_active:
            expressions.append(
                self.db.model.__table__.c['nr_added'] >
                self.db.model.__table__.c['nr_claimed'])
        whereclause = and_(*expressions) if expressions else None
        if fields:
            fields = [self.db.model.__table__.c[field] for field in fields]
        else:
            fields = self.db.model.__table__.c.values()

        query = select(
            fields,
            whereclause=whereclause,
            order_by=self.db.model.last_claimed_timestamp,
            limit=limit)
        for row in self.db.session.execute(query):
            project_dict = dict(zip(row.keys(), row))
            yield self.decode_json(project_dict)

    @staticmethod
    def _getattr_from_column_name(job, column_name):
        """Return the value of a column in a job instance by column name"""
        for attr, column in inspect(job.__class__).c.items():
            if column.name == column_name:
                return getattr(job, attr)

    def get_project(self, project_id, fields=None):
        project = self.db.model.query.filter_by(id=project_id).first()
        if not project:
            return
        project_dict = {c.name: self._getattr_from_column_name(project, c.name)
                        for c in project.__table__.columns}
        if fields:
            project_dict = {
                k: v for k, v in project_dict.items() if k in fields}
        return self.decode_json(project_dict)

    def update_project(self, project_id, **data):
        data = self.encode_json(data)
        values = {}
        for field, value in data.items():
            if field in self.INCREMENTAL_FIELDS:
                values[self.db.model.__table__.c[field]] = (
                    self.db.model.__table__.c[field] + value)
            else:
                values[self.db.model.__table__.c[field]] = value
        statement = self.db.model.__table__.update().where(
            self.db.model.id == project_id).values(values)
        result = self.db.session.execute(statement)
        self.db.session.flush()
        return bool(result.rowcount)

    def insert_project(self, project_id, user_name, **kwargs):
        project = kwargs
        project['id'] = project_id
        project['created_by_user'] = user_name
        if 'name' not in project:
            project['name'] = project_id
        project = self.db.model(**self.encode_json(project))
        self.db.session.add(project)
        self.db.session.flush()

    def remove_project(self, project_id):
        project = self.db.model.query.filter_by(id=project_id).first()
        if project:
            self.db.session.delete(project)
            self.db.session.flush()

    def project_exists(self, project_id):
        if self.db.model.query.filter_by(id=project_id).first():
            return True
        return False

    def job_added(self, project_id):
        """Report that a job was added to this project.

        Return False if the project does not exist.
        """
        return self.update_project(
            project_id, last_added_timestamp=datetime.utcnow(), nr_added=1)

    def job_claimed(self, project_id):
        """Report that a job in this project was claimed."""
        return self.update_project(
            project_id, last_claimed_timestamp=datetime.utcnow(), nr_claimed=1)

    def job_finished(self, project_id, processing_time):
        """Report that a job in this project was finished"""
        return self.update_project(
            project_id, nr_finished=1, processing_time=processing_time)

    def job_failed(self, project_id, processing_time):
        """Report that a job in this project failed"""
        return self.update_project(
            project_id, nr_failed=1, processing_time=processing_time)

    @classmethod
    def encode_json(cls, job_dict):
        for field in cls.JSON_FIELDS:
            if field in job_dict:
                job_dict[field] = json.dumps(job_dict[field] or {})
        return job_dict

    @classmethod
    def decode_json(cls, job_dict):
        for field in cls.JSON_FIELDS:
            if field in job_dict:
                job_dict[field] = json.loads(job_dict[field] or '{}')
        return job_dict
