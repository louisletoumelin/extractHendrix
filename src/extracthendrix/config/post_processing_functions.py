"""
Functions used to process each model variable
"""

# Global imports
import numpy as np


def read_dict(dict_data, term, variable):
    """Read dictionary"""
    return dict_data[term][variable]


def compute_decumul(dict_data, term, name_variable_FA, time_delta=3600, **kwargs):
    """
    Calcule le décumul pour l'échéance term

    # Conversion: - from mm to kg/m2/s for precip
    #              - from J/m2 to W/m2 for incoming LW and SW

    """
    delta = read_dict(dict_data, term, name_variable_FA) - read_dict(dict_data, term -1, name_variable_FA)
    return delta / time_delta


def compute_psurf(dict_data, term, name_variable_FA, **kwargs):
    return np.exp(read_dict(dict_data, term, name_variable_FA))


def compute_wind_speed(dict_data, term, name_u_component_fa, name_v_component_fa, **kwargs):

    u = read_dict(dict_data, term, name_u_component_fa)
    v = read_dict(dict_data, term, name_v_component_fa)

    return np.sqrt(u**2 + v**2)


def compute_wind_direction(dict_data, term, name_u_component_fa, name_v_component_fa, **kwargs):

    u = read_dict(dict_data, term, name_u_component_fa)
    v = read_dict(dict_data, term, name_v_component_fa)

    return np.mod(180 + np.rad2deg(np.arctan2(u, v)), 360)


def compute_zs(dict_data, term, name_variable_FA, **kwargs):
    return read_dict(dict_data, term, name_variable_FA) / 9.81


def compute_snowfall(dict_data, term, name_snow_FA, name_graupel_FA, **kwargs):
    snow = compute_decumul(dict_data, term, name_snow_FA)
    graupel = compute_decumul(dict_data, term, name_graupel_FA)
    return snow + graupel


def compute_SCA_SWdown(dict_data, term, name_surfrayt_sola_de_FA, name_surfrayt_dir_sur_FA, **kwargs):
    surfrayt_sola_de = compute_decumul(dict_data, term, name_surfrayt_sola_de_FA)
    name_surfrayt_dir_sur = compute_decumul(dict_data, term, name_surfrayt_dir_sur_FA)
    return surfrayt_sola_de - name_surfrayt_dir_sur
