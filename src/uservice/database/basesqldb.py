from os import environ

from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

_engine = _db_session = None


class SqlDB:

    def __init__(self, model):
        global _engine, _db_session
        if not _engine:
            dburl = environ['USERVICE_DATABASE_URI']
            _engine = create_engine(
                dburl,
                convert_unicode=True,
                pool_size=30,
                max_overflow=0,
                pool_timeout=180,
                pool_recycle=600
            )
            _db_session = scoped_session(
                sessionmaker(autocommit=True,
                             autoflush=True,
                             bind=_engine))
        self.engine = _engine
        self.session = _db_session
        self.model = model
        self.model.query = _db_session.query_property()
        self.model.__table__.create(_db_session.bind, checkfirst=True)
