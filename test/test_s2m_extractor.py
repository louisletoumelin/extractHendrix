from extracthendrix.s2m_extractor import *
from pprint import pprint

help = S2MArgHelper(
    model='S2M_PRO',
    member=36,
    runtime=time(hour=3),
    geometry='cor'
)
params = help.get_params_for_run_with_date(datetime(2022, 3, 12), -30)
pprint(params)
# noter que nulle part on n'indique previ=True/False c'est l'échéance qui va déterminer quel est sa valeur
extractor = S2MExtractor(folder='tmp', s2mArgHelper=help)

extractor.get_netcdf(datetime(2022, 3, 26), 10)
extractor.get_netcdf(datetime(2022, 3, 27), 10)
