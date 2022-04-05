from extracthendrix.core import HendrixConductor
from datetime import date, datetime, timedelta, time
from extracthendrix.extractors import AromeExtractor, S2MExtractor, S2MArgHelper

native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"


# analysis_time = datetime(2022, 4, 1, 0)

# hc = HendrixConductor('hendrix', 'test_hc', 'AROME', analysis_time, 'alp', [
#                       'snow_density', 'LWdown'], None, 1)

# hc.get_resource_from_hendrix(3)

# hc.model_description = hc.model_description[0:1]

arome_extr = AromeExtractor(
    native_files_folder=native_files_folder, model='AROME', runtime=time(0))
# arome_extr.model_description_and_alternative_parameters = arome_extr.model_description_and_alternative_parameters[0:1]

# arome_extr._get_native_file(date(2022, 4, 1), 3)
# arome_extr._get_native_file(date(2022, 4, 1), 4)
# arome_extr._get_native_file(date(2022, 4, 1), 5)


helper = S2MArgHelper(model='S2M_PRO', member=36,
                      runtime=time(hour=3), geometry='cor')
s2m_extr = S2MExtractor(native_files_folder=native_files_folder,
                        cache_folder='/home/merzisenh/CACHE/netcdf/',
                        s2mArgHelper=helper)
s2m_extr._get_native_file(date(2022, 4, 1), 0)
s2m_extr._get_native_file(date(2022, 4, 1), 3)
s2m_extr._get_native_file(date(2022, 4, 1), -15)
