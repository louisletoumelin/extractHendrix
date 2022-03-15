listchamp=['CLSTEMPERATURE','S090TEMPERATURE','S089TEMPERATURE',
           'S088TEMPERATURE','CLSVENT.ZONAL','CLSVENT.MERIDIEN',
           'CLSHUMI.RELATIVE','CLSHUMI.SPECIFIQ','CLSU.RAF60M.XFU',
           'CLSV.RAF60M.XFU',
           'SURFFLU.CHA.SENS','SURFFLU.LAT.MEVA','SURFFLU.LAT.MSUB',
           'SURFRAYT SOLA DE','SURFRAYT THER DE',
           'SURFFLU.RAY.THER','SURFFLU.RAY.SOLA',
           'SURFRAYT DIR SUR','SURFTENS.TURB.ZO','SURFTENS.TURB.ME',
           'SURFACCPLUIE','SURFACCNEIGE','SURFACCGRAUPEL','SURFDIAGHAIL',
           'ATMONEBUL.BASSE','ATMONEBUL.MOYENN','ATMONEBUL.HAUTE',
           'SURFTEMPERATURE','SURFRESERV.NEIGE','CLPMHAUT.MOD.XFU']

listchampcum=['SURFFLU.CHA.SENS','SURFFLU.LAT.MEVA','SURFFLU.LAT.MSUB',
              'SURFRAYT SOLA DE','SURFRAYT THER DE','SURFFLU.RAY.THER',
              'SURFFLU.RAY.SOLA','SURFRAYT DIR SUR','SURFTENS.TURB.ZO',
              'SURFTENS.TURB.ME','SURFACCPLUIE','SURFACCNEIGE',
              'SURFACCGRAUPEL','ATMONEBUL.BASSE','ATMONEBUL.MOYENN',
              'ATMONEBUL.HAUTE']

dat = int(dict['date'][hh] / 10000.)
t2m = dict['CLSTEMPERATURE'][i, hh] - 273.15
aa = (dict['S089TEMPERATURE'][i, hh] - dict['S090TEMPERATURE'][i, hh]) / 11.76  # 16.76-5.m
bb = dict['S090TEMPERATURE'][i, hh] - 5 * aa
t10m = 10 * aa + bb - 273.15  # interpolation lineaire entre 16.76m et 5m
hu2m = (dict['CLSHUMI.RELATIVE'][i, hh]) * 100.
q2m = (dict['CLSHUMI.SPECIFIQ'][i, hh])
ff10m = ((dict['CLSVENT.ZONAL'][i, hh]) ** 2 + (dict['CLSVENT.MERIDIEN'][i, hh]) ** 2) ** 0.5
dd10m = math.degrees(math.atan2(dict['CLSVENT.ZONAL'][i, hh], dict['CLSVENT.MERIDIEN'][i, hh])) + 180.
swd = dict['SURFRAYT SOLA DE'][i, hh] / 3600.
lwu = (dict['SURFRAYT THER DE'][i, hh] - dict['SURFFLU.RAY.THER'][i, hh]) / 3600.
h = -1 * dict['SURFFLU.CHA.SENS'][i, hh] / 3600.
le = -1 * (dict['SURFFLU.LAT.MEVA'][i, hh] + dict['SURFFLU.LAT.MSUB'][i, hh]) / 3600.

fmu = (((dict['SURFTENS.TURB.ZO'][i, hh]) ** 2 + (dict['SURFTENS.TURB.ME'][i, hh]) ** 2) ** 0.5) / 3600.
lwd = dict['SURFRAYT THER DE'][i, hh] / 3600.
swu = (dict['SURFRAYT SOLA DE'][i, hh] - dict['SURFFLU.RAY.SOLA'][i, hh]) / 3600.
swdiff = (dict['SURFRAYT SOLA DE'][i, hh] - dict['SURFRAYT DIR SUR'][i, hh]) / 3600.

t90 = dict['S090TEMPERATURE'][i, hh] - 273.15
t89 = dict['S089TEMPERATURE'][i, hh] - 273.15
t88 = dict['S088TEMPERATURE'][i, hh] - 273.15
ffraf = ((dict['CLSU.RAF60M.XFU'][i, hh]) ** 2 + (dict['CLSV.RAF60M.XFU'][i, hh]) ** 2) ** 0.5

rr = dict['SURFACCPLUIE'][i, hh]
rs = dict['SURFACCNEIGE'][i, hh]
rg = dict['SURFACCGRAUPEL'][i, hh]
diagh = dict['SURFDIAGHAIL'][i, hh]

nebb = dict['ATMONEBUL.BASSE'][i, hh] / 3600.
nebm = dict['ATMONEBUL.MOYENN'][i, hh] / 3600.
nebh = dict['ATMONEBUL.HAUTE'][i, hh] / 3600.

ts = dict['SURFTEMPERATURE'][i, hh] - 273.15
snow = dict['SURFRESERV.NEIGE'][i, hh]
clph = dict['CLPMHAUT.MOD.XFU'][i, hh]

# to get point
#listlon=[1.374, 14.124, 4.927, 2.208, 2.1948, -0.692, 4.407, -5.783, 0.37, 5.7553, 6.1098, 6.975, 6.17]
#listlat=[43.575, 52.167, 51.971, 48.713, 48.71, 44.832, 43.858, 41.816, 43.128, 45.2810, 45.1281, 45.968, 45.174]
#listname=['TLSE', 'LIND', 'CABA', 'PALA', 'PALA1', 'BORD', 'NIME', 'VALL', 'LANN', 'COLP', 'LACB', 'ARGE', 'STSO']
dict[listchamp[ch]][i, hh] = field.getvalue_ll(listlon[i], listlat[i])
