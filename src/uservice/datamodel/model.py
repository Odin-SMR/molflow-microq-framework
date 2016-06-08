from os import walk
from os.path import join as path_join
from os.path import relpath, getctime

from re import compile
from datetime import datetime
from sqlalchemy import (Column, DateTime, String, Integer, Float,
                        Numeric, ForeignKeyConstraint)  # , ForeignKey)
from sqlalchemy.orm import relationship  # , backref
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker


Base = declarative_base()


class Level1(Base):
    __tablename__ = 'level1'
    orbit = Column(Integer, primary_key=True)
    backend = Column(String(7), primary_key=True)
    calversion = Column(Numeric(2, 1), primary_key=True)
    hdffile = relationship('HdfFile')
    logfile = relationship('LogFile')
    scans = relationship('Scan')


class HdfFile(Base):
    __tablename__ = 'l1hdffiles'
    __table_args__ = (
        ForeignKeyConstraint(
            ['orbit', 'backend', 'calversion'],
            ['level1.orbit', 'level1.backend', 'level1.calversion']
        ),
    )

    orbit = Column(Integer, primary_key=True)
    backend = Column(String(7), primary_key=True)
    calversion = Column(Numeric(2, 1), primary_key=True)
    filedate = Column(DateTime)
    update = Column(DateTime)


class LogFile(Base):
    __tablename__ = 'l1logfiles'
    __table_args__ = (
        ForeignKeyConstraint(
            ['orbit', 'backend', 'calversion'],
            ['level1.orbit', 'level1.backend', 'level1.calversion']
        ),
    )
    orbit = Column(Integer, primary_key=True)
    backend = Column(String(7), primary_key=True)
    calversion = Column(Numeric(2, 1), primary_key=True)
    filedate = Column(DateTime)
    update = Column(DateTime)


class Scan(Base):
    __tablename__ = 'scans'
    __table_args__ = (
        ForeignKeyConstraint(
            ['orbit', 'backend', 'calversion'],
            ['level1.orbit', 'level1.backend', 'level1.calversion']
        ),
    )
    orbit = Column(Integer, primary_key=True)
    backend = Column(String(7), primary_key=True)
    calversion = Column(Numeric(2, 1), primary_key=True)
    mjd = Column(Float)
    stw = Column(Integer)
    level1 = relationship("Level1", back_populates="scans")


class FileServer(object):
    """Handles Odin files in a directory"""
    def __init__(self, path):
        self.path = path

    def add_files(self):
        """A list of all files in the storage"""
        file_list = []
        for dirpath, _, fnames in walk(self.path):
            for filename in fnames:
                file_list.append(path_join(dirpath, filename))
        return file_list


class Level1Inserter(object):
    def __init__(self, level1b_dir):
        engine = create_engine('mysql://odinuser:IK)Bag4F@mysqlhost/smr')
        session = sessionmaker(bind=engine)
        self.ses = session()
        self.pattern = compile(
            "^(?P<calversion>[\d]+\.[\d]+).*"
            "O(?P<backend>[ABCD])"
            "1B(?P<orbit>[\w]{4,5})"
            "\.(?P<type>[\w]{3})"
            "(?:$|\.gz$)"
            )
        file_storage = FileServer(level1b_dir)
        file_list = file_storage.add_files()
        for file in file_list:
            match = self.pattern.search(relpath(file, level1b_dir))
            if match is None:
                continue
            matchdict = match.groupdict()
            backend = matchdict['backend']
            file_type = matchdict['type']
            calversion = matchdict['calversion']
            orbit = eval("0x" + matchdict['orbit'])
            logfile = []
            hdffile = []
            if file_type == "HDF":
                hdffile = [HdfFile(
                    filedate=datetime.fromtimestamp(getctime(file)),
                    update=datetime.now()
                    )]
            if file_type == "LOG":
                logfile = [LogFile(
                    filedate=datetime.fromtimestamp(getctime(file)),
                    update=datetime.now())]
            level1 = self.ses.query(Level1).filter_by(
                orbit=orbit,
                calversion=calversion,
                backend=backend,
                ).first()
            if level1:
                if file_type == "HDF":
                    level1.hdffile = hdffile
                if file_type == "LOG":
                    level1.logfile = logfile
            else:
                self.ses.add(
                    Level1(
                        orbit=orbit,
                        calversion=calversion,
                        backend=backend,
                        logfile=logfile,
                        hdffile=hdffile,
                        )
                    )
        self.ses.commit()


def main():
    """IT all starts here"""
    level1b_dir = '/odin/smr/Data/level1b/'
    l1b_inserter = Level1Inserter(level1b_dir)


if __name__ == '__main__':
    main()
