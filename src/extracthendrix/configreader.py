from datetime import datetime, time, timedelta
import functools
import time as timeutils
import os

from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, get_model_names
from extracthendrix.readers import AromeHendrixReader
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_script_stopped_email, send_success_email


def onRetryDefault(exception_raised, time_fail, nb_attempts, time_to_next_retry):
    print(exception_raised, time_fail, nb_attempts, time_to_next_retry)


def onFailureDefault(exception_raised, current_time):
    print(exception_raised, current_time)


def retry_and_finally_raise(
        onRetry=onRetryDefault,
        onFailure=onFailureDefault,
        time_retries=[]
):  #[timedelta(hours=n) for n in [0.5, 1, 2, 3, 6]]
    """
    Args:
    cache_method (:obj:`method`): La méthode à exécuter
    config_user (:obj:`extractHendrix.configreader.ConfigReader`): la configuration de l'utilisateur
    time_retries (:obj:`list` of :obj:`datetime.timedelta`): les intervalles de temps au bout desquels relancer la fonction en cas d'échec
    """
    def decorator_retry(func):
        @functools.wraps(func)
        def wrapper_retry(*args):
            if len(time_retries) == 0:
                return func(*args)
            for numretry, delta in enumerate(time_retries):
                try:
                    return func(*args)
                except Exception as E:
                    onRetry(E, timeutils.asctime(), numretry+1, delta)
                    timeutils.sleep(delta.total_seconds())
            # last attempt before giving up
            try:
                return func(*args)
            except Exception as E:
                onFailure(E, timeutils.asctime())
                raise E
        return wrapper_retry
    return decorator_retry


class Grouper:
    """
    Handles grouping of downladed files (daily, monthly...etc)

    Takes care of grouping file according to the user demands, whenever the files are downloaded.
    This is better than concatenating files at the end because of lower file redundance and memory footprint.

    :param groupby: time period to group by outputs files
    :type groupby: str
    """
    def __init__(self, groupby):
        self.groupby = groupby

    def filetag(self, run, term):
        """
        Gives a tag (str) of the date for which the extraction is valid.
        e.g. "2020-09-5"

        :param run: date of the run
        :type run: datetime
        :param term: hour of the term
        :type term: int
        :return: str
        """
        if self.groupby == ('timeseries', 'daily'):
            return validity_date(run, term).strftime("%Y_%m_%d")
        if self.groupby == ('timeseries', 'monthly'):
            return validity_date(run, term).strftime("%Y_%m")
        if self.groupby == ('forecast',):
            return validity_date(run, 0).strftime("%Y_%m_%d")

    def batch_is_complete(self, previous, current):
        """Detect when next day/month is extracted"""
        if self.groupby == ('timeseries', 'daily'):
            return validity_date(*previous).day != validity_date(*current).day
        if self.groupby == ('timeseries', 'monthly'):
            return validity_date(*previous).month != validity_date(*current).month
        if self.groupby == ('forecast',):
            return previous[0] != current[0]


class DictNamespace:
    """A trick to use attributes instead of dictionary keys"""
    def __init__(self, dict_):
        self.__dict__ = dict_

    def get(self, key):
        return self.__dict__.get(key)


class TimeIterator:
    def __init__(self, config_user):
        self.model = config_user.get("model")
        self.run = config_user.get("run")
        self.start_date = config_user.get("start_date")
        self.end_date = config_user.get("end_date")
        self.start_term = config_user.get("start_term")
        self.end_term = config_user.get("end_term")
        self.delta_t = config_user.get("delta_t")
        self.term = config_user.get("term")

        assert isinstance(self.start_date, datetime)
        assert isinstance(self.end_date, datetime)

    def dateiterator(self):
        current_date = self.start_date
        while current_date <= self.end_date:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (current_date, current_term)
                current_term += self.delta_t
            current_date += timedelta(days=1)

    def dateiteratorforecast(self):
        current_date = self.start_date
        while current_date <= self.end_date:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (datetime.combine(current_date, time(hour=self.run)), current_term)
                current_term += self.delta_t
            current_date += timedelta(days=1)

    def dateiteratoranalysis(self):
        current_datetime = self.start_date
        while current_datetime <= self.end_date:
            yield (current_datetime, self.term)
            current_datetime += timedelta(hours=self.delta_t)

    def get_iterator(self):
        if "analysis" in self.model:
            return self.dateiteratoranalysis()
        else:
            return self.dateiteratorforecast()


def check_config_user(config_user):

    assert config_user["start_date"] <= config_user["end_date"], "Start date must be before or equal to end date"

    if not isinstance(config_user["domain"], list):
        config_user["domain"] = list(config_user["domain"])
    assert isinstance(config_user["domain"], list)

    group_results_as_time_series = config_user["groupby"][0] == 'timeseries'
    model_is_in_forecast_mode = not "analysis" in config_user["model"]
    if group_results_as_time_series and model_is_in_forecast_mode:
        str_raise = "In mode time series, between duration between terms must be 24h"
        assert config_user["end_term"] - config_user["start_term"] == 24, str_raise


def execute(config_user):
    # Record time
    extraction_starts = datetime.now()

    check_config_user(config_user)

    # A trick to use c.attribute instead of c["attribute"]
    c = DictNamespace(config_user)

    # Create folder and subfolders
    layout = FolderLayout(work_folder=c.work_folder)

    # Initialize grouper
    grouper = Grouper(c.groupby)

    # Initialize computer
    computer = ComputedValues(
        layout,
        domain=c.domain,
        computed_vars=c.variables,
        autofetch_native=True,
        model=c.model)

    # Time iterator
    iterator = TimeIterator(config_user)

    previous_date = (c.get("start_date"), c.get("start_term"))
    for date_, term in iterator.get_iterator():
        current_date = (date_, term)
        time_tag = grouper.filetag(*previous_date)

        # Look if all files (all members and all domains) are already in final folder
        if computer.files_are_in_final(time_tag):
            continue
        else:
            if grouper.batch_is_complete(previous_date, current_date):
                computer.concat_and_clean_computed_folder(time_tag)
                computer.clean_cache_folder()

            retry_and_finally_raise(
                onRetry=send_problem_extraction_email(config_user),
                onFailure=send_script_stopped_email(config_user)
            )(computer.compute)(*current_date)

            previous_date = (date_, term)

    last_time_tag = grouper.filetag(*previous_date)
    computer.concat_and_clean_computed_folder(last_time_tag)
    computer.clean_cache_folder()

    # Clean predictions
    layout.clean_layout()
    computer.make_surfex_compliant()
    computer.clean_final_folder()

    # Record end time
    extraction_ends = datetime.now()

    # Email
    send_success_email(config_user)(extraction_ends, extraction_ends - extraction_starts)


def get_prestaging_file_list(config_user):
    c = DictNamespace(config_user)
    model_names = get_model_names(c.variables)
    listfiles = []
    notfound = []
    iterator = TimeIterator(config_user)

    for model_name in model_names:
        reader = AromeHendrixReader(model=model_name, getmode='locate')
        model_list_files, model_not_found = reader.get_file_list(iterator.get_iterator())
        listfiles += model_list_files
        notfound += model_not_found
    return listfiles, notfound


def get_prestaging_file(config_user):
    c = DictNamespace(config_user)
    layout = FolderLayout(work_folder=c.work_folder)
    listfiles, _ = get_prestaging_file_list(config_user)
    filepath = os.path.join(layout.work_folder, 'prestaging.txt')
    with open(filepath, 'w') as fp:
        for element in listfiles:
            fp.write(element + "\n")
    print("prestaging info successfully written to {filepath}".format(
        filepath=filepath))
