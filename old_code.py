!/usr/bin/env python
# -*- coding: utf-8 -*-
#-----------------------
# latest changes :
#                * 2020/11/10 IG : - modify vconf to '3dvarfr' instead of 'france' after bascule on 2/06/2020
#                                  - modify namespace to 'vortex.archive.fr'
#                * 2021/04/27 IG : - modify namespace : 'vortex.archive.fr' prior to 2-7-2019, 'oper.meteo.fr' before. We now use datetime instead of bronx for dates in the main prep_forcing file-2 for consistency.
import epygram
import usevortex
import os,sys
from footprints import proxy as fpx
import copy
import matplotlib.pyplot as plt
import netCDF4
import datetime
import numpy as np
import numpy.ma as ma


def callSystemOrDie(commande,errorcode=None):
    status=os.system(commande)
    if status!=0:

        if type(errorcode) is int:
            print("The following command fails with error code "+str(status)+":\n"+commande)
            sys.exit(errorcode)
        else:
            sys.exit("The following command fails with error code "+str(status)+":\n"+commande)
#        raise BaseException("The following command fails with error code "+str(status)+":\n"+commande)
    return status

def extract_array(field,
                  first_i, last_i,
                  first_j, last_j):
    """
    Extract a rectangular sub-array from the field, given the i,j index limits
    of the sub-array, and return the extracted field.
    Written by A. Mary (GMAP)
    This function is depreciated and the method extract_subarray is now used
    (from Epygram 1.2.10)
    """

    # copy the geometry object and modify the grid parameters and dimensions
    geom_kwargs = copy.deepcopy(field.geometry._attributes)
    geom_kwargs.pop('dimensions')
    geom_kwargs['grid']['LAMzone'] = None
    coords_00 = field.geometry.ij2ll(first_i, first_j)
    geom_kwargs['grid']['input_position'] = (0,0)
    geom_kwargs['grid']['input_lon'] = epygram.util.Angle(coords_00[0], 'degrees')
    geom_kwargs['grid']['input_lat'] = epygram.util.Angle(coords_00[1], 'degrees')
    geom_kwargs['dimensions'] = {'X':last_i - first_i, 'Y':last_j - first_j}
    newgeom = fpx.geometry(**geom_kwargs)  # create new geometry object

    # select data
    subdata = field.getdata()[first_j:last_j, first_i:last_i]
    # copy the field object and set the new geometry, then data
    field_kwargs = copy.deepcopy(field._attributes)
    field_kwargs['geometry'] = newgeom
    field_kwargs.pop('data')
    newfield = fpx.field(**field_kwargs)
    newfield.setdata(subdata)

    return newfield

def extract_domain(field,domain):

   """
   Extract field over a specific area.
   The indexes correspond to the AROME 1.3 km grid.
   """

   if domain =='alp':
      first_i = 900
      last_i = 1075
      first_j = 525
      last_j = 750
   elif domain=='pyr':
      first_i = 480
      last_i = 785
      first_j = 350
      last_j = 475
   elif domain=='test_alp':
      first_i = 1090
      last_i = 1100
      first_j = 740
      last_j = 750
   elif domain=='jesus':
       first_i=551
       last_i=593
       first_j=414
       last_j=435

   fld_zoom = field.extract_subarray(first_i, last_i,
                        first_j, last_j)
   return (fld_zoom)


def save_in_nc(domain,champs,alti_zoom,ltair,date_beg,date_end):

   """
   Build a NetCDF forcing file using data fields read in AROME and MESCAN ICMSH files
   """

#Define name of variables in output file (dictionary between FA and NC)
   dict_FA2nc_tot = {'SURFTEMPERATURE':'ts','CLSTEMPERATURE':'Tair','S090TEMPERATURE':'T1',
                  'CLSHUMI.SPECIFIQ':'Qair','CLS_FF':'Wind','CLS_DD':'Wind_DIR',
                  'SURFPRESSION':'PSurf','SPECSURFGEOPOTEN':'ZS', 'SURFACCPLUIE':'Rainf',
                  'SURFACCNEIGE':'Snowf','SURFACCGRAUPEL':'Grauf','SURFRAYT THER DE':'LWdown',
                  'SURFRAYT SOLA DE':'SCA_SWdown','SURFRAYT DIR SUR':'DIR_SWdown','CLSVENT.ZONAL':'Wind',
                  'CLSU.RAF60M.XFU':'Wind_Gust','CLSVENT.MERIDIEN':'Wind_DIR',
                  'SURFPREC.ANA.EAU':'Rainf_ana','SURFPREC.ANA.NEI':'Snowf_ana'
                       }
# Name of forcing file
   forcing_file='FORCING_day_'+domain+'_'+date_beg.strftime("%Y%m%d%H")+'_'+date_end.strftime("%Y%m%d%H")+'.nc'
   output_resource = epygram.formats.resource(forcing_file, 'w', fmt='netCDF')  # on ouvre le netCDF de sortie en écriture
   # et on lui dit quel comportement on veut qu'il adopte (du point de vue conventions netCDF)
   output_resource.behave(N_dimension='Number_of_points',
                       X_dimension='xx',
                       Y_dimension='yy',
                       force_a_T_dimension=True
                       )

   #Add graupel to total snow accumulation and remove graupel from output
   champs['SURFACCNEIGE'].setdata(np.maximum(0.,champs['SURFACCNEIGE'].getdata()+champs['SURFACCGRAUPEL'].getdata()))
   del champs['SURFACCGRAUPEL']

   # Insure rain is positive
   champs['SURFACCPLUIE'].setdata(np.maximum(0.,champs['SURFACCPLUIE'].getdata()))

   #Compute diffuse component of incoming shortwave radiation
   # Difference between total and diffuse.
   champs['SURFRAYT SOLA DE'].setdata(np.maximum(0.,champs['SURFRAYT SOLA DE'].getdata()-champs['SURFRAYT DIR SUR'].getdata()))

   #Update surface pressure
   champs['SURFPRESSION'].operation('exp')

   #Compute wind direction and module from U and V
   vectwind=epygram.fields.make_vector_field(champs['CLSVENT.ZONAL'],champs['CLSVENT.MERIDIEN'])
   ff = vectwind.to_module()
   dd =  vectwind.compute_direction()
   champs['CLSVENT.ZONAL'].setdata(ff.getdata())
  # del champs['CLSVENT.MERIDIEN']
   champs['CLSVENT.MERIDIEN'].setdata(dd.getdata())
#
   #Compute gust module
   vectwind=epygram.fields.make_vector_field(champs['CLSU.RAF60M.XFU'],champs['CLSV.RAF60M.XFU'])
   ff = vectwind.to_module()
   champs['CLSU.RAF60M.XFU'].setdata(ff.getdata())
   del champs['CLSV.RAF60M.XFU']

   if ltair:
       # Temperature at 1st prognostic level is used instead of diagnostic level
       champs['CLSTEMPERATURE'].setdata(champs['S090TEMPERATURE'].getdata())
       champs['CLSHUMI.SPECIFIQ'].setdata(champs['S090HUMI.SPECIFI'].getdata())
   del champs['S090TEMPERATURE']
   del champs['S090HUMI.SPECIFI']

# Write all the fields in the NetCdf forcing file
   for fld in champs.values():
       fld.fid['netCDF'] = dict_FA2nc_tot[fld.fid['FA']]  # conversion de nom
       output_resource.writefield(fld)

# Add elevation
   f = netCDF4.Dataset(forcing_file,'r+')
   zs = f.createVariable('ZS','d',('yy','xx'))
   zs[:]=alti_zoom
                                                                                                                                                                                                                                                                                                                                                                                                                                                                       1,1           Top


# Add necessary data for SURFEX
callSystemOrDie("ncap2 -O -s 'FORC_TIME_STEP=3600.' " + forcing_file + " " + forcing_file)
callSystemOrDie("ncap2 -O -s 'CO2air=Tair*0. + 0.00062' " + forcing_file + " " + forcing_file)
#   callSystemOrDie("ncap2 -O -s 'Wind_DIR=Tair*0. + 0.' "+forcing_file+" "+forcing_file)
callSystemOrDie("ncap2 -O -s 'UREF=ZS*0. + 10.' " + forcing_file + " " + forcing_file)
callSystemOrDie("ncap2 -O -s 'ZREF=ZS*0. + 2.' " + forcing_file + " " + forcing_file)
callSystemOrDie(
    "ncap2 -O -s'slope=ZS*0.+0.;aspect=ZS*0.+0.;FRC_TIME_STP=FORC_TIME_STEP' " + forcing_file + " " + forcing_file)
callSystemOrDie("ncrename -O -v latitude,LAT " + forcing_file)
callSystemOrDie("ncrename -O -v longitude,LON " + forcing_file)
callSystemOrDie("ncks -O --mk_rec_dmn time " + forcing_file + " " + forcing_file)


def extract_day(date, liste_dom, ltair, lmescan, analysis_time, initialterm, finalterm, larome, ldrawplot):
    """
    Main routine to extract, process and write AROME and MESCAN required to build SURFEX forcing
    """

    date_beg = date + datetime.timedelta(hours=analysis_time + (initialterm + 1))
    date_end = date + datetime.timedelta(hours=analysis_time + finalterm)

    terms = range(initialterm, finalterm + 1)

    # Local name of dowloaded ICMSH files
    nom_temporaire_local = 'hist_arome_[term].fa'  # mais l'idée est qu'on n'a pas besoin de manipuler explicitement ce nom de fichier
    nom_temporaire_local_ana = 'hist_arome_ana.fa'  # mais l'idée est qu'on n'a pas besoin de manipuler explicitement ce nom de fichier


    champs_a_extraire = ['CLSTEMPERATURE', 'S090TEMPERATURE', 'CLSHUMI.SPECIFIQ', 'S090HUMI.SPECIFI', 'SURFPRESSION',
                         'CLSVENT.ZONAL', 'CLSVENT.MERIDIEN',
                         'CLSU.RAF60M.XFU', 'CLSV.RAF60M.XFU']
    champs_cum = ['SURFACCPLUIE', 'SURFACCNEIGE', 'SURFACCGRAUPEL', 'SURFRAYT THER DE', 'SURFRAYT SOLA DE',
                  'SURFRAYT DIR SUR']
    champs_cum_ana = ['SURFPREC.ANA.EAU', 'SURFPREC.ANA.NEI']

    namespace = 'oper.archive.fr'  # archive + local cache : le temps de mettre au point le script, C)vite de retransfC)rer les fichiers C  chaque fois
    if date_beg.date() > datetime.date(2019, 7,
                                       2):  # date codee en dur : elle correspond au moment ou la localisation des archives a change.
        namespace = 'vortex.archive.fr'  # the files we request are archived (on hendrix), coming from DSI suites
    namespace2 = 'olive.archive.fr'  # Name space for MESCAN experiment

    champs = {}
    champs_j = {}
    data_sto = {}
    alti_zoom = {}

    for dd in liste_dom:
        champs[dd] = {}
        champs_j[dd] = {}
        data_sto[dd] = {}

    if (lmescan):
        # Define resoucrce description
        # MESCAN experiment have carried out by Camille Birman
        # Contact her for my details on MESCAN experiments
        resource_description = dict(experiment='B6LR',  # oper suite
                                    kind='analysis',  # model state
                                    block='surfan',
                                    date=date + datetime.timedelta(hours=30),
                                    # Next day is used since the analysis is done between D-1 6 and D 6
                                    term=6,
                                    geometry='franmgsp',  # the name of the model domain
                                    local=nom_temporaire_local_ana,  # the local filename of the resource, once fetched.
                                    cutoff='assim',  # type of cutoff // 'prod' vs 'assim'
                                    vapp='arome',  # type of application in operations namespace
                                    vconf='france',  # name of config in operation namespace
                                    model='arome',  # name of the model, usually = vapp
                                    origin='canari',
                                    namespace=namespace2)

        r1 = \
        usevortex.get_resources(getmode='epygram',  # on veut récupérer l'objet epygram correspondant à la ressource
                                **resource_description)[0]

        for f in champs_cum_ana:
            print
            f
            fld = r1.readfield(f)  # lecture du champ

            for dd in liste_dom:
                fld_zoom = extract_domain(fld, dd)
                fld_dat = fld_zoom.getdata()
                fld_diff = fld_dat
                fld_zoom.setdata(fld_diff)
                champs_j[dd][fld_zoom.fid['FA']] = fld_zoom
                # Plot MESCAN variables
                if ldrawplot and f == 'SURFPREC.ANA.EAU':
                    fig, _ = fld_zoom.plotfield(colormap='gist_ncar_r', minmax_in_title=True)
                    fig.savefig('RR24_mescan_' + date_end.strftime("%Y%m%d%H") + '_' + dd + '.png')

        r1.close()  # on ferme la ressource
        os.remove(r1.container.abspath)  # et on supprime le fichier  local (temporaire)

    if (larome):
        for term in terms:  # boucle sur les échéances
            # description de la ressource
            resource_description = dict(suite='oper',  # oper suite
                                        kind='historic',  # model state
                                        date=date + datetime.timedelta(hours=analysis_time),
                                        # the initial date and time
                                        term=term,  # the forecast term
                                        geometry='franmgsp',  # the name of the model domain
                                        local=nom_temporaire_local,  # the local filename of the resource, once fetched.
                                        cutoff='prod',  # type of cutoff // 'prod' vs 'assim'
                                        vapp='arome',  # type of application in operations namespace
                                        vconf='3dvarfr',  # name of config in operation namespace
                                        model='arome',  # name of the model, usually = vapp
                                        namespace=namespace, block='forecast', experiment='oper')
            r = \
            usevortex.get_resources(getmode='epygram',  # on veut récupérer l'objet epygram correspondant à la ressource
                                    **resource_description)[0]

            # Read and store elevation
            if term == initialterm:
                fld = r.readfield('SPECSURFGEOPOTEN')
                if fld.spectral:
                    fld.sp2gp()
                for dd in liste_dom:
                    fld_zoom = extract_domain(fld, dd)
                    fld_zoom.validity = epygram.base.FieldValidity()
                    alti_zoom[dd] = fld_zoom.getdata() / 9.81

            # Treatment for cumulative field
            # Separate case initialterm=0 (no cumulative fluxes in 0 file) and initialterm>0
            for f in champs_cum:

                if (term == 0):
                    print 'Init from +00'
                else:
                    fld = r.readfield(f)  # lecture du champ

                for dd in liste_dom:

                    if (term == 0):
                        print 'Init from +00'
                    else:
                        fld_zoom = extract_domain(fld, dd)

                    if term == initialterm:
                        # Conversion: - from mm to kg/m2/s for precip
                        #              - from J/m2 to W/m2 for incoming LW and SW
                        if (initialterm > 0):
                            fld_dat = fld_zoom.getdata()
                            data_sto[dd][fld_zoom.fid['FA']] = fld_dat  # Stockage des donnes echeance precedente
                    else:
                        fld_dat = fld_zoom.getdata()
                        # Conversion: - from mm to kg/m2/s for precip
                        #              - from J/m2 to W/m2 for incoming LW and SW
                        if (term == 1):
                            fld_diff = fld_dat / 3600.
                        else:
                            fld_diff = (fld_dat - data_sto[dd][fld_zoom.fid['FA']]) / 3600.

                        fld_zoom.setdata(np.maximum(0., fld_diff))
                        if (term == initialterm + 1):
                            champs[dd][fld_zoom.fid['FA']] = fld_zoom
                        else:
                            champs[dd][fld_zoom.fid['FA']].extend(
                                fld_zoom)  # suivantes: on étend la dimension temporelle du champ

                        # Treatment for non-cumulative field (NOTA: wind gust field changes name over time in the FA files => add IG)

                    if (term > initialterm):
                        old_windgust_name = False
                        for f in champs_a_extraire:
                            if f == 'CLSU.RAF60M.XFU' and (f in r.listfields()) == False:
                                f = 'CLSU.RAF.MOD.XFU'
                                old_windgust_name = True
                            if f == 'CLSV.RAF60M.XFU' and (f in r.listfields()) == False:
                                f = 'CLSV.RAF.MOD.XFU'
                            fld = r.readfield(f)  # lecture du champ
                            fld.validity[0].get()
                            if fld.spectral:
                                fld.sp2gp()
                            for dd in liste_dom:
                                fld_zoom = extract_domain(fld, dd)
                                if term == initialterm + 1:
                                    champs[dd][fld_zoom.fid['FA']] = fld_zoom  # premiere échéance
                                else:
                                    champs[dd][fld_zoom.fid['FA']].extend(
                                        fld_zoom)  # suivantes: on étend la dimension temporelle du champ

                    r.close()  # on ferme la ressource
                    os.remove(r.container.abspath)  # et on supprime le fichier  local (temporaire)

                nterm = len(terms) - 1

                ######### Treatment for wind gusts // add IG
                if old_windgust_name:
                    for dd in liste_dom:
                        champs[dd]['CLSU.RAF60M.XFU'] = copy.deepcopy(champs[dd]['CLSU.RAF.MOD.XFU'])
                        champs[dd]['CLSV.RAF60M.XFU'] = copy.deepcopy(champs[dd]['CLSV.RAF.MOD.XFU'])
                        champs[dd]['CLSU.RAF60M.XFU'].fid['FA'] = 'CLSU.RAF60M.XFU'
                        champs[dd]['CLSV.RAF60M.XFU'].fid['FA'] = 'CLSV.RAF60M.XFU'
                        del champs[dd]['CLSU.RAF.MOD.XFU']
                        del champs[dd]['CLSV.RAF.MOD.XFU']

    ######### Treatment for precipitation data

        for dd in liste_dom:
            champs[dd]['SURFPREC.ANA.EAU'] = copy.deepcopy(champs[dd]['SURFACCPLUIE'])
            champs[dd]['SURFPREC.ANA.NEI'] = copy.deepcopy(champs[dd]['SURFACCNEIGE'])#+champs[dd]['SURFACCGRAUPEL']
            champs[dd]['SURFPREC.ANA.EAU'].fid['FA'] = 'SURFPREC.ANA.EAU'
            champs[dd]['SURFPREC.ANA.NEI'].fid['FA'] = 'SURFPREC.ANA.NEI'
            rr_aro = champs[dd]['SURFACCPLUIE'].getdata()
            sn_aro = champs[dd]['SURFACCGRAUPEL'].getdata()+champs[dd]['SURFACCNEIGE'].getdata()


            # MESCAN is not used: Snowf_Ana=Snowf_forecast and Rnowf_Ana=Rnowf_forecast
            champs[dd]['SURFPREC.ANA.EAU'].setdata(rr_aro)
            champs[dd]['SURFPREC.ANA.NEI'].setdata(sn_aro)


        # Built NetCDF file for each domain
        for dd in liste_dom:
            print 'save in nc: ',dd
            save_in_nc(dd,champs[dd],alti_zoom[dd],ltair,date_beg,date_end)

