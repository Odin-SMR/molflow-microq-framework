from datetime import datetime

from sqlalchemy import select, and_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TIMESTAMP as DateTime, String

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
    name = Column(String(64), primary_key=True)
    created_timestamp = Column(DateTime(), default=datetime.utcnow, index=True)
    created_by_user = Column(String(32), index=True)
    last_added_timestamp = Column(DateTime(), index=True)
    last_claimed_timestamp = Column(DateTime(), index=True)
    deadline_timestamp = Column(DateTime(), index=True)


class ProjectsDB(object):

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
            yield project_dict

    def update_project(self, name, **data):
        statement = self.db.model.__table__.update().where(
            self.db.model.name == name).values(**data)
        result = self.db.session.execute(statement)
        self.db.session.flush()
        return bool(result.rowcount)

    def insert_project(self, name, user_name, **kwargs):
        project = kwargs
        project['name'] = name
        project['created_by_user'] = user_name
        project = self.db.model(**project)
        self.db.session.add(project)
        self.db.session.flush()

    def remove_project(self, name):
        project = self.db.model.query.filter_by(name=name).first()
        if project:
            self.db.session.delete(project)
            self.db.session.flush()

    def project_exists(self, name):
        if self.db.model.query.filter_by(name=name).first():
            return True
        return False

    def job_added(self, project_name):
        """Report that a job was added to this project.

        Return False if the project does not exist.
        """
        return self.update_project(
            project_name, last_added_timestamp=datetime.utcnow())

    def job_claimed(self, project_name):
        """Report that a job in this project was claimed."""
        return self.update_project(
            project_name, last_claimed_timestamp=datetime.utcnow())
