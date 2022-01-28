from datetime import datetime, timedelta
from extracthendrix.core import HendrixConductor
from extracthendrix.config.config_fa2nc import transformations, domains
import os
import epygram



def get_resource_locally(analysis_time, model_name, term, workdir=None):
    fa_folder = '/home/merzisenh/NO_SAVE/AROME'
    analysis_time_str = analysis_time.strftime('%Y-%m-%d-%Hh')
    filename = os.path.join(fa_folder, "%s_ana:%s_step:%s"%(model_name, analysis_time_str, term))
    return epygram.formats.resource(filename=filename, openmode='r')


conductor = HendrixConductor(
        folder='/home/merzisenh/NO_SAVE',
        getter=get_resource_locally,
        model_name='AROME',
        analysis_time=datetime(2019,5,1,0),
        domain=domains['alp'],
        variables_nc = ['Tair','Wind']
        )

for term in range(1,12):
    conductor._epygram2netcdf(term)
data = conductor.readDataFromCache(2,10)


