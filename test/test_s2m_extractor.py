from datetime import timedelta, time, datetime, date
from pprint import pprint

from extracthendrix.s2m_extractor import S2MExtractor

extractor = S2MExtractor(folder='demo',kind='pro', previ=True, runtime=time(hour=3), member=36, geometry='cor')
pprint(extractor.get_available_runs())
extractor.get_netcdf(date(2021,5,5))

