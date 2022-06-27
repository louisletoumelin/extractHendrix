import numpy as np
from bronx.meteo.thermo import Thermo


def copy(read_cache, date, term, domain, native_variable):
    return read_cache(date, term, domain, native_variable)


def compute_temperature_in_degree_c(read_cache, date, term, domain, native_variable):
    """
    convert absolute temperature to degrees C.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param native_variable: temperature in K
    :return: temperature in degrees C
    """
    return read_cache(date, term, domain, native_variable) - 273.15


def compute_decumul(read_cache, date, term, domain, native_variable):
    """
    convert absolute temperature to degrees C.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param native_variable: temperature in K
    :return: temperature in degrees C
    """
    return read_cache(date, term, domain, native_variable) - read_cache(date, term-1, domain, native_variable)


def compute_t_r_p2qv(read_cache, date, term, domain, temperature, rh, pressure):
    """
    Calculate specific humidity (liquid phase only) from temperature, relative humidity and air pressure.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param temperature: air temperature (K)
    :param rh: relative humidity (%)
    :param pressure: air pressure (Pa)
    :return: specific humidity (kg/kg)
    """
    t = read_cache(date, term, domain, temperature)
    r = read_cache(date, term, domain, rh)
    p = read_cache(date, term, domain, pressure)
    esat = Thermo.T_phase2esat(t, 'W')
    e = Thermo.Huw_esatw2e(r, esat)
    qv = Thermo.e_P_qliquid_qice2qv(e, p, 0, 0)
    return qv


def compute_wind_speed(read_cache, date, term, domain, name_u_component, name_v_component):
    """
    compute wind speed from u component and v component of wind.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param name_u_component: u component of wind
    :param name_v_component: v component of wind
    :return: wind speed
    """
    u = read_cache(date, term, domain, name_u_component)
    v = read_cache(date, term, domain, name_v_component)
    return np.sqrt(u**2 + v**2)


def compute_wind_direction(read_cache, date, term, domain, name_u_component, name_v_component):
    """
    compute wind direction in degrees from u component and v component of wind.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param name_u_component: u component of wind
    :param name_v_component: v component of wind
    :return: wind direction
    """
    u = read_cache(date, term, name_u_component)
    v = read_cache(date, term, name_v_component)
    return np.mod(180 + np.rad2deg(np.arctan2(u, v)), 360)


def sum_solid_prec(read_cache, date, term, domain, snow, graupel, hail):
    """
    calculate sum of solid precipitation rates as the sum of snow graupel and hail.
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param snow: snow precipitation rate
    :param graupel: graupel precipitation rate
    :param hail: hail precipitation rate
    :return: total solid precipitation rate
    """
    s = read_cache(date, term, domain, snow)
    g = read_cache(date, term, domain, graupel)
    h = read_cache(date, term, domain, hail)
    return s+g+h


def percent2fraction(read_cache, date, term, domain, var):
    """
    convert percent to fraction (value between 0 and 1)
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param var: variable in %
    :return: variable expressed as fraction (var/100.)
    """
    percent = read_cache(date, term, domain, var)
    return percent/100.


def joule2watt_hourly(read_cache, date, term, domain, var):
    """
    convert joule/m2 to Watt/m2 for hourly time step (3600s)
    :param read_cache: read cache method from cache manager
    :param date: analysis date
    :param term: forecast term
    :param var: variable in Joules/m2
    :return: variable in Watt/m2
    """
    rad = read_cache(date, term, domain, var)
    return rad/3600.
