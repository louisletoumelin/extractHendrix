import epygram
import usevortex
from datetime import datetime
import os


def get_filename(model_name, analysis_time, step):
    analysis_time_str = analysis_time.strftime('%Y-%m-%d-%Hh')
    return "%s_ana:%s_step:%s"%(model_name, analysis_time_str, step)

model_description = dict(suite='oper',  # oper suite
                            kind='historic',  # model state
                            geometry='franmgsp',  # the name of the model domain
                            cutoff='prod',  # type of cutoff // 'prod' vs 'assim'
                            vapp='arome',  # type of application in operations namespace
                            vconf='3dvarfr',  # name of config in operation namespace
                            model='arome',  # name of the model, usually = vapp
                            namespace='oper.archive.fr',
                            block='forecast',
                            experiment='oper')

analysis_time = datetime(2019, 5, 1, 0)

for term in range(0, 25):
    resource_description = dict(
            **model_description,
            local=os.path.join(
                '/home/merzisenh/NO_SAVE/AROME/',
                get_filename('AROME', analysis_time, term)
                ),
            date= analysis_time, term=term)
    resource = usevortex.get_resources(getmode='epygram', **resource_description)




