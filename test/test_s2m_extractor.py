from datetime import timedelta, time, datetime, date
from pprint import pprint

from extracthendrix.s2m_extractor import S2MExtractor

extractor = S2MExtractor(
        folder="demo",
        kind="pro",
        previ=True,
        runtime=time(hour=3),
        geometry="cor",
        member=36)






pprint(extractor.get_available_runs())

extractor.get_netcdf(date(2021,5,5))


geometry="cor"
argsextract = dict(folder='/home/merzisenh/NO_SAVE/cachesytron', geometry=geometry, member=36)

datevalidite = date(2022,1,27)


forcing_ana = S2MExtractor(kind='meteo',runtime=time(hour=6), previ=False, **argsextract).get_netcdf(datevalidite)




