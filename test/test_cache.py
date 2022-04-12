from datetime import timedelta, time, datetime, date
from pprint import pprint
from extracthendrix.cache import AromeCacheManager
import epygram


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"
cache_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_cache_"


arome_cache_manager = AromeCacheManager(
    domain='alp',
    variables=['S090HUMI.SPECIFI', 'CLSHUMI.RELATIVE',
               'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
    native_files_folder=native_files_folder,
    cache_folder=cache_folder,
    model='AROME',
    runtime=time(0)
)

wished_date = date(2022, 4, 12)
term = 9

arome_cache_manager.put_in_cache(wished_date, term)

ventz = arome_cache_manager.read_cache(wished_date, term, 'CLSVENT.ZONAL')
