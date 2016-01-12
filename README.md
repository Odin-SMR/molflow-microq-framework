# microService framework for data processing


## Intent
A framework for distributing jobs to workers.

The intent is to use worker microservices that ask a server for jobs. All
communication will be over REST with some kind of authentication for those
calls that would benefit from it. Some calls are also made for humans to use
for getting statuses and performing administration.


## REST hierarchy

### /rest/jobs/

URL for getting a (human readable?) list of jobs with id and statuses:
- available
- claimed (message, e.g. percent done, time claimed, claimant id etc.)
- done (message, e.g. delivery time, deliverer id etc.)

### /rest/jobs/fetch/

URL for getting the next job in the "queue" from the server.  No authentication
required.

Result is URL for claiming, getting data, reporting status etc.


### /rest/jobs/<id>/

URL for getting the status of job <id>, also returns URLs for getting data to
process, claiming etc. as applicable. Probably not human readable.


### /rest/jobs/<id>/status/

URL for getting status of job <id>, also returns URLs for getting data to
process, claiming etc. as applicable. Human readable.

### /rest/jobs/<id>/status/update/

URL for updating status of job <id>. Some sort of authentication might be
implemeted, such as only allowing claims where a proper key is supplied via
e.g. ?key=.

An authentic call makes the Server updates status of job and notes the time.
Old status moved to log? New status can be supplied e.g. via ?status=.

Result is some sort of status confirmation reporting success or failure.


### /rest/jobs/<id>/data/
URL for getting the data (or URLs to data) needed to start processing.


### /rest/jobs/<id>/claim/
URL for claiming a job. Some sort of authentication might be implemeted, such
as only allowing claims where a proper key is supplied via e.g. ?key=.

An authentic call to claim will cause the Server to relabel the job as claimed,
prohibiting other Workers from claiming it. Time of claiming and id of claimant
(Worker) will be noted, in order to identify problems and unlocking jobs where
the Worker is taking to long to deliver the job.

Result is some sort of status confirmation (and URL to data..?) if the job can
be claimed, otherwise some negative confirmation/http status code.


### /rest/jobs/<id>/lock/
URL for locking a job, e.g. when claimed. Some sort of authentication might be
implemeted, such as only allowing locking where a proper key is supplied via
e.g. ?key=.

An authentic call tells the server to update the status to Locked.

Result is some sort of status confirmation reporting success or failure.


### /rest/jobs/<id>/unlock/
URL for unlocking a job, e.g. when the Worker that claimed it is suspected to
have crashed. Some sort of authentication might be implemeted, such as only
allowing claims where a proper key is supplied via e.g. ?key=.

An authentic should clear claimant id etc, but some info may be kept in a log.

Result is some sort of status confirmation reporting success or failure.


### /rest/jobs/<id>/deliver/
URL for delivering a job, e.g. when claimed. Some sort of authentication might
be implemeted, such as only allowing claims where a proper key is supplied via
e.g. ?key=.

An authentic call should make the Server take the delivered data, put it where
it belongs, update the database, update the status of the job, and return a
confirmation to the Worker.

Result is some sort of status confirmation reporting success or failure.  If
the result is not Success, the Worker should try again later. If the job has
already been delivered by another Worker, the result should still say success
as a contingency, so that the Worker can move on and claim a new job.
