from extracthendrix import execute, prestage, documentation, \
    help_variables, help_model, help_groupby, help_domain
from datetime import datetime

config_user = dict(
    work_folder="path/to/my/folder/",
    model="ARPEGE",
    domain=["alp", "switzerland"],
    variables=["Tair", "Wind", "SWE"],
    email_address="louis.letoumelin@meteo.fr",
    start_date=datetime(2022, 6, 26),
    end_date=datetime(2022, 6, 27),
    groupby=('timeseries', 'daily'),
    run=0,
    delta_t=1,
    start_term=6,
    end_term=29
)

# prestage(config_user)
execute(config_user)
