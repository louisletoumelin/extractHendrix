import xarray as xr


def dataConcatenator(dateiterator, cacheManager):
    variables = cacheManager.variables
    variables_labelled_with_time = {variable: [] for variable in variables}
    for date_, term in dateiterator:
        for variable in variables:
            variables_labelled_with_time[variable].append(
                cacheManager.read_cache(date_, term, variable)
            )
    final_dataset = xr.Dataset(
        {
            variable: xr.concat(variable_values, "time")
            for variable, variable_values in variables_labelled_with_time.items()
        }
    )
    return final_dataset


# pour obtenir le netcdf
# final_dataset.to_netcdf(finalfilepath)
