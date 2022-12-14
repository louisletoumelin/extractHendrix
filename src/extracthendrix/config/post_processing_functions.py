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
    delta = read_dict(dict_data, term, name_variable_FA) - read_dict(dict_data, term-1, name_variable_FA)
    return delta / time_delta


def compute_decumul_and_negative(dict_data, term, name_variable_FA, time_delta=3600, **kwargs):
    delta = read_dict(dict_data, term, name_variable_FA) - read_dict(dict_data, term-1, name_variable_FA)
    return -delta / time_delta


def compute_psurf(dict_data, term, name_variable_FA, **kwargs):
    return np.exp(read_dict(dict_data, term, name_variable_FA))


def compute_temperature_in_degree_c(dict_data, term, name_variable_FA, **kwargs):
    return read_dict(dict_data, term, name_variable_FA) - 273.15


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


def compute_decumul_and_diff(dict_data, term, name_1, name_2, **kwargs):
    var1 = compute_decumul(dict_data, term, name_1)
    var2 = compute_decumul(dict_data, term, name_2)
    return var1 - var2


def compute_latent_heat_flux(dict_data, term, name_evaporation_FA, name_sublimation_FA, **kwargs):
    evaporation = compute_decumul(dict_data, term, name_evaporation_FA)
    sublimation = compute_decumul(dict_data, term, name_sublimation_FA)
    return -(evaporation + sublimation)


def compute_sum_all_water_species(dict_data, term, name_droplet, name_ice, name_snow, name_rain, **kwargs):
    droplet = read_dict(dict_data, term, name_droplet)
    ice = read_dict(dict_data, term, name_ice)
    snow = read_dict(dict_data, term, name_snow)
    rain = read_dict(dict_data, term, name_rain)

    return droplet + ice + snow + rain


def compute_multiply_by_100(dict_data, term, name_variable_FA, **kwargs):
    return 100*read_dict(dict_data, term, name_variable_FA)
