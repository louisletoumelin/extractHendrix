from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, dateiterator


class Grouper():

    def __init__(self, groupby):
        self.groupby = groupby
    

    def filetag(self, runtime, date_, term):
        if self.groupby == ('timeseries','daily'):
            return validity_date(runtime, date_, term).strftime("%Y-%m-%d")
        if self.groupby == ('timeseries','monthly'):
            return validity_date(runtime, date_, term).strftime("%Y-%m")
        if self.groupby == ('forecast',):
            return validity_date(runtime,date_,0).strftime("%Y-%m-%d")

    def batch_is_complete(self, runtime, previous, current):
        if self.groupby == ('timeseries','daily'):
            return validity_date(runtime, *previous).day != validity_date(runtime, *current).day
        if self.groupby == ('timeseries','monthly'):
            return validity_date(runtime, *previous).month != validity_date(runtime, *current).month
        if self.groupby == ('forecast',):
            return previous[0] != current[0]



class DictNamespace():

    def __init__(self, dict_):
        self.__dict__ = dict_


def execute(config_user):
    c = DictNamespace(config_user)
    layout = FolderLayout(work_folder=c.work_folder)
    grouper = Grouper(c.groupby)
    computer = ComputedValues(
        layout,
        domain=c.domain,
        computed_vars=c.variables,
        analysis_hour=c.analysis_hour,
        autofetch_native=True
    )
    previous = (c.start_date, c.start_term)
    for date_, term in dateiterator(c.start_date, c.end_date, c.start_term, c.end_term, c.delta_terms):
        if grouper.batch_is_complete(c.analysis_hour, previous, (date_, term)):
            computer.concat_files_and_forget(
                    grouper.filetag(c.analysis_hour, *previous)
                    )
        computer.compute(date_, term)
        previous = (date_, term)
    computer.concat_files_and_forget(
                    grouper.filetag(c.analysis_hour, *previous)
                    )
    return



    
