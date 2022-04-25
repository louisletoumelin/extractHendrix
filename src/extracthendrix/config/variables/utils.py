class Variable:

    def __init__(self, native_vars=None, compute=None, original_long_name=None, name=None):
        self.native_vars = native_vars
        self.compute = compute
        self.original_long_name = original_long_name
        self.name = name


class NativeVariable:

    def __init__(self, model_name=None, name=None):
        self.model_name = model_name
        self.name = name
