import extracthendrix as eh
from datetime import datetime

config_user = dict(

#  Where you want to store the outputs
folder= '/cnrm/cen/users/NO_SAVE/letoumelinl/folder3/',

# Models are defined in the models.ini file
model_name = 'AROME',

# The domain can be defined by its name or its coordinates
# Existing domain can be found in the config_fa2nc.py file
domain = "alp",

# Variables to extract and to store in the netcdf file
# Variable are defined in the config_fa2nc.py file
variables_nc = ['snow_density', 'LWdown' ,'PSurf', 'Qair', 'Rainf', 'SCA_down', 'Snowf', 'Tair', 'Wind', 'Wind_DIR', 'Wind_Gust'],

# "local" if the FA file are on your computer or "hendrix" otherwise
getter = "hendrix",

# "timeseries" or "forecast".
# Ex: "forecast" = 1 analysis at 06:00 + 30 terms ahead
mode = "timeseries",

# For prestaging and sending mail during (your mail = destination) extraction
email_address = "louis.letoumelin@meteo.fr",

# datetime(year, month, day)
date_start = datetime(2020, 6, 1),
date_end = datetime(2020, 6, 30),

# Analysis hour
run = 0,

# Delta between terms
delta_t = 1,

# Term in hour after analysis
start_term = 6, # Default: 6
end_term = 6 + 23 ,# Defautl: 6+23 = 29

# How to group the netcdf files: "month", "year", "all"
group_by_output_file = "month"
)

e = eh.Extractor(config_user)

e.download()


