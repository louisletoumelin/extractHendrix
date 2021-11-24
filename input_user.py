# Input from the user could look like that (I would prefer key/value architecture, it is easier to understand)
"""
01/01/2018                                  # begin
02/01/2018                                  # end
"alp"                                       # domain or lat/lon
0                                           # analysis hour
6                                           # first term
Tair                                        # variable to extract n1
T1                                          # variable to extract n2
Wind                                        # variable to extract n3
ZS                                          # variable to extract n4
Rainf                                       # variable to extract n5
louis.letoumelin@meteo.fr                   # to send a mail if it bugs
True                                        # prepare prestagging mail
"""

def _get_terms_from_input_user():
    """
    Input = config file from user
    Output = tuple(initial_term, list of terms)
    """
    # todo implement this function
    pass


def _get_domain_from_input_user():
    """
    Input: user file
    Output: domain
    """
    # todo implement this function
    pass


def _get_dates_of_simulation_from_input_user():
    """
    Input: user file
    Output: dates
    """
    # todo implement this function
    pass


def _get_variable_to_extract_from_input_user():
    """
    Input: user file
    Output: list of variables
    """
    # todo implement this function
    pass


def get_vortex_ressource():
    """This function search for existing ressource description and get it using epygram.
    It hould return a vortex ressource (not an array)"""
    # todo implement this function

    # todo We should also create a dictionnary containing different ressources descriptions
    # for different extraction case (AROME or AROME500m)
    resource_description = dict(experiment='B6LR',  # oper suite
                                kind='analysis',  # model state
                                block='surfan',
                                date=date + datetime.timedelta(hours=30),
                                # Next day is used since the analysis is done between D-1 6 and D 6
                                term=6,
                                geometry='franmgsp',  # the name of the model domain
                                local=nom_temporaire_local_ana,  # the local filename of the resource, once fetched.
                                cutoff='assim',  # type of cutoff // 'prod' vs 'assim'
                                vapp='arome',  # type of application in operations namespace
                                vconf='france',  # name of config in operation namespace
                                model='arome',  # name of the model, usually = vapp
                                origin='canari',
                                namespace=namespace2)

    r1 = \
        usevortex.get_resources(getmode='epygram',  # on veut récupérer l'objet epygram correspondant à la ressource
                                **resource_description)[0]
    pass


def get_input_user():
    """wrapper of all _get functions"""
    dates = _get_dates_of_simulation_from_input_user()
    initial_term, terms = _get_terms_from_input_user()
    domain = _get_domain_from_input_user()
    variables_to_extract = _get_variable_to_extract_from_input_user()

    return dates, initial_term, domain, variables_to_extract
