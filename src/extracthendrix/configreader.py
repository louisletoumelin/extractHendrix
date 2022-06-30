from datetime import datetime, time, timedelta
import functools
import time as timeutils
import os
import logging
import glob

from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, get_model_names
from extracthendrix.readers import AromeHendrixReader
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_script_stopped_email, send_success_email

logging.getLogger("footprints").setLevel("ERROR")
logging.getLogger('vortex').setLevel("ERROR")
logging.basicConfig(level=logging.DEBUG,
                    handlers=[logging.StreamHandler()],
                    format='\n[%(asctime)s][%(name)s][%(levelname)s]%(message)s')
logger = logging.getLogger(__name__)
logger.setLevel("DEBUG")


def onRetryDefault(exception_raised, time_fail, nb_attempts, time_to_next_retry):
    """Print when retry to launch extraction after an error has been raised (e.g. problem on Hendrix)."""
    #print(exception_raised, time_fail, nb_attempts, time_to_next_retry)
    logger.warning(exception_raised, time_fail, nb_attempts, time_to_next_retry)


def onFailureDefault(exception_raised, current_time):
    """Print when failed to launch extraction after an error has been raised (e.g. problem on Hendrix)."""
    #print(exception_raised, current_time)
    logger.warning(exception_raised, current_time)


def delete_last_file_in_folder(path):
    list_of_files = glob.glob(path + '/*')
    if list_of_files:
        latest_file = max(list_of_files, key=os.path.getctime)
        os.remove(latest_file)
        logger.info(f"Deleted {latest_file}")


def retry_and_finally_raise(
        onRetry=onRetryDefault,
        onFailure=onFailureDefault,
        layout=None,
        time_retries=[timedelta(hours=0.01)]): #timedelta(hours=n) for n in [0.5, 1, 2, 3, 6]
    """
    Decorator to retry extraction when an error is raised, until a point where we assume the code failed and raise
    an exception.

    This permits to wait when Hendrix has problem and not stop the extraction. For example, if Hendrix has a problem
    for 3 hours we will wait before relaunching the extraction.

    :param onRetry: Function to print on retry.
    :param onFailure: Function to print on failure.
    :param time_retries: Time intervals to wait before trying to relaunch extraction.
    :type time_retries: list of datetime.timedelta.
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
                if layout:
                    #delete_last_file_in_folder(layout._cache_)
                    delete_last_file_in_folder(layout._computed_)
                    #delete_last_file_in_folder(layout._native_)
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

    def get(self, key, default_value=None):
        return self.__dict__.get(key, default_value)


class TimeIterator:
    """
    A class to select the iterator:

    1. Iterate on terms with runtime fixed for forecast.
    2. Iterate on runtime with term fixed for analysis.
    """
    def __init__(self, config_user):
        """
        :param config_user: Dictionary containing the configuration as given by the user.
        """
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
        """Depreciated, old iterator"""
        current_date = self.start_date
        while current_date <= self.end_date:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (current_date, current_term)
                current_term += self.delta_t
            current_date += timedelta(days=1)

    def dateiteratorforecast(self):
        """Iterator for forecasts"""
        current_date = self.start_date
        while current_date <= self.end_date:
            current_term = self.start_term
            while current_term <= self.end_term:
                yield (datetime.combine(current_date, time(hour=self.run)), current_term)
                current_term += self.delta_t
            current_date += timedelta(days=1)

    def dateiteratoranalysis(self):
        """Iterator for analysis"""
        current_datetime = self.start_date
        while current_datetime <= self.end_date:
            yield (current_datetime, self.term)
            current_datetime += timedelta(hours=self.delta_t)

    def dateiterator4dvar(self, synoptic_hour=6):
        """Iterator for 4dvar analysis"""
        current_datetime = self.start_date
        while current_datetime <= self.end_date:
            hour_analysis = 6 * (current_datetime.hour // synoptic_hour)
            analysis_date = current_datetime.replace(hour=hour_analysis)
            term = current_datetime.hour % 6
            yield (analysis_date, term)
            current_datetime += timedelta(hours=self.delta_t)

    def get_iterator(self):
        """Return the appropriate iterator given a model name"""
        model_is_analysis = "analysis" in self.model
        model_is_4dvar = "4dvar" in self.model
        if model_is_analysis and not model_is_4dvar:
            return self.dateiteratoranalysis()
        elif model_is_4dvar:
            return self.dateiterator4dvar()
        else:
            return self.dateiteratorforecast()


def check_config_user(config_user):
    """
    Assert that user configuration, i.e. the dictionary given by the user with all the specifiactions of the extraction,
    is correct
    """
    assert config_user["start_date"] <= config_user["end_date"], "Start date must be before or equal to end date"

    if not isinstance(config_user["domain"], list):
        config_user["domain"] = list(config_user["domain"])
    assert isinstance(config_user["domain"], list)

    group_results_as_time_series = config_user["groupby"][0] == 'timeseries'
    model_is_in_forecast_mode = not "analysis" in config_user["model"]
    if group_results_as_time_series and model_is_in_forecast_mode:
        str_raise = "In mode time series, between duration between terms must be 24h"
        assert config_user["end_term"] - config_user["start_term"] == 24, str_raise

    return config_user

def execute(config_user):
    """
    Main function that triggers the execution of the extraction as specified by the user in config_user.

    Example of a config user:

        config_user = dict(
            work_folder="/home/letoumelinl/develop/examples/",
            model="AROME",
            domain=["alp", "switzerland"],
            variables=["SWE"],
            email_address="louis.letoumelin@meteo.fr",
            start_date=datetime(2022, 6, 26),
            end_date=datetime(2022, 6, 26),
            groupby=('timeseries', 'daily'),
            run=0,
            delta_t=1,
            start_term=6,
            end_term=30)

    :param config_user: Dictionary containing the configuration as given by the user.
    """
    logger.info("Start extraction")

    # Record time
    extraction_starts = datetime.now()

    config_user = check_config_user(config_user)

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
        model=c.model,
        members=c.get("members", [None]))

    # Time iterator
    iterator = TimeIterator(config_user)

    previous_date = (c.get("start_date"), c.get("start_term"))
    for date_, term in iterator.get_iterator():
        current_date = (date_, term)
        time_tag = grouper.filetag(*previous_date)

        # Look if all files (all members and all domains) are already in final folder
        if computer.files_are_in_final(time_tag):
            logger.debug(f"File {date_}, term {term}, already in cache")
            continue
        else:
            if grouper.batch_is_complete(previous_date, current_date):
                computer.concat_and_clean_computed_folder(time_tag)
                computer.clean_cache_folder()

            retry_and_finally_raise(
                onRetry=send_problem_extraction_email(config_user),
                onFailure=send_script_stopped_email(config_user),
                layout=layout
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

    logger.info("Extraction finished")


def get_prestaging_file_list(config_user, layout):
    """
    Prepare a list with the content of a prestaging file.

    :param config_user: Dictionary containing the configuration as given by the user.
    """
    c = DictNamespace(config_user)

    computer = ComputedValues(
        layout,
        domain=c.domain,
        computed_vars=c.variables,
        autofetch_native=True,
        model=c.model,
        members=c.get("members", [None]))

    model_names = get_model_names(computer.computed_vars)
    listfiles = []
    notfound = []
    iterator = TimeIterator(config_user)
    for member in computer.members:
        for model_name in model_names:
            reader = AromeHendrixReader(model=model_name, getmode='locate', member=member)
            model_list_files, model_not_found = reader.get_file_list(iterator.get_iterator())
            listfiles += model_list_files
            notfound += model_not_found
    return listfiles, notfound


def prestage(config_user):
    """
    Write a .txt file the information necessary for prestagging.

    :param config_user: Dictionary containing the configuration as given by the user.
    """

    config_user = check_config_user(config_user)

    c = DictNamespace(config_user)

    layout = FolderLayout(work_folder=c.work_folder)

    listfiles, _ = get_prestaging_file_list(config_user, layout)
    name_str = config_user["email_address"].split("@")[0].replace('.', '_')
    begin_str = config_user["start_date"].strftime("%m_%d_%Y")
    end_str = config_user["end_date"].strftime("%m_%d_%Y")
    name_txt_file = f"prestaging_{name_str}_{c.model}_begin_{begin_str}_end_{end_str}.txt"
    filepath = os.path.join(layout.work_folder, name_txt_file)

    with open(filepath, 'w') as fp:
        fp.write(f"#MAIL={c.email_address}\n")
        for element in listfiles:
            fp.write(element + "\n")

    print("\n\nPlease find below the procedure for prestaging. \
        Note a new file named 'request_prestaging_*.txt' has been created on your current folder\n\n1. \
        Drop this file on Hendrix, in the folder DemandeMig/ChargeEnEspaceRapide \
        \nYou can use FileZilla with your computer, or ftp to drop the file.\n\n2. \
        Rename the extension of the file '.txt' (once it is on Hendrix) with '.MIG'\n\
        'request_prestaging_*.txt'  => 'request_prestaging_*.MIG'\n\n\
        Note: don't rename in '.MIG' before dropping the file on Hendrix, or Hendrix could launch prestaging\
        before the file is fully uploaded\n\n3. \
        Please wait for an email from the Hendrix team to download your data\n\n")

    print("Prestaging info successfully written to {filepath}".format(filepath=filepath))


def print_link_to_hendrix_documentation():
    print("The documentation of the storage system Hendrix is available here:")
    print("http://confluence.meteo.fr/pages/viewpage.action?pageId=299881305")


def print_link_to_confluence_table_with_downloaded_data():
    link = "http://confluence.meteo.fr/pages/viewpage.action?pageId=314552092"
    print("\nHave you check that the data you request is not already downloaded at CEN?\n")
    print("Please see the link below")
    print(link)


def print_link_to_arome_variables():
    link = "http://intra.cnrm.meteo.fr/aromerecherche/spip.php?article25"
    print("Website with all AROME variables (might be outdated)")
    print(link)
    link = "https://opensource.umr-cnrm.fr/projects/pnt-mine/wiki/Champs_de_surface_des_fichiers_de_sortie_en_PNT"
    print("Website with all AROME surface variables (might be outdated)")
    print(link)


def documentation():
    """Print documentation about Hendrix, Data already downloaded at cen, AROME variables"""
    print_link_to_hendrix_documentation()
    print_link_to_confluence_table_with_downloaded_data()
    print_link_to_arome_variables()
