"""all codes related with netcdf goes here"""

def init_daily_netcdf_file():
    forcing_file = 'FORCING_day_' + domain + '_' + date_beg.strftime("%Y%m%d%H") + '_' + date_end.strftime(
        "%Y%m%d%H") + '.nc'
    output_resource = epygram.formats.resource(forcing_file, 'w',
                                               fmt='netCDF')  # on ouvre le netCDF de sortie en écriture
    # et on lui dit quel comportement on veut qu'il adopte (du point de vue conventions netCDF)
    output_resource.behave(N_dimension='Number_of_points',
                           X_dimension='xx',
                           Y_dimension='yy',
                           force_a_T_dimension=True
                           )

def add_hourly_array_to_netcdf():
    """
    This function takes an array and add it to a netcdf file. If the variable already exists, it appends the array
    to the time dimension
    """

    pass


def concatenate_final_netcdf():
    #todo implement this function
    pass


def create_first_hour_netcdf():
    #todo implement this function
    pass


def add_SURFEX_metadata_to_nc():
    # todo implement the function
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
    pass


def create_daily_netcdf():
    #todo implement this function
    pass
