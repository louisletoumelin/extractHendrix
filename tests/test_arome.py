import epygram
import pytest
from extracthendrix.readers import AromeHendrixReader, NativeFileUnfetchedException
from extracthendrix.generic import AromeCacheManager, sort_native_vars_by_model, FolderLayout
import os
import shutil
from datetime import date, time
from extracthendrix.config.variables import pearome
import extracthendrix.config.variables.arome_native as an


test_folder = '/home/merzisenh/NO_SAVE/extracthendrix/testing'
test_data_folder = '/home/merzisenh/NO_SAVE/test_data_extracthendrix'
folderLayout = FolderLayout(work_folder=test_folder)


def setup_function():
    folderLayout._create_layout()


def teardown_function():
    shutil.rmtree(test_folder)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionnally")
def test_read_arome():
    model = 'AROME'
    reader = AromeHendrixReader(folderLayout, model, time(hour=3))
    reader.get_native_file(date(2022, 6, 17), 1)


def test_put_in_cache_arome(helpers):
    helpers.symlink_files(test_data_folder, test_folder, 'arome', '_native_')
    domain = 'alp'
    analysis_hour = 3
    date_, term = date(2022, 6, 17), 1
    variables = [an.CLSTEMPERATURE, an.S090TEMPERATURE,
                 an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN, an.SURFTEMPERATURE]
    cache_manager = AromeCacheManager(
        domain=domain,
        variables=variables,
        folderLayout=folderLayout,
        model='AROME',
        runtime=time(hour=analysis_hour),
        delete_native=False,
        autofetch_native=False
    )
    cache_manager.put_in_cache(date_, term)
    expected_name = cache_manager.get_cache_path(date_, term)
    assert os.path.isfile(os.path.join(folderLayout._cache_, expected_name))


def test_put_in_cache_arome_no_native_file_no_autofetch(helpers):
    helpers.symlink_files(test_data_folder, test_folder, 'arome', '_native_')
    domain = 'alp'
    analysis_hour = 3
    # this term is not in the testing data so we're supposed to raise an exception
    date_, term = date(2022, 6, 17), 3
    variables = [an.CLSTEMPERATURE, an.S090TEMPERATURE,
                 an.CLSVENT__ZONAL, an.CLSVENT__MERIDIEN, an.SURFTEMPERATURE]
    cache_manager = AromeCacheManager(
        domain=domain,
        variables=variables,
        folderLayout=folderLayout,
        model='AROME',
        runtime=time(hour=analysis_hour),
        delete_native=False,
        autofetch_native=False
    )
    with pytest.raises(NativeFileUnfetchedException) as e_info:
        cache_manager.put_in_cache(date_, term)
