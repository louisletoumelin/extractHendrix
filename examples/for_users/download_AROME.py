from extracthendrix import execute, prestage, documentation, \
    help_variables, help_model, help_groupby, help_domain
from datetime import datetime

# The following configuration will download AROME forecasts
config_user = dict(

    # Your folder. If it doesn't exists, it will be created.
    work_folder="path/to/my/folder/",

    # Model: "AROME", "AROME_analysis", "PEAROME", "ARPEGE", "ARPEGE_analysis_4dvar", "PEARP"...
    # Use help_model() command to get help with this key.
    model="AROME",

    # Domain: "alp", "corsica", "pyr", "switzerland". You can give one or many, and it will not significantly
    # impact extraction time. However, it will require more memory storage.
    # Use help_domain() command to get help with this key.
    domain=["alp", "corsica", "pyr", "switzerland"],

    # Variables. Use help_model("AROME") if you need the names and description of variables.
    variables=['Tair', 'T1', 'ts', 'Tmin', 'Tmax', 'Qair', 'Q1', 'RH2m', 'Wind', 'Wind_Gust', 'Wind_DIR',
                'PSurf', 'ZS', 'BLH', 'Rainf', 'Snowf', 'LWdown', 'LWnet', 'DIR_SWdown', 'SCA_SWdown',
                'SWnet', 'SWD', 'SWU', 'LHF', 'SHF', 'CC_cumul', 'CC_cumul_low', 'CC_cumul_middle',
                'CC_cumul_high', 'Wind90', 'Wind87', 'Wind84', 'Wind75', 'TKE90', 'TKE87', 'TKE84', 'TKE75',
                'TT90', 'TT87', 'TT84', 'TT75', 'SWE', 'snow_density', 'snow_albedo', 'vegetation_fraction'],

    # We send mail if there is a problem or if the extraction is finished.
    email_address="louis.letoumelin@meteo.fr",

    # Extraction starts at start_date
    start_date=datetime(2018, 10, 31),

    # Extraction ends at end_date
    end_date=datetime(2018, 10, 31),

    # How you want your files to be grouped at the end. If you use ('timeseries', 'daily'),
    # you will have continuous time series of data, and one netcdf file for one day.
    # Use help_groupby() command to get help with this key.
    groupby=('timeseries', 'daily'),

    # Runtime to use
    run=0,

    # Delta time between terms (for forecasts), or between dates (for analysis).
    # Ex: delta_t=1 will extract hourly data. delta_t=5 only every 5 hours.
    delta_t=1,

    # Starts extraction for this forecast lead time (for forecast only).
    start_term=6,

    # Ends extraction for this forecast lead time (for forecast only). In time_series mode (see groupby),
    # end_term - start_term == 23 in order to reconstruct continuous time series.
    end_term=29
)

# Create a prestaging file
prestage(config_user)

# Wait that Hendrix team has work with the prestaging (up to one or two days for bug extractions).

# Execute extraction
execute(config_user)

# use documentation to have information about models, Hendrix documentation, data already downloaded at CEN.
documentation()
