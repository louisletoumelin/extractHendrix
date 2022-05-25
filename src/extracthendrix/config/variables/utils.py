class Variable:

    def __init__(self, native_vars=None, compute=None, original_long_name=None, name=None, outname=None,
                 units=None):
        self.native_vars = native_vars
        self.compute = compute
        self.original_long_name = original_long_name
        self.units = units
        self.name = name
        if outname:
            self.outname = outname
        else:
            self.outname = name


class NativeVariable:

    def __init__(self, model_name=None, name=None, outname=None):
        self.model_name = model_name
        self.name = name
        if outname:
            self.outname = outname
        else:
            self.outname = name
