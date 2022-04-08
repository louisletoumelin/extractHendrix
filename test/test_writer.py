from extracthendrix import AromeCacheManager
from datetime import timedelta, time, datetime, date
from pprint import pprint
from extracthendrix.cache import AromeCacheManager
from extracthendrix.writers import dataConcatenator

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

dates = [
    date(2022, 4, 5),
    date(2022, 4, 6),
    date(2022, 4, 7)
]

terms = [3]

final_dataset = dataConcatenator(dates, terms, arome_cache_manager)
