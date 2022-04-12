from extracthendrix import AromeCacheManager
from datetime import timedelta, time, datetime, date
from pprint import pprint
from extracthendrix.cache import AromeCacheManager
from extracthendrix.writers import dataConcatenator
from extracthendrix.config.variables import arome, arome_surface

native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"
cache_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_cache_"


arome_cache_manager = AromeCacheManager(
    domain='alp',
    variables=['CLSTEMPERATURE', 'S090TEMPERATURE',
               'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
    native_files_folder=native_files_folder,
    cache_folder=cache_folder,
    model='AROME',
    runtime=time(0)
)

dateiterator = [
    (datetime(2022, 4, 10, 0, 0), 6),
    (datetime(2022, 4, 10, 0, 0), 7),
    (datetime(2022, 4, 10, 0, 0), 8),
    (datetime(2022, 4, 10, 0, 0), 9),
    (datetime(2022, 4, 10, 0, 0), 10),
    (datetime(2022, 4, 10, 0, 0), 11),
    (datetime(2022, 4, 10, 0, 0), 12)
]

final_dataset = dataConcatenator(dateiterator, arome_cache_manager)
