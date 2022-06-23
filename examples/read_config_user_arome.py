from datetime import datetime, timedelta
import extracthendrix.config.variables.arome as ar
from extracthendrix.configreader import execute, get_prestaging_file_list, get_prestaging_file
from extracthendrix.hendrix_emails import send_problem_extraction_email, send_success_email, send_script_stopped_email


config_user = dict(
    work_folder="/cnrm/cen/users/NO_SAVE/merzisenh/pourisabelle2",
    domain="alp",
    variables=[ar.SWE],
    email_adress="hugo.merzisen@meteo.fr",
    start_date=datetime(2022, 6, 21),
    end_date=datetime(2022, 6, 23),
    groupby=('timeseries', 'daily'),
    analysis_hour=0,
    delta_terms=6,
    start_term=6,
    end_term=30
)

execute(config_user)
# listfiles, notfound = get_prestaging_file_list(config_user)
# get_prestaging_file(config_user)


# send_problem_extraction_email(config_user)(
#     Exception('boum'), datetime(2022, 2, 2, 2), 3, timedelta(hours=1)
# )

# send_success_email(config_user)(
#     current_time=datetime(2022, 2, 2, 2),
#     time_to_download=timedelta(hours=34567)
# )

# send_script_stopped_email(config_user)(
#     current_time=datetime(2022, 2, 2, 2),
#     exception = Exception('PAF')
#     )
