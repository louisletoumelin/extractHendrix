import pytest
from extracthendrix.readers import AromeHendrixReader
from extracthendrix.generic import AromeCacheManager, sort_native_vars_by_model
import os
import shutil
from datetime import date, time
from extracthendrix.config.variables import pearome


test_folder = '/home/merzisenh/NO_SAVE/extracthendrix/testing'

native_files_folder = os.path.join(test_folder, '_native_')
data_folder = os.path.join(test_folder, 'data', 'pearome')
cache_folder = os.path.join(test_folder, '_cache_')


def setup_module():
    os.mkdir(native_files_folder)
    os.mkdir(cache_folder)


def teardown_module():
    shutil.rmtree(native_files_folder)
    shutil.rmtree(cache_folder)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionnally")
@pytest.mark.parametrize("member", range(1, 5))
def test_read_pearome(member):
    model = 'PEAROME'
    reader = AromeHendrixReader(
        native_files_folder, model, time(hour=3), member=member)
    reader.get_native_file(date(2020, 3, 1), 2)


def test_cache_pearome():
    date_, term = date(2020, 3, 1), 1
    domain = 'alp'
    analysis_hour = 3
    variables_nc = [pearome.Tair, pearome.Qair,
                    pearome.Wind, pearome.Wind_DIR, pearome.Psurf]
    variables = sort_native_vars_by_model(variables_nc)['PEAROME']
    cache_manager = AromeCacheManager(
        domain=domain,
        variables=variables,
        native_files_folder=data_folder,
        cache_folder=cache_folder,
        model='PEAROME',
        runtime=time(hour=analysis_hour),
        delete_native=False,
        member=2
    )
    cache_manager.put_in_cache(date_, term)
    # expected_name = 'PEAROME-run_20200301T03-00-00Z-term_1h_mb002.grib'
    expected_name = cache_manager.get_cache_path(date_, term)
    assert os.path.isfile(os.path.join(cache_folder, expected_name))
