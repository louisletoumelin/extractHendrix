from datetime import timedelta, time, datetime, date
import itertools
from pprint import pprint
import os

from cen.layout.nodes import S2MTaskMixIn
from vortex import toolbox

from extracthendrix.core import get_model_description


available_combinations = [
    dict(kind=['meteo', 'pro'],
        runtime= [time(hour=3)],
        previ=[False], 
        member=range(36), 
        begin=[timedelta(days=-i) for i in range(2,5)], 
        end=[timedelta(days=-i) for i in range(1,4)]
        ),
    dict(kind=['meteo', 'pro'], 
        runtime= [time(hour=3)], 
        previ=[True], 
        member=range(37), 
        begin=[timedelta(days=-1)],
        end=[timedelta(days=4)]
        ),
    dict(kind=['meteo', 'pro'], 
        runtime=[time(hour=6)], 
        previ=[False], 
        member=range(37), 
        begin=[timedelta(days=-1)], 
        end=[timedelta(days=0)]
        ),
    dict(kind=['pro'], 
        runtime=[time(hour=6)], 
        previ=[True], 
        member=range(37),
        begin=[timedelta(days=0)],
        end=[timedelta(days=4)]
        ),
    dict(kind=['pro'],
        runtime=[time(hour=9)], 
        previ=[True],
        member=range(36),
        begin=[timedelta(days=0)],
        end=[timedelta(days=4)]
        ),
    dict(kind=['meteo', 'pro'],
        runtime=[time(hour=9)],
        previ=[False],
        member=range(36),
        begin=[timedelta(days=-1)],
        end=[timedelta(days=0)]
        )
    ]
available_single_combinations = []
for combination in available_combinations:
    for (kind, runtime, previ, member) in itertools.product(combination['kind'], combination['runtime'], combination['previ'], combination['member']):
        comb_copy = dict(**combination)
        comb_copy.update(dict(kind=kind, runtime=runtime, previ=previ, member=member))
        available_single_combinations.append(comb_copy)


class RunDoesntExistException(Exception):
    pass


class MoreThanOneRunMatchException(Exception):
    pass


class Config(object):
    pass


class S2MExtractor(S2MTaskMixIn):
    def __init__(self, folder='tmp', kind=None, geometry=None, runtime=None, previ=None, member=None): 
        self.kind = kind
        self.runtime = runtime
        self.previ = previ
        self.member = member

        if not os.path.isdir(folder):
            os.mkdir(folder)
        self.folder = folder
        self.conf = Config()
        if kind=='pro':
            self.resource_description = get_model_description('S2M_PRO')
        if kind=='meteo':
            self.resource_description = get_model_description('S2M_FORCING')
        if self.previ:
            for description in self.resource_description:
                description['cutoff']='production'
        else:
            for description in self.resource_description:
                description['cutoff']='assimilation'
        for description in self.resource_description:
            description['geometry']=geometry
        self.conf.__dict__ = self.resource_description[0]

    def get_resource_description(self):
        return self.resource_description

    def get_available_runs(self):
        filter_ = dict([(param, value) for param, value in {'kind':self.kind, 'runtime':self.runtime, 'previ':self.previ, 'member':self.member}.items() if value is not None])
        return [combination for combination in available_single_combinations if all([combination[arg] == value for arg, value in filter_.items()])]

    def get_params_for_run(self):
        run = self.get_available_runs()
        if len(run) == 0:
            raise RunDoesntExistException()
        if len(run) > 1:
            raise MoreThanOneRunMatchException()
        return run[0]

    def get_dates_for_run(self, date):
        run = self.get_params_for_run()
        rundatetime = datetime.combine(date=date, time=self.runtime)
        datebegin = [rundatetime.replace(hour=6) + delta for delta in run['begin']]
        dateend = [rundatetime.replace(hour=6) + delta for delta in run['end']]
        return datebegin, dateend

    def get_netcdf(self, date):
        resource_description = dict(**self.resource_description[0])
        dates_begin, dates_end = self.get_dates_for_run(date)
        rundate = datetime.combine(date=date, time=self.runtime)
        anaprevi = 'previ' if self.previ else 'analyse'
        filepaths = []
        for datebegin, dateend in zip(dates_begin, dates_end):
            rundatestr, beginstr, endstr = [date_.strftime("%Y%m%d_%Hh") for date_ in [rundate, datebegin, dateend]] 
            filepath = os.path.join(self.folder,'%s-%s-member%s-run%s_%s_%s.nc'%(self.kind, anaprevi, self.member, rundatestr,beginstr, endstr))
            resource_description.update(
                    local=filepath,
                    date= rundate,
                    datebegin=datebegin,
                    dateend=dateend,
                    member=self.member,
                    previ=self.previ
                    )
            tb = toolbox.input(**resource_description)
            tb[0].get()
            filepaths.append(filepath)
        return filepaths


def get_s2m_netcdf(date=None, kind=None, runtime=None, previ=None, member=None):
    extractor = S2MExtractor(kind, runtime, previ, member)
    extractor.get_netcdf(date)


