from sqlalchemy import Table, Column, Integer, Float, Text, String, MetaData
import migrate.changeset
from migrate.changeset.constraint import PrimaryKeyConstraint

# Import of changeset adds drop and alter methods to Column etc.
# Suppress unused import warning:
migrate.changeset


def upgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine, reflect=True)
    projects = Table('projects', meta, autoload=True)

    print("Upgrade 'projects'")

    pkey = PrimaryKeyConstraint('name', table=projects)
    pkey.drop()

    projects.c.name.alter(name='id')
    meta = MetaData(bind=migrate_engine, reflect=True)
    projects = Table('projects', meta, autoload=True)
    pkey = PrimaryKeyConstraint('id', table=projects)
    pkey.create()

    projects.c.deadline_timestamp.alter(name='deadline')

    Column('nr_added', Integer, default=0).create(
        projects, populate_default=True)
    Column('nr_claimed', Integer, default=0).create(
        projects, populate_default=True)
    Column('nr_finished', Integer, default=0).create(
        projects, populate_default=True)
    Column('nr_failed', Integer, default=0).create(
        projects, populate_default=True)
    Column('processing_time', Float, default=0).create(
        projects, populate_default=True)
    Column('processing_image_url', String(512)).create(projects)
    Column('name', String(128)).create(projects)
    Column('environment', Text).create(projects)

    for table_name in meta.tables.keys():
        if table_name.startswith('jobs_'):
            print("Upgrade %r" % table_name)
            jobs = Table(table_name, meta, autoload=True)
            Column('processing_time', Float, default=0).create(
                jobs, populate_default=True)
            Column('view_result_url', String(512)).create(jobs)


def downgrade(migrate_engine):
    meta = MetaData(bind=migrate_engine, reflect=True)
    projects = Table('projects', meta, autoload=True)

    print("Downgrade 'projects'")

    projects.c.nr_added.drop()
    projects.c.nr_claimed.drop()
    projects.c.nr_finished.drop()
    projects.c.nr_failed.drop()
    projects.c.processing_time.drop()
    projects.c.processing_image_url.drop()
    projects.c.name.drop()
    projects.c.environment.drop()

    pkey = PrimaryKeyConstraint('id', table=projects)
    pkey.drop()

    projects.c.id.alter(name='name')
    meta = MetaData(bind=migrate_engine, reflect=True)
    projects = Table('projects', meta, autoload=True)
    pkey = PrimaryKeyConstraint('name', table=projects)
    pkey.create()

    projects.c.deadline.alter(name='deadline_timestamp')

    for table_name in meta.tables.keys():
        if table_name.startswith('jobs_'):
            print("Downgrade %r" % table_name)
            jobs = Table(table_name, meta, autoload=True)
            jobs.c.processing_time.drop()
            jobs.c.view_result_url.drop()
