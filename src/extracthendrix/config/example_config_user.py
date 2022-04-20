from datetime import datetime
from extracthendrix.config.variables import arome, arome_surface

config_user = dict(
    folder='/cnrm/cen/users/NO_SAVE/merzisenh/AROME',
    # model_name='AROME', pas nécessaire si on indique le modèle dans  models_parameters.py
    domain="alp",
    variables_nc=[arome.Tair, arome.T1,
                  arome.Wind, arome.ts, arome_surface.SWE],
    mode="timeseries",
    email_adress="hugo.merzisen@meteo.fr",
    date_start=datetime(2022, 4, 10),
    date_end=datetime(2022, 4, 11),
    analysis_hour=0,
    delta_terms=1,
    start_term=6,
    end_term=6 + 23,
    # group_by_output_file = "month"
)
