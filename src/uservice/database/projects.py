import json
from datetime import datetime

from sqlalchemy import select, and_, inspect
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TIMESTAMP as DateTime, String, Text

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
    last_claimed_timestamp = Column(DateTime(), index=True)


class ProjectsDB(object):

    # These fields are stored as json strings in the database:
    JSON_FIELDS = ['environment']

    UPDATED_BY_USER = set([
        'environment', 'deadline', 'name', 'processing_image_url'])

    def __init__(self):
        self.db = SqlDB(Project)

    def get_projects(self, match=None, limit=None):
        """Yield projects as dicts"""
        expressions = []
        if match:
            for k, v in match.items():
                expressions.append(self.db.model.__table__.c[k] == v)
        whereclause = and_(*expressions) if expressions else None
        query = select(
            self.db.model.__table__.c.values(),
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
        statement = self.db.model.__table__.update().where(
            self.db.model.id == project_id).values(**self.encode_json(data))
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
            project_id, last_added_timestamp=datetime.utcnow())

    def job_claimed(self, project_id):
        """Report that a job in this project was claimed."""
        return self.update_project(
            project_id, last_claimed_timestamp=datetime.utcnow())

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
