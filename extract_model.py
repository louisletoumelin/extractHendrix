#Version 2
name_nc  = {
               'rayonnement':
    dict(fields_required = ['SURFRAYT SOLA DE', 'SURFRAYT DIR SUR'],
    compute =  difference),

    'wind_gust':
    dict(
        fields_required = ['NEW.NAME.COMPLEX', 'OLD.NAME.COMPLEX'], # Il y a deux noms pour les rafales
        compute =  check_name_for_wind_gust),

    dict(name_nc = 'temperature',
         fields_required =['NOM.VACHEMENT.COMPLIQUE']),

    'temp':
    dict(fields_required=['NOM.TEMP'],  # Il y a deux noms pour les rafales
         compute=postprocess_default),

}


for index, term in enumerate(terms):
    for name,infos in name_nc.items():
        final[name] = infos['compute'](vortexreader_readfield, *infos[fields_required], index)


def difference(vortexreader_readfield, var1, var2):
    vortexreader_readfield(var1).get_data() - vortexreader_readfield(var2).get_data()

def cumul(vortexreader, var1):
    vortexreader.readfield(var1).get_data()/3600

def postprocess_default(name_nc, fields_required):
    return vortexreader.readfield(name_fa) # + changement de nom



# Utilisateur: rentre

01/01/2018
02/01/2018
temp, diagnostic
humidity, prognostic
rayonnement,
vent

# TODO: fonction de lecture Vortex
# lire tous les fields_required dans name_nc -> names_fa
# data_from_vortex =  {}
# for name in names_fa:
#      data[name] = vortex.readfield(var1)

# for name in name_nc:
#     final_array = name_nc[compute].get_data()(data, *fields_required)


# fonctions :

# lecture d'un champ FA (argument: nom_fa) (et le mapping pour field_alternate)

# transformation des champs FA en champs finaux

