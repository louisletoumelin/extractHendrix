import numpy as np


def compute_temperature_in_degree_c(read_cache, date, term, native_variable):
    return read_cache(date, term, native_variable) - 273.15


def compute_wind_speed(read_cache, date, term, name_u_component, name_v_component):
    u = read_cache(date, term, name_u_component)
    v = read_cache(date, term, name_v_component)
    return np.sqrt(u**2 + v**2)
