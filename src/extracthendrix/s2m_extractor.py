from datetime import timedelta, time, datetime, date
import itertools
from pprint import pprint
import os

from cen.layout.nodes import S2MTaskMixIn
from vortex import toolbox

from extracthendrix.core import get_model_description


class RunDoesntExistException(Exception):
    pass


class MoreThanOneRunMatchException(Exception):
    pass


class GeometryIsMissingException(Exception):
    pass


class Config(object):
    pass


available_combinations = [
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         runtime=[time(hour=3)],
         previ=[False],
         member=range(37),
         timerange=zip([timedelta(days=-i) for i in range(2, 5)], [timedelta(days=-i) for i in range(1, 4)])),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         runtime=[time(hour=3)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=4))]
         ),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         runtime=[time(hour=6)],
         previ=[False],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=0))]
         ),
    dict(model=['S2M_PRO'],
         runtime=[time(hour=6)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=0), timedelta(days=4))]
         ),
    dict(model=['S2M_PRO'],
         runtime=[time(hour=9)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=0), timedelta(days=4))]
         ),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         runtime=[time(hour=9)],
         previ=[False],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=0))]
         )
]
available_single_combinations = []
for combination in available_combinations:
    for (model, runtime, previ, member, timerange) in itertools.product(
        combination['model'],
        combination['runtime'],
        combination['previ'],
        combination['member'],
        combination['timerange']
    ):
        for geometry in ('alp', 'pyr', 'cor', 'postes'):
            available_single_combinations.append(
                dict(
                    model=model,
                    runtime=runtime,
                    previ=previ,
                    member=member,
                    geometry=geometry,
                    begin=timerange[0],
                    end=timerange[1]
                )
            )


class S2MArgHelper:
    def __init__(self, **kwargs):
        self.checkargs(kwargs)
        self.s2m_args = kwargs

    def checkargs(self, kwargs):
        for key in kwargs.keys():
            if key not in ('model', 'runtime', 'previ', 'member', 'geometry'):
                raise ValueError("Clé illégale pour les arguments de S2M")

    def add_arg(self, **kwargs):
        self.checkargs(kwargs)
        self.s2m_args.update(kwargs)

    def get_available_runs(self, term=None):
        available_runs_any_terms =\
            [
                combination for combination in
                available_single_combinations
                if all(
                    [combination[arg] == value
                     for arg, value in self.s2m_args.items()]
                )
            ]
        if term is None:
            return available_runs_any_terms
        available_runs = [
            run for run in available_runs_any_terms
            if (run['begin'] < timedelta(hours=term) <= run['end'])
        ]
        return available_runs

    def get_params_for_run(self, term=None):
        """
        term: échéance en nombre entier - éventuellement négatif - d'heures
        """
        if 'geometry' not in self.s2m_args:
            raise GeometryIsMissingException()
        run = self.get_available_runs(term=term)
        if len(run) == 0:
            raise RunDoesntExistException()
        if len(run) > 1:
            raise MoreThanOneRunMatchException()
        return dict(run[0], geometry=self.s2m_args['geometry'])

    def get_params_for_run_with_date(self, date, term):
        run = self.get_params_for_run(term=term)
        rundatetime = datetime.combine(
            date=date, time=self.s2m_args['runtime'])
        datebegin = rundatetime.replace(hour=6) + run['begin']
        dateend = rundatetime.replace(hour=6) + run['end']
        params = dict(
            run,
            rundatetime=rundatetime,
            datebegin=datebegin,
            dateend=dateend
        )
        del params['end']
        del params['begin']
        del params['runtime']
        return params


class S2MExtractor:
    def __init__(self, folder='tmp', s2mArgHelper=S2MArgHelper()):
        self.helper = s2mArgHelper
        if not os.path.isdir(folder):
            os.mkdir(folder)
        self.folder = folder

    def get_file_hash(self, date, term):
        params4request = self.helper.get_params_for_run_with_date(date, term)
        anaprevi = 'previ' if params4request['previ'] else 'analyse'
        rundatestr, beginstr, endstr = [
            rundate.strftime("%Y%m%d_%Hh")
            for rundate in [
                params4request['rundatetime'],
                params4request['datebegin'],
                params4request['dateend']
            ]
        ]
        hash = '%s-%s-%s-member%s-run%s_%s_%s.nc' % (
            params4request['model'],
            anaprevi,
            params4request['geometry'],
            params4request['member'],
            rundatestr,
            beginstr,
            endstr)
        return hash

    def get_netcdf(self, date, term):
        params4request = self.helper.get_params_for_run_with_date(date, term)
        filename = self.get_file_hash(date, term)
        filepath = os.path.join(self.folder, filename),
        witch = VortexWitchCraftExtractor(filepath=filepath, **params4request)
        witch.get_netcdf()
        return filepath


class VortexWitchCraftExtractor(S2MTaskMixIn):
    def __init__(self, filepath=None, model=None, geometry=None, previ=None, member=None, rundatetime=None, datebegin=None, dateend=None):
        self.conf = Config()
        self.resource_description = get_model_description(model)[0]
        self.resource_description.update(
            cutoff='production' if previ else 'assimilation',
            geometry=geometry,
            local=filepath,
            date=rundatetime,
            datebegin=datebegin,
            dateend=dateend,
            member=member,
            previ=previ
        )
        self.conf.__dict__ = self.resource_description

    def get_netcdf(self):
        tb = toolbox.input(**self.resource_description)
        tb[0].get()
