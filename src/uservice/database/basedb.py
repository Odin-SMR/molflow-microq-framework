from collections import OrderedDict


class DBError(Exception):
    pass


class BaseDatabaseAPI(object):
    """Base API to a database.

    Inherit and implement:

    * get_jobs
    * job_exists
    * _update_job
    * _insert_job
    """
    # TODO: Put this in a job model
    CLAIMED = 'claimed'
    CLAIMED_TIMESTAMP = 'claimed_timestamp'

    def __init__(self, project):
        self.project = project

    def insert_job(self, job_id, job_data):
        self._verify(job_data)
        return self._insert_job(job_id, job_data)

    def get_jobs(self, job_id=None, match=None, fields=None):
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

    def _insert_job(self, job):
        raise NotImplementedError

    def _verify(self, data):
        # TODO
        pass


class InMemoryDatabase(BaseDatabaseAPI):
    """Simple dict based database for testing"""
    def __init__(self, project):
        super(InMemoryDatabase, self).__init__(project)
        self.db = OrderedDict()

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

        self.db[job_id] = job_data
        return job_id

    def job_exists(self, job_id):
        return job_id in self.db
