import epygram
import pytest
from extracthendrix.readers import AromeHendrixReader, NativeFileUnfetchedException
from extracthendrix.generic import AromeCacheManager, sort_native_vars_by_model, FolderLayout
import os
import shutil
from datetime import date, time, datetime
from extracthendrix.config.variables import pearome
import extracthendrix.config.variables.arome_native as an


test_folder = f"/cnrm/cen/users/NO_SAVE/{os.environ['HOME'].split('/')[-1]}/extracthendrix/testing/"
test_data_folder = '/cnrm/cen/users/NO_SAVE/merzisenh/test_data_extracthendrix/'
folderLayout = FolderLayout(work_folder=test_folder)


@pytest.fixture
def folder():
    return f"/cnrm/cen/users/NO_SAVE/{os.environ['HOME'].split('/')[-1]}/extracthendrix/testing"


@pytest.fixture
def data_folder():
    return '/cnrm/cen/users/NO_SAVE/merzisenh/test_data_extracthendrix/'


def setup_function():
    folderLayout.create_layout()


def teardown_function(test_folder):
    print(test_folder)
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
    print("debug")
    print("test_put_in_cache_arome_no_native_file_no_autofetch")
    with pytest.raises(NativeFileUnfetchedException):
        cache_manager.put_in_cache(date_, term, domain)