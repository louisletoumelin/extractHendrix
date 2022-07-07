from extracthendrix import execute, prestage, documentation, \
    help_variables, help_model, help_groupby, help_domain
from datetime import datetime


config_user = dict(
    work_folder="path/to/my/folder/",
    model="AROME_analysis",
    domain=["alp", "switzerland"],
    variables=["Tair"],
    email_address="louis.letoumelin@meteo.fr",
    start_date=datetime(2022, 6, 26, 0),
    end_date=datetime(2022, 6, 26, 1),
    groupby=('timeseries', 'daily'),
    delta_t=1,
)

# prestage(config_user)
execute(config_user)
