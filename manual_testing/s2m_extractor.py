from extracthendrix.readers import S2MHendrixReader, S2MArgHelper
from pprint import pprint
from datetime import time, datetime
from netCDF4 import Dataset
import xarray as xr


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"

helper = S2MArgHelper(model='S2M_PRO', member=36,
                      runtime=time(hour=3), geometry='cor')
# helper = S2MArgHelper(model='S2M_PRO', member=35, geometry='cor')

pprint(helper.get_available_runs())


extractor = S2MHendrixReader(native_files_folder=native_files_folder,
                             cache_folder='/home/merzisenh/CACHE/netcdf/',
                             s2mArgHelper=helper)


# params = help.get_params_for_run_with_date(datetime(2022, 3, 12), -30)
# noter que nulle part on n'indique previ=True/False c'est l'échéance qui va déterminer quel est sa valeur

date1 = datetime(2022, 3, 26)
date2 = datetime(2022, 3, 27)
extractor.get_native_file(date1, 10)
extractor.get_native_file(date2, 10)
