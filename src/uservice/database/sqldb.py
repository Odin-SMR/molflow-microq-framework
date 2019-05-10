from datetime import datetime
from operator import itemgetter

from sqlalchemy import (
    and_, false, func, select, distinct as sqldistinct, inspect)
from sqlalchemy.ext.declarative import declarative_base, declared_attr
from sqlalchemy.ext.declarative.base import _declarative_constructor
from sqlalchemy import (
    Column, TIMESTAMP as DateTime, String, Text, Boolean, Float, Index)

from ..utils.defs import JOB_STATES, TIME_PERIODS, TIME_PERIOD_TO_DELTA
from .basedb import BaseJobDatabaseAPI, STATE_TO_TIMESTAMP
from .basesqldb import SqlDB

MODELS = {}


class JobBase:

    @declared_attr
    def __tablename__(cls):
        return 'jobs_%s' % cls.__name__[3:]

    # TODO: encoding
    # TODO: Throw exception if string too long to fit in column

    # Job data
    id = Column(String(64), primary_key=True)
    # Note: The attribute name is not the same as the column name
    #       because 'type' is reserved in python.
    job_type = Column('type', String(64))
    source_url = Column(String(512))
    target_url = Column(String(512))
    view_result_url = Column(String(512))

    # Job status data
    added_timestamp = Column(DateTime(), default=datetime.utcnow, index=True)
    claimed = Column(Boolean, default=False)
    current_status = Column(
        String(64), default=JOB_STATES.available, index=True)
    worker = Column(String(64), index=True)
    worker_output = Column(Text)
    claimed_timestamp = Column(DateTime(), index=True)
    finished_timestamp = Column(DateTime(), index=True)
    failed_timestamp = Column(DateTime(), index=True)
    processing_time = Column(Float)

    @declared_attr
    def __table_args__(cls):
        return (Index('claimed_idx', "claimed", "type"), )


def _job_constructor(self, **kwargs):
    kwargs['job_type'] = kwargs.pop('type', None)
    _declarative_constructor(self, **kwargs)

Base = declarative_base(cls=JobBase, constructor=_job_constructor)


def get_job_model(project):
    global MODELS, Base
    if project in MODELS:
        return MODELS[project]
    Job = type('Job{}'.format(project), (Base,), {})
    MODELS[project] = Job
    return Job


class SqlJobDatabase(BaseJobDatabaseAPI):

    def __init__(self, project):
        self.db = SqlDB(get_job_model(project))
        super(SqlJobDatabase, self).__init__(project)

    @staticmethod
    def _getattr_from_column_name(job, column_name):
        """Return the value of a column in a job instance by column name"""
        for attr, column in inspect(job.__class__).c.items():
            if column.name == column_name:
                return getattr(job, attr)

    def _get_job(self, job_id, fields):
        job = self.db.model.query.filter_by(id=job_id).first()
        if not job:
            return
        job_dict = {c.name: self._getattr_from_column_name(job, c.name)
                    for c in job.__table__.columns}
        if fields:
            job_dict = {k: v for k, v in job_dict.items() if k in fields}
        return job_dict

    def _get_jobs(self, fields, match=None, start_time=None, end_time=None,
                  time_field=None, limit=None):
        """See parent docstring"""
        expressions = []
        if match:
            for k, v in match.items():
                expressions.append(self.db.model.__table__.c[k] == v)
        timestamp_col = None
        if time_field:
            timestamp_col = getattr(self.db.model, time_field)
            if start_time:
                expressions.append(timestamp_col >= start_time)
            if end_time:
                expressions.append(timestamp_col < end_time)
        whereclause = and_(*expressions) if expressions else None

        fields = [self.db.model.__table__.c[field] for field in fields]
        query = select(fields, whereclause=whereclause, order_by=timestamp_col,
                       limit=limit)
        for row in self.db.session.execute(query):
            job_dict = dict(zip(row.keys(), row))
            yield job_dict

    def count_jobs(self, group_by='current_status'):
        group_by = getattr(self.db.model, group_by)
        query = select([func.count('*'), group_by], group_by=group_by)
        return {row[1]: row[0] for row in self.db.session.execute(query)}

    def count_jobs_per_time_period(self, job_state,
                                   time_period=TIME_PERIODS.hourly,
                                   count_field_name=None,
                                   distinct=False,
                                   start_time=None,
                                   end_time=None):
        """See parent docstring"""
        ts = getattr(self.db.model, STATE_TO_TIMESTAMP[job_state])
        count = '*'
        if count_field_name:
            count = getattr(self.db.model, count_field_name)
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

        expressions = []
        if start_time or end_time:
            if start_time:
                expressions.append(ts >= start_time)
            if end_time:
                expressions.append(ts < end_time)
        whereclause = and_(*expressions) if expressions else None

        query = select([func.count(count)] + group_by, whereclause=whereclause,
                       group_by=group_by)
        counts = []
        for row in self.db.session.execute(query):
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
        if self.db.model.query.filter_by(id=job_id).first():
            return True
        return False

    def claim_job(self, job_id):
        """Claim a job, return True if the job was claimed"""
        statement = self.db.model.__table__.update().where(
            and_(self.db.model.id == job_id,
                 self.db.model.claimed == false())).values(
                     claimed=True)
        result = self.db.session.execute(statement)
        self.db.session.flush()
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
        statement = self.db.model.__table__.update().where(
            self.db.model.id == job_id).values(**data)
        result = self.db.session.execute(statement)
        self.db.session.flush()
        return bool(result.rowcount)

    def _insert_job(self, job_id, job):
        job = self.db.model(**job)
        self.db.session.add(job)
        self.db.session.flush()

    def close(self):
        self.db.session.remove()

    def drop(self):
        self.db.model.__table__.drop(self.db.session.bind, checkfirst=True)
        self.db.session.flush()
