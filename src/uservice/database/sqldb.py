from datetime import datetime

from sqlalchemy import create_engine, and_, false
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TIMESTAMP as DateTime, String, Text, Boolean

from utils.defs import JOB_STATES
from uservice.database.basedb import BaseJobDatabaseAPI

engine = db_session = None
Base = declarative_base()

MODELS = {}


def get_job_model(project):
    global MODELS, Base
    if project in MODELS:
        return MODELS[project]

    class Job(Base):
        __tablename__ = 'jobs_%s' % project
        # TODO: encoding, index
        # TODO: Throw exception if string too long to fit in column
        id = Column(String(64), primary_key=True)
        job_type = Column(String(64))
        source_url = Column(String(512))
        target_url = Column(String(512))
        added_timestamp = Column(DateTime(), default=datetime.utcnow)
        claimed = Column(Boolean, default=False)
        current_status = Column(String(64), default=JOB_STATES.available)
        worker = Column(String(64))
        worker_output = Column(Text)
        claimed_timestamp = Column(DateTime())
        finished_timestamp = Column(DateTime())
        failed_timestamp = Column(DateTime())
    MODELS[project] = Job
    return Job


class SqlJobDatabase(BaseJobDatabaseAPI):

    def __init__(self, project, dburl=None):
        global engine, db_session
        if not engine:
            engine = create_engine(
                dburl, convert_unicode=True, pool_size=30, pool_recycle=3600)
            db_session = scoped_session(
                sessionmaker(autocommit=True,
                             autoflush=True,
                             bind=engine))
        self.engine = engine
        self.db_session = db_session
        self.model = get_job_model(project)
        self.model.query = db_session.query_property()
        self.model.__table__.create(db_session.bind, checkfirst=True)

    def get_jobs(self, job_id=None, match=None, fields=None):
        if job_id:
            job = self.model.query.filter_by(id=job_id).first()
            jobs = [job] if job else []
        else:
            match = match or {}
            jobs = self.model.query.filter_by(**match)
        for job in jobs:
            job_dict = {c.name: getattr(job, c.name)
                        for c in job.__table__.columns}
            job_dict['type'] = job_dict.pop('job_type')
            if fields:
                job_dict = {k: v for k, v in job_dict.items() if k in fields}
            yield job_dict

    def job_exists(self, job_id):
        if self.model.query.filter_by(id=job_id).first():
            return True
        return False

    def claim_job(self, job_id):
        """Claim a job, return True if the job was claimed"""
        statement = self.model.__table__.update().where(
            and_(self.model.id == job_id,
                 self.model.claimed == false())).values(
                claimed=True)
        result = self.db_session.execute(statement)
        self.db_session.flush()
        return bool(result.rowcount)

    def _update_job(self, job_id, data):
        """
        Args:
           job_id (str): The job id.
           data (dict): Data to update the job object with.
        Returns:
           # bool: True if something changed.
           bool: True if the job exists.

        From http://docs.sqlalchemy.org/en/latest/dialects/mysql.html:

        SQLAlchemy standardizes the DBAPI cursor.rowcount attribute to be the
        usual definition of "number of rows matched by an UPDATE or DELETE"
        statement. This is in contradiction to the default setting on most
        MySQL DBAPI drivers, which is "number of rows actually
        modified/deleted". For this reason, the SQLAlchemy MySQL dialects
        always add the constants.CLIENT.FOUND_ROWS flag, or whatever is
        equivalent for the target dialect, upon connection. This setting is
        currently hardcoded.
        """
        statement = self.model.__table__.update().where(
            self.model.id == job_id).values(**data)
        result = self.db_session.execute(statement)
        self.db_session.flush()
        return bool(result.rowcount)

    def _insert_job(self, job_id, job):
        job['job_type'] = job.pop('type')
        job = self.model(**job)
        self.db_session.add(job)
        self.db_session.flush()

    def close(self):
        self.db_session.remove()

    def drop(self):
        self.model.__table__.drop(self.db_session.bind, checkfirst=True)
        self.db_session.flush()
