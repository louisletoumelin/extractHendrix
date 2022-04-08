import xarray as xr


def dataConcatenator(dates, terms, cacheManager):
    variables = cacheManager.variables
    variables_labelled_with_time = {variable: [] for variable in variables}
    for date_ in dates:
        for term in terms:
            for variable in variables:
                with cacheManager.read_cache(date_, term, variable) as dataset:
                    variables_labelled_with_time[variable].append(dataset)
    final_dataset = xr.Dataset(
        {
            variable: xr.concat(variable_values, "time")[variable]
            for variable, variable_values in variables_labelled_with_time.items()
        }
    )
    return final_dataset


# pour obtenir le netcdf
# final_dataset.to_netcdf(finalfilepath)
