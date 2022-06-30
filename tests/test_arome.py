import pytest
from extracthendrix.readers import AromeHendrixReader, NativeFileUnfetchedException
from extracthendrix.generic import AromeCacheManager
from extracthendrix.generic import FolderLayout
from extracthendrix.configreader import execute, prestage
import extracthendrix.config.variables.arome_native as an
import os
import shutil
from datetime import date, time, datetime

"""
To run this file, install pytest (pip install pytest).

pytest --disable-warnings extracthendrix/tests/test_arome.py
"""

test_folder = f"/cnrm/cen/users/NO_SAVE/{os.environ['HOME'].split('/')[-1]}/extracthendrix/testing/"
test_data_folder = '/cnrm/cen/users/NO_SAVE/merzisenh/test_data_extracthendrix/'
folderLayout = FolderLayout(work_folder=test_folder)

# pytest --disable-warnings test_arome.py

@pytest.fixture
def folder():
    return f"/cnrm/cen/users/NO_SAVE/{os.environ['HOME'].split('/')[-1]}/extracthendrix/testing"


@pytest.fixture
def data_folder():
    return '/cnrm/cen/users/NO_SAVE/merzisenh/test_data_extracthendrix/'


def setup_function():
    folderLayout.create_layout()


def teardown_function(test_folder):
    shutil.rmtree(test_folder, ignore_errors=True)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionnally")
def test_read_arome(folderLayout):
    model = 'AROME'
    reader = AromeHendrixReader(folderLayout, model, time(hour=3))
    reader.get_native_file(date(2022, 6, 17), 1)

def test_put_in_cache_arome(helpers):
    try:
        helpers.symlink_files(test_data_folder, test_folder, 'arome', '_native_')
    except FileExistsError:
        pass
    domain = 'alp'
    date_, term = datetime(2022, 6, 17, 3), 1
    variables = [an.CLSTEMPERATURE, an.S090TEMPERATURE,
                 an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN, an.SURFTEMPERATURE]

    cache_manager = AromeCacheManager(
        domain=domain,
        native_variables=variables,
        folderLayout=folderLayout,
        model='AROME',
        delete_native=False,
        autofetch_native=True
    )
    cache_manager.put_in_cache(date_, term, domain)
    expected_name = cache_manager.get_path_file_in_cache(date_, term, domain)
    assert os.path.isfile(os.path.join(folderLayout._cache_, expected_name))


def test_put_in_cache_arome_no_native_file_no_autofetch(helpers, folder, data_folder):
    try:
        helpers.symlink_files(data_folder, folder, 'arome', '_native_')
    except FileExistsError:
        pass
    domain = 'alp'
    # this term is not in the testing data so we're supposed to raise an exception
    date_, term = datetime(2022, 6, 17), 3
    variables = [an.CLSTEMPERATURE, an.S090TEMPERATURE,
                 an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN, an.SURFTEMPERATURE]
    cache_manager = AromeCacheManager(
        domain=domain,
        native_variables=variables,
        folderLayout=folderLayout,
        model='AROME',
        delete_native=False,
        autofetch_native=False
    )
    with pytest.raises(NativeFileUnfetchedException):
        cache_manager.put_in_cache(date_, term, domain)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionally")
def test_config_arome():

    config_user = dict(
        work_folder=test_folder,
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
        end_term=30
    )

    execute(config_user)

    results = []
    for file in os.listdir(test_folder):
        final_folder_exists = ("HendrixExtraction" in file) and ("ID" in file)
        results.append(final_folder_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)
    assert any(results)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionally")
def test_config_arome_analysis():

    config_user = dict(
        work_folder=test_folder,
        model="AROME_analysis",
        domain=["alp", "switzerland"],
        variables=["Tair"],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2022, 6, 26, 0),
        end_date=datetime(2022, 6, 26, 1),
        groupby=('timeseries', 'daily'),
        delta_t=1,
    )

    execute(config_user)

    results = []
    for file in os.listdir(test_folder):
        final_folder_exists = ("HendrixExtraction" in file) and ("ID" in file)
        results.append(final_folder_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)
    assert any(results)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionally")
def test_config_arpege():

    for file in os.listdir(test_folder):
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)

    config_user = dict(
        work_folder=test_folder,
        model="ARPEGE",
        domain=["alp", "switzerland"],
        variables=["Tair"],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2022, 6, 26),
        end_date=datetime(2022, 6, 27),
        groupby=('timeseries', 'daily'),
        run=0,
        delta_t=1,
        start_term=6,
        end_term=30
    )

    execute(config_user)

    results = []
    for file in os.listdir(test_folder):
        final_folder_exists = ("HendrixExtraction" in file) and ("ID" in file)
        results.append(final_folder_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)
    assert any(results)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionally")
def test_arpege_analysis_4dvar():

    for file in os.listdir(test_folder):
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)

    config_user = dict(
        work_folder=test_folder,
        model="ARPEGE_analysis_4dvar",
        domain=["alp", "switzerland"],
        variables=["Tair"],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2022, 6, 28, 0),
        end_date=datetime(2022, 6, 29, 5),
        groupby=('timeseries', 'daily'),
        delta_t=1,
        start_term=6,
        end_term=30)

    execute(config_user)

    results = []
    for file in os.listdir(test_folder):
        final_folder_exists = ("HendrixExtraction" in file) and ("ID" in file)
        results.append(final_folder_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)
    assert any(results)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionally")
def test_pearp():

    for file in os.listdir(test_folder):
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)

    config_user = dict(
        work_folder=test_folder,
        model="PEARP",
        domain=["alp", "switzerland"],
        variables=["Tair"],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2022, 6, 28, 0),
        end_date=datetime(2022, 6, 28, 3),
        groupby=('timeseries', 'daily'),
        run=0,
        delta_t=1,
        start_term=6,
        end_term=30,
        members=[1, 2])

    execute(config_user)

    results = []
    for file in os.listdir(test_folder):
        final_folder_exists = ("HendrixExtraction" in file) and ("ID" in file)
        results.append(final_folder_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)
    assert any(results)


def test_prestaging():

    for file in os.listdir(test_folder):
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)

    config_user = dict(
        work_folder=test_folder,
        model="AROME",
        domain=["alp", "switzerland"],
        variables=["SWE"],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2021, 1, 26),
        end_date=datetime(2021, 1, 30),
        groupby=('timeseries', 'daily'),
        run=0,
        delta_t=1,
        start_term=6,
        end_term=30
    )

    prestage(config_user)

    results = []
    for file in os.listdir(test_folder):
        prestaging_file_exists = ("prestaging" in file)
        results.append(prestaging_file_exists)
        path_to_file = os.path.join(test_folder, file)
        shutil.rmtree(path_to_file, ignore_errors=True)

    assert any(results)
