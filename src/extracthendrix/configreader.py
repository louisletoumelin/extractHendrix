from datetime import datetime, time, timedelta
import functools
import time as timeutils
import os

from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, dateiterator, get_model_names
from extracthendrix.readers import AromeHendrixReader
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_script_stopped_email, send_success_email


def onRetryDefault(exception_raised, time_fail, nb_attempts, time_to_next_retry):
    print(exception_raised, time_fail, nb_attempts, time_to_next_retry)


def onFailureDefault(exception_raised, current_time):
    print(exception_raised, current_time)


def retry_and_finally_raise(
        onRetry=onRetryDefault,
        onFailure=onFailureDefault,
        time_retries=[timedelta(hours=n) for n in [0.5, 1, 2, 3, 6]]
):
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

    def filetag(self, runtime, date_, term):
        """
        Gives a tag (str) of the date for which the extraction is valid.

        :param runtime: hour of the run
        :type runtime: int
        :param date_: date of the run
        :type date_: datetime
        :param term: hour of the term
        :type term: int
        :return: str (e.g. "2020-09-5")
        """
        if self.groupby == ('timeseries', 'daily'):
            return validity_date(runtime, date_, term).strftime("%Y-%m-%d")
        if self.groupby == ('timeseries', 'monthly'):
            return validity_date(runtime, date_, term).strftime("%Y-%m")
        if self.groupby == ('forecast',):
            return validity_date(runtime, date_, 0).strftime("%Y-%m-%d")

    def batch_is_complete(self, runtime, previous, current):
        """Detect when next day/month is extracted"""
        if self.groupby == ('timeseries', 'daily'):
            return validity_date(runtime, *previous).day != validity_date(runtime, *current).day
        if self.groupby == ('timeseries', 'monthly'):
            return validity_date(runtime, *previous).month != validity_date(runtime, *current).month
        if self.groupby == ('forecast',):
            return previous[0] != current[0]


class DictNamespace:
    """A trick to use attributes instead of dictionary keys"""
    def __init__(self, dict_):
        self.__dict__ = dict_


def execute(config_user):
    # Record time
    extraction_starts = datetime.now()

    # A trick to use c.attribute instead of c["attribute"]
    c = DictNamespace(config_user)

    # Create folder and subfolders
    layout = FolderLayout(work_folder=c.work_folder)

    # Initialize grouper
    grouper = Grouper(c.groupby)

    computer = ComputedValues(
        layout,
        domain=c.domain,
        computed_vars=c.variables,
        analysis_hour=c.analysis_hour,
        autofetch_native=True
    )

    previous = (c.start_date, c.start_term)
    for date_, term in dateiterator(c.start_date, c.end_date, c.start_term, c.end_term, c.delta_terms):
        if grouper.batch_is_complete(c.analysis_hour, previous, (date_, term)):
            computer.concat_files_and_forget(
                grouper.filetag(c.analysis_hour, *previous)
            )

        retry_and_finally_raise(
            onRetry=send_problem_extraction_email(config_user),
            onFailure=send_script_stopped_email(config_user)
        )(computer.compute)(date_, term)

        previous = (date_, term)

    computer.concat_files_and_forget(
        grouper.filetag(c.analysis_hour, *previous)
    )
    extraction_ends = datetime.now()
    send_success_email(config_user)(
        extraction_ends, extraction_ends - extraction_starts)


def get_prestaging_file_list(config_user):
    c = DictNamespace(config_user)
    model_names = get_model_names(c.variables)
    listfiles = []
    notfound = []
    for model_name in model_names:
        reader = AromeHendrixReader(
            model=model_name,
            runtime=time(hour=c.analysis_hour),
            getmode='locate'
        )
        model_list_files, model_not_found = reader.get_file_list(
            dateiterator(
                c.start_date, c.end_date,
                c.start_term, c.end_term,
                c.delta_terms
            )
        )
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
