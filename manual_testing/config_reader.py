from extracthendrix.config.example_config_user import config_user
from extracthendrix.configreader import apply_config_user


# renvoie un dataset xarray avec toutes les variables calculées et concaténées selon la dimension temps
xx = apply_config_user(config_user)
