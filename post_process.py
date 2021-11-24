"""
Functions used to process each AROME variable
"""
# Global imports
import numpy as np

# Local imports
import epygram


def default(vortex_ressource, name_fa, domain, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    field = vortex_ressource.readfield(name_fa)
    field = extract_domain(field, domain)
    return field.get_data()


def _select_name_wind_gust(new_name_u, new_name_v, old_name_u, old_name_v, list_variables):
    """
    Select the appropriate wind gust name for FA files (because it changes with time)

    Parameters
    ----------
    new_name_u : str
        new name for wind gust (u component)
    new_name_v : str
        new name for wind gust (v component)
    old_name_u : str
        old name for wind gust (u component)
    old_name_v : str
        old name for wind gust (v component)
    list_variables : list
        list of all FA variables in vortex ressource

    Returns
    -------
    u_name : str
        name of wind gust variable in current vortex ressource (u component)
    v_name : str
        name of wind gust variable in current vortex ressource (v component)

    Raises
    ------
    AttributeError
        when no wind_gust name is found
    """
    if (new_name_u in list_variables) and (new_name_v in list_variables):
        u_name = new_name_u
        v_name = new_name_v
    elif (old_name_u in list_variables) and (old_name_v in list_variables):
        u_name = old_name_u
        v_name = old_name_v
    else:
        raise AttributeError(f"Wind gust name not found in FA fields."
                             f"New names: {new_name_u}, {new_name_v}"
                             f"Old names: {old_name_u}, {old_name_v}")
    return u_name, v_name


def wind_gust(vortex_ressource, new_name_u, new_name_v, old_name_u, old_name_v, domain, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    list_variables = vortex_ressource.listfields()
    u_name, v_name = _select_name_wind_gust(new_name_u, new_name_v, old_name_u, old_name_v, list_variables)

    u_gust = vortex_ressource.readfield(u_name)
    v_gust = vortex_ressource.readfield(v_name)

    # I don't know why we do this but we have to do this
    # todo wrap this in a function
    u_gust.validity[0].get()
    v_gust.validity[0].get()
    for variable in [u_gust, v_gust]:
        if variable.spectral:
            variable.sp2gp()

    u_gust = extract_domain(u_gust, domain)
    v_gust = extract_domain(v_gust, domain)

    vectwind = epygram.fields.make_vector_field(u_gust, v_gust)
    wind_gust = vectwind.to_module().get_data()

    return wind_gust


def wind_speed_from_components(vortex_ressource, name_u, name_v, domain, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    u = vortex_ressource.readfield(name_u)
    v = vortex_ressource.readfield(name_v)

    # I don't know why we do this but we have to do this
    # todo wrap this in a function
    u.validity[0].get()
    v.validity[0].get()
    for variable in [u, v]:
        if variable.spectral:
            variable.sp2gp()

    u = extract_domain(u, domain)
    v = extract_domain(v, domain)

    # todo this operation is replicated for wind direction, maybe merge it
    wind_vector = epygram.fields.make_vector_field(u, v)
    wind_speed = wind_vector.to_module().get_data()
    #wind_direction = wind_vector.compute_direction().get_data()

    return wind_speed


def wind_direction_from_components(vortex_ressource, name_u, name_v, domain, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    u = vortex_ressource.readfield(name_u)
    v = vortex_ressource.readfield(name_v)

    # I don't know why we do this but we have to do this
    # todo wrap this in a function
    u.validity[0].get()
    v.validity[0].get()
    for variable in [u, v]:
        if variable.spectral:
            variable.sp2gp()

    u = extract_domain(u, domain)
    v = extract_domain(v, domain)

    # todo this operation is replicated for wind direction, maybe merge it
    wind_vector = epygram.fields.make_vector_field(u, v)
    wind_direction = wind_vector.compute_direction().get_data()

    return wind_direction


def Psurf(vortex_ressource, name_fa, domain, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    field = vortex_ressource.readfield(name_fa)
    field = extract_domain(field, domain)
    field = field.operation('exp')
    return field.get_data()


def zs(vortex_ressource, name_fa, domain, term=None, inital_term=None, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array

    We only extract zs at a single term
    """
    if term == inital_term:
        zs = vortex_ressource.readfield(name_fa)

        if zs.spectral:
            zs.sp2gp()

        zs = extract_domain(zs, domain)
        zs.validity = epygram.base.FieldValidity()
        return zs.getdata() / 9.81


def cumul(vortex_ressource, name_fa, domain, term=None, initial_term=None, stored_data=None, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    if term > 0:
        field = vortex_ressource.readfield(name_fa)
        field = extract_domain(field, domain)

        array = field.getdata()

        # store cumulative data
        stored_data[domain][name_fa] = array

        if term != initial_term:
            # Conversion: - from mm to kg/m2/s for precip
            #              - from J/m2 to W/m2 for incoming LW and SW
            array = (array - 0) / 3600 if term == 1 else (array - stored_data[domain][name_fa]) / 3600
            array = np.maximum(0, array, dtype=np.float64)
            return array
        else:
            # todo it's weird, we don't store cumulative data during initial term (Isabelle neither)
            # todo: Hugo, maybe there is a bug here in Isabelle code (or I didn't understand it)
            print("Term==initial term: no cumulative data (not sure about that)")
    else:
        print("Term==0: no cumulative data")


def cumul_snow_graupel(vortex_ressource, name_fa_snow, name_fa_graupel, domain,
                       term=None, initial_term=None, stored_data=None, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    snow = cumul(vortex_ressource, name_fa_snow, domain,
                 term=term, initial_term=initial_term, stored_data=stored_data, **kwargs)
    graupel = cumul(vortex_ressource, name_fa_graupel, domain,
                    term=term, initial_term=initial_term, stored_data=stored_data, **kwargs)

    return snow + graupel


def SCA_SWdown(vortex_ressource, name_fa_surfrayt_sola_de, name_fa_surfrayt_dir_sur, domain,
               term=None, initial_term=None, stored_data=None, **kwargs):
    """
    Input: vortex ressource
    Output: numpy array
    """
    surfrayt_sola_de = cumul(vortex_ressource, name_fa_surfrayt_sola_de, domain,
                             term=term, initial_term=initial_term, stored_data=stored_data, **kwargs)
    surfrayt_dir_sur = cumul(vortex_ressource, name_fa_surfrayt_dir_sur, domain,
                             term=term, initial_term=initial_term, stored_data=stored_data, **kwargs)

    return surfrayt_sola_de - surfrayt_dir_sur



