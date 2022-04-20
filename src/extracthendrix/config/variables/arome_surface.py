class Variables:
    model_name = 'AROME_SURFACE'

    def __init__(self, variables=None, compute=None, original_long_name=None, name=None):
        self.variables = variables
        self.compute = compute
        self.original_long_name = original_long_name
        self.name = name


SWE = Variables(
    variables=['X001WSN_VEG1'],
    compute=None,
    original_long_name="contenu équivalent en eau de la neige [km m-2]",
    name='SWE'
)
