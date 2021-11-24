import usevortex

def select_namespace():
    # todo clean this implementation, it is now a direct copy/past from old code
    namespace =  'oper.archive.fr'  # archive + local cache : le temps de mettre au point le script, C)vite de retransfC)rer les fichiers C  chaque fois
    #IG++
    if date_beg.date() > datetime.date(2019,7,2): # date codee en dur : elle correspond au moment ou la localisation des archives a change.
        #print('date > 2 juil 2019\n')
        #print(date_beg)
        namespace = 'vortex.archive.fr'  # the files we request are archived (on hendrix), coming from DSI suites
        #print('ISA check namespace\n')
        #print(namespace)
    #IG--
    namespace2 = 'olive.archive.fr' # Name space for MESCAN experiment


def check_if_files_are_already_downloaded_at_CEN():
    #todo implement this function
    pass


def send_a_mail_if_extraction_stopped():
    #todo implement this function
    pass


def select_domain_by_lat_lon():
    # todo implement this function usig epygram function
    pass


def prepare_prestaggging_demand_mail(dates, terms, domain, *args):
    #todo implement this function. I am not sure about the arguments.
    #todo we need to know all the paths to all the files on hendrix
    #todo Also look at get_ressource method and its option prestaging
    #http://www.umr-cnrm.fr/gmapdoc/meshtml/EPYGRAM1.4.3/_modules/usevortex.html#get_resources
    resource_descriptions = [dict(suite='oper',  # oper suite
                                kind='historic',  # model state
                                date=date + datetime.timedelta(hours=analysis_time),
                                # the initial date and time
                                term=term,  # the forecast term
                                geometry='franmgsp',  # the name of the model domain
                                local=nom_temporaire_local,  # the local filename of the resource, once fetched.
                                cutoff='prod',  # type of cutoff // 'prod' vs 'assim'
                                vapp='arome',  # type of application in operations namespace
                                vconf='3dvarfr',  # name of config in operation namespace
                                model='arome',  # name of the model, usually = vapp
                                namespace=namespace, block='forecast', experiment='oper')]

    for ressource in resource_descriptions:
        r = usevortex.get_resources(getmode='locate', **ressource)[0]
        print(r)

"""
    def get_gribfc_arome_oper(date, term, geometry='FRANGP0025', **others):
        #Proxy for AROME oper GRIBs.

        _others = dict(suite='oper',
                       model='arome',
                       cutoff='prod',
                       vapp='arome',
                       vconf='france',
                       origin='hst',
                       kind='gridpoint',
                       nativefmt='grib')
        _others.update(others)
        return get_resources(date=date, term=term, geometry=geometry,
                             **_others)
"""