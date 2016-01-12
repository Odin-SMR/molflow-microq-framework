"""A simple datamodel implementation"""

from flask import Flask
from odinapi.views.views import DateInfo, DateBackendInfo
from odinapi.views.views_cached import DateInfoCached, PeriodInfoCached
from odinapi.views.statistics import (FreqmodeStatistics,
                                      TimelineFreqmodeStatistics)
from odinapi.views.views import ScanSpec, FreqmodeInfo
from odinapi.views.smr_site import (ViewIndex, ViewScanSpec, ViewLevel1,
                                    ViewLevel1Stats,)
from odinapi.views.smr_site import ViewFreqmodeInfoPlot
from odinapi.views.data_info import FileInfo
from odinapi.views.views import ScanPTZ, ScanAPR
from os import environ


class Odin(Flask):
    """The main app running the odin site"""
    def __init__(self, name):
        super(Odin, self).__init__(name)
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/',
            view_func=DateInfoCached.as_view('freqmodeinfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/period_info/<int:year>/<int:month>/'
            '<int:day>/',
            view_func=PeriodInfoCached.as_view('periodinfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_raw/<date>/',
            view_func=DateInfo.as_view('freqmoderaw')
            )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/',
            view_func=DateBackendInfo.as_view('backendinfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/freqmode_info/<date>/<backend>/'
            '<int:freqmode>/',
            view_func=FreqmodeInfo.as_view('scaninfo')
            )
        self.add_url_rule(
            '/rest_api/<version>/scan/<backend>/<int:freqmode>/<int:scanno>/',
            view_func=ScanSpec.as_view('scan')
            )
        self.add_url_rule(
            '/rest_api/<version>/file_info/',
            view_func=FileInfo.as_view('file_info')
            )
        self.add_url_rule(
            '/rest_api/<version>/ptz/<date>/<backend>/<int:freqmode>/'
            '<int:scanno>/',
            view_func=ScanPTZ.as_view('ptz')
            )
        self.add_url_rule(
            '/rest_api/<version>/apriori/<species>/<date>/<backend>/'
            '<int:freqmode>/<int:scanno>/',
            view_func=ScanAPR.as_view('apriori')
            )
        self.add_url_rule(
            '/',
            view_func=ViewIndex.as_view('index')
            )
        self.add_url_rule(
            '/level1',
            view_func=ViewLevel1.as_view('level1')
            )
        self.add_url_rule(
            '/level1statistics',
            view_func=ViewLevel1Stats.as_view('level1statistics')
            )
        self.add_url_rule(
            '/level2',
            view_func=ViewLevel1.as_view('level2')
            )
        self.add_url_rule(
            '/browse/<backend>/<int:freqmode>/<int:scanno>/',
            view_func=ViewScanSpec.as_view('viewscan')
            )
        self.add_url_rule(
            '/plot/<date>/<backend>/<int:freqmode>',
            view_func=ViewFreqmodeInfoPlot.as_view('plotscans')
            )
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/',
            view_func=FreqmodeStatistics.as_view('freqmodestatistics')
            )
        self.add_url_rule(
            '/rest_api/<version>/statistics/freqmode/timeline/',
            view_func=TimelineFreqmodeStatistics.as_view('timefmstatistics')
            )


def main():
    """Default function"""
    app = Odin(__name__)
    app.run(
        host='0.0.0.0',
        debug='ODIN_API_PRODUCTION' not in environ,
        threaded=True
        )

if __name__ == "__main__":
    main()
