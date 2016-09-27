from datetime import datetime
from operator import itemgetter

from sqlalchemy import (
    create_engine, and_, false, func, select, distinct as sqldistinct)
from sqlalchemy.orm import scoped_session, sessionmaker
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Column, TIMESTAMP as DateTime, String, Text, Boolean

from utils.defs import JOB_STATES, TIME_PERIODS, TIME_PERIOD_TO_DELTA
from uservice.database.basedb import BaseJobDatabaseAPI, STATE_TO_TIMESTAMP

engine = db_session = None
Base = declarative_base()

MODELS = {}


def get_job_model(project):
    global MODELS, Base
    if project in MODELS:
        return MODELS[project]

    # TODO: Make a class factory instead (got warning from sqlalchemy when
    #       creating more than one Job class)

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

    @staticmethod
    def _translate_dict(job_dict):
        if 'job_type' in job_dict:
            job_dict['type'] = job_dict.pop('job_type')
        return job_dict

    def _get_job(self, job_id, fields):
        job = self.model.query.filter_by(id=job_id).first()
        if not job:
            return
        job_dict = {c.name: getattr(job, c.name)
                    for c in job.__table__.columns}
        job_dict = self._translate_dict(job_dict)
        if fields:
            job_dict = {k: v for k, v in job_dict.items() if k in fields}
        return job

    def _get_jobs(self, fields, match=None, start_time=None, end_time=None,
                  time_field=None, limit=None):
        """See parent docstring"""
        expressions = []
        if match:
            for k, v in match.items():
                if k == 'type':
                    k = 'job_type'
                expressions.append(getattr(self.model, k) == v)
        timestamp_col = None
        if time_field:
            timestamp_col = getattr(self.model, time_field)
            if start_time:
                expressions.append(timestamp_col >= start_time)
            if end_time:
                expressions.append(timestamp_col < end_time)
        whereclause = and_(*expressions) if expressions else None
        if 'type' in fields:
            fields.remove('type')
            fields.append('job_type')

        fields = [getattr(self.model, field) for field in fields]
        query = select(fields, whereclause=whereclause, order_by=timestamp_col,
                       limit=limit)
        for row in self.db_session.execute(query):
            job_dict = dict(zip(row.keys(), row))
            yield self._translate_dict(job_dict)

    def count_jobs(self, group_by='current_status'):
        group_by = getattr(self.model, group_by)
        query = select([func.count('*'), group_by], group_by=group_by)
        return {row[1]: row[0] for row in self.db_session.execute(query)}

    def count_jobs_per_time_period(self, job_state,
                                   time_period=TIME_PERIODS.hourly,
                                   count_field_name=None,
                                   distinct=False):
        """See parent docstring"""
        ts = getattr(self.model, STATE_TO_TIMESTAMP[job_state])
        count = '*'
        if count_field_name:
            count = getattr(self.model, count_field_name)
        if distinct:
            count = sqldistinct(count)

        group_by = []
        format_str = ''
        periods = [(TIME_PERIODS.yearly, func.year, '%Y'),
                   (TIME_PERIODS.monthly, func.month, '-%m'),
                   (TIME_PERIODS.daily, func.day, '-%d'),
                   (TIME_PERIODS.hourly, func.hour, ' %H:00')]
        for period, sqlfunc, fmt in periods:
            group_by.append(sqlfunc(ts))
            format_str += fmt
            if period == time_period:
                break

        query = select([func.count(count)] + group_by, group_by=group_by)
        counts = []
        for row in self.db_session.execute(query):
            if not row[1]:
                # These jobs have not been in this job state.
                continue
            dt = datetime(*row[1:])
            counts.append({
                'period': dt.strftime(format_str),
                'count': row[0],
                'start_time': dt,
                'end_time': dt + TIME_PERIOD_TO_DELTA[time_period]})
        counts.sort(key=itemgetter('start_time'))
        return counts

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
