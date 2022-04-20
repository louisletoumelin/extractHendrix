from extracthendrix.config.post_proc_functions_new import compute_temperature_in_degree_c, compute_wind_speed


class Variables:
    model_name = 'AROME'

    def __init__(self, variables=None, compute=None, original_long_name=None, name=None):
        self.variables = variables
        self.compute = compute
        self.original_long_name = original_long_name
        self.name = name

    def __repr__(self):
        return "%s:%s" % (self.model_name, self.original_long_name)


Tair = Variables(
    variables=['CLSTEMPERATURE'],
    compute=compute_temperature_in_degree_c,
    original_long_name="2 m Temperature",
    name="Tair"
)

T1 = Variables(
    variables=['S090TEMPERATURE'],
    compute=compute_temperature_in_degree_c,
    original_long_name="Prognostic lowest level temperature",
    name="T1"
)

Wind = Variables(
    variables=['CLSVENT.ZONAL', 'CLSVENT.MERIDIEN'],
    compute=compute_wind_speed,
    original_long_name="10 m wind speed",
    name="Wind")

ts = Variables(
    variables=['SURFTEMPERATURE'],
    compute=None,
    original_long_name="Surface temperature. Ts (the one used in radiation)",
    name='ts'
)
