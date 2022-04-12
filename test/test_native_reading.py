from extracthendrix.readers import AromeHendrixReader
from datetime import date, time


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"


reader = AromeHendrixReader(
    native_files_folder=native_files_folder,
    model='AROME',
    runtime=time(0)
)


wished_date = date(2022, 4, 12)
term = 6


reader.get_native_file(wished_date, term)
