import epygram
import pytest
from extracthendrix.readers import AromeHendrixReader
from extracthendrix.generic import AromeCacheManager, sort_native_vars_by_model, FolderLayout
import os
import shutil
from datetime import date, time, datetime
from extracthendrix.config.variables import pearome
import extracthendrix.config.variables.pearome_grib as peg


test_folder = f"/cnrm/cen/users/NO_SAVE/{os.environ['HOME'].split('/')[-1]}/extracthendrix/testing/"
test_data_folder = '/home/merzisenh/NO_SAVE/test_data_extracthendrix'

folderLayout = FolderLayout(work_folder=test_folder)

# TODO: (to keep it easy)
# test_data contains folders _native_, _cache_ to test CacheManager, ComputedValues, etc...
# symlink


def setup_function():
    folderLayout.create_layout()


def teardown_function():
    shutil.rmtree(test_folder)


@pytest.mark.skip(reason="fetching on Hendrix takes too long, run this test occasionnally")
@pytest.mark.parametrize("member", range(1, 5))
def test_read_pearome(member):
    model = 'PEAROME'
    reader = AromeHendrixReader(
        folderLayout, model, time(hour=3), member=member)
    reader.get_native_file(date(2020, 3, 1), 2)


def test_put_in_cache_pearome(helpers):
    helpers.symlink_files(test_data_folder, test_folder, 'pearome', '_native_')
    date_, term = datetime(2020, 3, 1, 3), 1
    domain = 'alp'
    native_variables = [
        peg.t2m, peg.t2m, peg.r2m, peg.pres0m, peg.u10m, peg.v10m,
        peg.u10m, peg.v10m, peg.pres0m
    ]
    cache_manager = AromeCacheManager(
        domain=domain,
        native_variables=native_variables,
        folderLayout=folderLayout,
        model='PEAROME',
        delete_native=False,
        member=2,
        autofetch_native=True
    )
    cache_manager.put_in_cache(date_, term, domain)
    expected_name = cache_manager.get_path_file_in_cache(date_, term, domain)
    assert os.path.isfile(os.path.join(folderLayout._cache_, expected_name))


def test_read_cache_pearome(helpers):
    helpers.symlink_files(test_data_folder, test_folder, 'pearome', '_cache_')
    date_, term = datetime(2020, 3, 1, 3), 1
    domain = 'alp'
    native_variables = [
        peg.t2m, peg.t2m, peg.r2m, peg.pres0m, peg.u10m, peg.v10m,
        peg.u10m, peg.v10m, peg.pres0m
    ]
    cache_manager = AromeCacheManager(
        domain=domain,
        native_variables=native_variables,
        folderLayout=folderLayout,
        model='PEAROME',
        delete_native=False,
        autofetch_native=True,
        member=2
    )
    t2m = cache_manager.read_cache(date_, term, domain, peg.t2m)
    # persistency test: this value must remain the same when we update the code
    assert t2m.isel(xx=50, yy=50).item() == 271.1785136721989
