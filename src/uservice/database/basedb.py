from collections import OrderedDict
from datetime import datetime

from flask import g

from utils.defs import JOB_STATES, TIME_PERIODS

STATE_TO_TIMESTAMP = {
    JOB_STATES.available: 'added_timestamp',
    JOB_STATES.claimed: 'claimed_timestamp',
    JOB_STATES.finished: 'finished_timestamp',
    JOB_STATES.failed: 'failed_timestamp'}


def get_db(project, cls, **dbsettings):
    if not hasattr(g, 'job_databases'):
        g.job_databases = {}
    if project not in g.job_databases:
        g.job_databases[project] = cls(project, **dbsettings)
    return g.job_databases[project]


class DBError(Exception):
    pass


class BaseJobDatabaseAPI(object):
    """Base API to a database.

    Inherit and implement:

    * __init__
    * close
    * get_jobs
    * job_exists
    * _update_job
    * _insert_job
    * drop
    """
    # TODO: Put this in a job model
    CLAIMED = 'claimed'
    CLAIMED_TIMESTAMP = 'claimed_timestamp'
    PUBLIC_FIELDS = [
        'id', 'type', 'source_url', 'claimed', 'current_status', 'worker',
        'added_timestamp', 'claimed_timestamp', 'failed_timestamp',
        'finished_timestamp', 'worker_output']
    PUBLIC_LISTING_FIELDS = PUBLIC_FIELDS[:-1]

    def __init__(self, project):
        self.project = project

    def insert_job(self, job_id, job_data):
        self._verify(job_data)
        return self._insert_job(job_id, job_data)

    def get_jobs(self, job_id=None, match=None, fields=None):
        raise NotImplementedError

    def count_jobs(self, group_by='current_status'):
        raise NotImplementedError

    def count_jobs_per_time_period(self, job_state,
                                   time_period=TIME_PERIODS.hourly,
                                   count_field_name=None,
                                   distinct=False):
        raise NotImplementedError

    def job_exists(self, job_id):
        raise NotImplementedError

    def claim_job(self, job_id):
        """Claim a job, return True if the job was claimed"""
        return self._update_job(job_id, {self.CLAIMED: True})

    def unclaim_job(self, job_id):
        """Unclaim a job"""
        self._update_job(job_id, {self.CLAIMED: False})

    def update_job(self, job_id, **data):
        self._verify(data)
        return self._update_job(job_id, data)

    def _update_job(self, job_id, data):
        """
        Args:
           job_id (str): The job id.
           data (dict): Data to update the job object with.
        Returns:
           bool: True if something changed.
        """
        raise NotImplementedError

    def _insert_job(self, job_id, job):
        raise NotImplementedError

    def _verify(self, data):
        # TODO
        pass

    def close(self):
        raise NotImplementedError

    def drop(self):
        raise NotImplementedError


class InMemoryJobDatabase(BaseJobDatabaseAPI):
    """Simple dict based database for testing"""

    DATABASES = {}

    def __init__(self, project):
        super(InMemoryJobDatabase, self).__init__(project)
        if project not in InMemoryJobDatabase.DATABASES:
            InMemoryJobDatabase.DATABASES[project] = OrderedDict()
        self.db = InMemoryJobDatabase.DATABASES[project]

    def close(self):
        pass

    def get_jobs(self, job_id=None, match=None, fields=None):
        if job_id:
            job = self.db.get(job_id)
            jobs = [job] if job else []
        else:
            jobs = self.db.values()
        if match:
            def matches(data, tomatch):
                for k, v in tomatch.items():
                    if data.get(k) != v:
                        return False
                return True
            jobs = [job_ for job_ in jobs if matches(job_, match)]
        for job in jobs:
            if fields:
                job = {k: v for k, v in job.items() if k in fields}
            yield job

    def _update_job(self, job_id, data):
        if not self.job_exists(job_id):
            raise DBError('Job does not exist')
        changed = any([self.db[job_id].get(k) != v for k, v in data.items()])
        self.db[job_id].update(data)
        return changed

    def _insert_job(self, job_id, job_data):
        if self.job_exists(job_id):
            raise DBError('Job already exists')
        job_data['claimed'] = False
        job_data['current_status'] = JOB_STATES.available
        job_data['added_timestamp'] = datetime.utcnow()

        self.db[job_id] = job_data
        return job_id

    def job_exists(self, job_id):
        return job_id in self.db

    def drop(self):
        InMemoryJobDatabase.DATABASES[self.project] = OrderedDict()
        self.db = InMemoryJobDatabase.DATABASES[self.project]
