import usevortex
from datetime import datetime
import epygram


# exemple de paramètres valides pour une extraction AROME
params_arome = {
    'vapp': 'arome',
    'suite': 'oper',
    'experiment': 'oper',
    'cutoff': 'prod',
    'kind': 'historic',
    'geometry': 'franmgsp',
    'vconf': '3dvarfr',
    'model': 'arome',
    'namespace': 'vortex.archive.fr',
    'block': 'forecast',
    'date': datetime(2022, 4, 5, 0, 0),
    'term': 6,
    'local': '/home/merzisenh/NO_SAVE/extracthendrix/_native_files_/AROME-run:20220405T00:00:00Z-term:3h.FA'}

output_vortex = usevortex.get_resources(getmode='epygram', **params_arome)

# après qu'il a fini, on peut aller chercher la ressource en local
# on se demande à quoi ça sert on reçoit un filepath en réponse...
output_fetch_vortex = usevortex.get_resources(getmode='fetch', **params_arome)

# il vaut mieux utiliser directement epygram on obtient le même objet qu'en
# qu'avec getmode=epygram
output_epygram = epygram.formats.resource(
    filename=params_arome['local'], openmode='r', fmt='FA')
