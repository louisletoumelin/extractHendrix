from datetime import datetime
import extracthendrix.config.variables.arome as ar
from extracthendrix.configreader import execute


config_user = dict(
    work_folder="/cnrm/cen/users/NO_SAVE/merzisenh/mythirdextraction",
    domain="alp",
    variables=[ar.SWE],
    email_adress="hugo.merzisen@meteo.fr",
    start_date=datetime(2022, 6, 21),
    end_date=datetime(2022, 6, 22),
    groupby = ('forecast',),
    analysis_hour=0,
    delta_terms=1,
    start_term=0,
    end_term=48
)

execute(config_user)
