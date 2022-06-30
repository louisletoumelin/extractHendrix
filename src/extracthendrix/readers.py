import logging
from datetime import timedelta, time, datetime, date
import itertools
import os
import configparser
import pkg_resources

import ftplib
from ftplib import FTP
from netrc import netrc

from cen.layout.nodes import S2MTaskMixIn
from vortex import toolbox
import xarray as xr
import usevortex

# from extracthendrix.core import get_all_resource_descriptions, CanNotReadEpygramField, CanNotAccessVortexResource
from extracthendrix.exceptions import RunDoesntExistException, MoreThanOneRunMatchException, GeometryIsMissingException

logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)


def return_path_if_exists_on_hendrix(ftp, path_resource):
    file_name = path_resource.split('/')[-1]
    path_folder = os.path.dirname(path_resource)
    # Check that the file exist at the specified path
    ftp.cwd(path_folder)
    listing_folder = ftp.nlst()
    full_file_name = next(x for x in listing_folder if file_name in x)
    return os.path.join(path_folder, full_file_name)


class NativeFileUnfetchedException(Exception):
    pass


def model_ini_to_dict(model_name):
    """Converts config/models.ini into a dictionary"""
    config = configparser.ConfigParser()
    models_path = pkg_resources.resource_filename('extracthendrix.config', 'models.ini')
    config.read(models_path)
    dict_model = dict(config[model_name])
    return dict_model


#  old get_model_description
def get_all_resource_descriptions(model_name, member=None):
    """

    Get vortex descriptions of a model.

    If a key of the resource_description changes with time (e.g. namespace), this will result in several
    resource descriptions

    :param model_name: Model name.
    :param member: Member number
    :return: List of model descriptions
    """

    dict_model = model_ini_to_dict(model_name)

    for key in dict_model.keys():
        dict_model[key] = dict_model[key].split(',')

    if member:
        dict_model['member'] = [member]

    keys, values = zip(*dict_model.items())
    list_dict_models = [dict(zip(keys, v)) for v in itertools.product(*values)]

    return list_dict_models


class HendrixFileReader:
    """This class deals with file on Hendrix."""

    def file_in_cache_path(self, date, term):
        """Not used"""
        filepath = self.folderLayout._cache_
        filename = self.get_file_hash(date, term)
        return os.path.join(filepath, filename)

    # old native_file_path
    def get_path_file_in_native(self, date, term):
        """
        Return path of the file in _native_ for the corresponding date/term combination.

        :param date: Run time.
        :param term: Forecast lead time.
        :return: Path of the file.
        """
        filepath = self.folderLayout._native_
        filename = self.get_file_hash(date, term)
        filename = f"{filename}.{self.fmt}"
        return os.path.join(filepath, filename)


available_combinations = [
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         run=[time(hour=3)],
         previ=[False],
         member=range(37),
         timerange=zip([timedelta(days=-i) for i in range(2, 5)], [timedelta(days=-i) for i in range(1, 4)])),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         run=[time(hour=3)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=4))]
         ),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         run=[time(hour=6)],
         previ=[False],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=0))]
         ),
    dict(model=['S2M_PRO'],
         run=[time(hour=6)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=0), timedelta(days=4))]
         ),
    dict(model=['S2M_PRO'],
         run=[time(hour=9)],
         previ=[True],
         member=range(37),
         timerange=[(timedelta(days=0), timedelta(days=4))]
         ),
    dict(model=['S2M_FORCING', 'S2M_PRO'],
         run=[time(hour=9)],
         previ=[False],
         member=range(37),
         timerange=[(timedelta(days=-1), timedelta(days=0))]
         )
]
available_single_combinations = []
for combination in available_combinations:
    for (model, run, previ, member, timerange) in itertools.product(
        combination['model'],
        combination['run'],
        combination['previ'],
        combination['member'],
        combination['timerange']
    ):
        for geometry in ('alp', 'pyr', 'cor', 'postes'):
            available_single_combinations.append(
                dict(
                    model=model,
                    run=run,
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
            if key not in ('model', 'run', 'previ', 'member', 'geometry'):
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
        FIXME: pas lumineux à soigner...
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
        """FIXME: pas totalement lumineux
        """
        run = self.get_params_for_run(term=term)
        rundatetime = datetime.combine(
            date=date, time=self.s2m_args['run'])
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
        del params['run']
        return params


class S2MHendrixReader(HendrixFileReader):
    def __init__(self, native_files_folder=None, cache_folder=None, s2mArgHelper=S2MArgHelper()):
        self.helper = s2mArgHelper
        self.native_files_folder = native_files_folder
        self.cache_folder = cache_folder

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

    def get_native_file(self, date, term):
        params4request = self.helper.get_params_for_run_with_date(date, term)
        filepath = os.path.join(
            self.native_files_folder,
            self.get_file_hash(date, term))
        if os.path.isfile(filepath):
            # comme on a plusieurs échéances dans le même fichier, on peut
            # demander plusieurs fois le même, on s'assure ici que ça n'arrive
            # pas
            return filepath
        witch = VortexWitchCraftReader(
            filepath=filepath,
            **params4request)
        witch.get_netcdf()
        return filepath

    def read_cache(self, date, term, variable_name):
        """FIXME: on a en gros l'idée de la lecture, homogéneïser avec les fonctions 
        équivalentes pour les fichiers AROME et ARPEGE quand on aura mis le nez
        dans ces derniers
        FIXME: gestion du temps (ici decode_times=False forcé par la présence de deux
        dimensions time pour les fichiers de la chaîne, il faudra recréer la dimension
        temps
        """
        data = xr.open_dataset(self.file_in_cache_path(
            date, term), decode_times=False)
        return data[variable_name].isel(time=term)


class Config(object):
    pass


class VortexWitchCraftReader(S2MTaskMixIn):
    def __init__(self, filepath=None, model=None, geometry=None, previ=None, member=None, rundatetime=None, datebegin=None, dateend=None):
        self.conf = Config()
        self.resource_description = get_all_resource_descriptions(model)[0]
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


class AromeHendrixReader(HendrixFileReader):
    """This class helps to extract AROME and ARPEGE files on Hendrix"""
    def __init__(self,
                 folderLayout=None,
                 model=None,
                 member=None,
                 getmode='get',
                 ):
        """
        :param folderLayout: instance of the class FolderLayout. Gives information about the working directory.
        :param model: Model name
        :param member: Member number
        :param getmode: getmode (for testing purpose)
        """
        self.folderLayout = folderLayout
        self.getmode = getmode
        self.model_name = model
        self.member = member
        # List with all model descriptions possibles (including alternative parameters such as "namespace")
        self.list_resource_descriptions = get_all_resource_descriptions(model, member) # old list_model_descriptions
        self.fmt = self.list_resource_descriptions[0]['nativefmt']  # FA or GRIB

    def get_file_hash(self, date, term):
        """
        Return file hash (i.e. part of the filename).

        :param date: Run time.
        :param term: Forecast lead time.
        :return: hash (str).
        """
        date = date.strftime("%Y%m%d%H")
        memberstr = f"_mb{self.member:03d}" if self.member else ""
        term = f"_term{term}" if term is not None else ""
        hash_ = f"{self.model_name}_run_{date}{term}{memberstr}"
        return hash_

    def get_file_list(self, dateandtermiterator):
        ftp = FTP('hendrix.meteo.fr')
        credentials = netrc().authenticators('hendrix')
        if credentials is None:
            credentials = netrc().authenticators('hendrix.meteo.fr')
        ftp.login(credentials[0], credentials[2])
        filelist = []
        notfound = []
        for date_, term in dateandtermiterator:
            resdesc = self._get_vortex_resource_description(date_, term)
            potential_locations = [
                usevortex.get_resources(
                    getmode='locate', **resource_description
                )
                for resource_description in resdesc]
            for resource in potential_locations:
                try:
                    filelist.append(return_path_if_exists_on_hendrix(ftp, resource[0].split(':')[1]))
                except (ftplib.error_perm, StopIteration):
                    notfound.append(resource[0])
        ftp.close()
        return filelist, notfound

    def _get_vortex_resource_description(self, date, term):
        """
        Prepare resource descriptions for downloading data with Vortex on Hendrix.

        :param date: Run time
        :param term: Forecast lead time
        :return: List of resource descriptions.
        """
        resource_descriptions = [dict(
            **model_description,
            date=date,
            term=term
        ) for model_description in self.list_resource_descriptions]

        if self.getmode == 'get':
            for resource in resource_descriptions:
                resource['local'] = os.path.join(self.get_path_file_in_native(date, term))

        return resource_descriptions

    def get_native_file(self, date, term, autofetch=True):
        """
        Download files on Hendrix if necessary.

        :param date: run
        :param term: forecast lead time
        :param autofetch:
        :return: filepath, str
        """
        filepath = self.get_path_file_in_native(date, term)

        # If file is downloaded, we skip
        file_already_downloaded = os.path.isfile(filepath)
        if file_already_downloaded:
            return filepath

        # Test purpose
        if not autofetch:
            raise NativeFileUnfetchedException()

        # Try every combinations od resource description possible
        # resource description = model description in Vortex
        last_exception = None
        for resource_description in self._get_vortex_resource_description(date, term):
            try:
                r = usevortex.get_resources(getmode='epygram', **resource_description)
                return filepath
            except Exception as e:
                last_exception = e

        # If not combination works, raise the error
        raise last_exception
