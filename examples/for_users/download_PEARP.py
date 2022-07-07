from extracthendrix import execute, prestage, documentation, \
    help_variables, help_model, help_groupby, help_domain
from datetime import datetime


config_user = dict(
    work_folder="path/to/my/folder/",
    model="PEARP",
    domain=["alp", "switzerland"],
    variables=["Tair"],
    email_address="louis.letoumelin@meteo.fr",
    start_date=datetime(2022, 6, 28, 0),
    end_date=datetime(2022, 6, 28, 3),
    groupby=('timeseries', 'daily'),
    run=0,
    delta_t=1,
    start_term=6,
    end_term=29,
    members=[1, 2])

# prestage(config_user)
execute(config_user)
