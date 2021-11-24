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
    pass
