from datetime import date, time
from extracthendrix.generic import ComputedValues, FolderLayout, dateiterator
import extracthendrix.config.variables.arome as ar
# TODO? idea: the computations made in the original script from Isabelle and Vincent aimed at manufacturing a forcing file to run
# Crocus - maybe it would be nice to name the file "crocus" rathet than arome and to provide a function creating a "Crocus ready" file
# but we should wait until we have a discussion on the code with the collegues


layout = FolderLayout(
    work_folder='/home/merzisenh/NO_SAVE/hendrix_extractions/example_compute')

computer = ComputedValues(
    folderLayout=layout,
    # for the needs of the example, in real extractions we don't want to keep the heavy native files around
    delete_native=False,
    delete_individuals=False,  # delete or not the individual files after beign computed
    domain='alp',
    # needs only AROME_SURFACE to be computed the files are much lighter
    computed_vars=[ar.SWE],
    analysis_hour=0,  # TODO: replace everywhere with runtime
    autofetch_native=True
)

date0 = date(2022, 6, 24)
term0 = 9

computer.compute(date0, term0)
# look at the contents of the folder _computed_: it contains a file with the desired calculated variable
# the _native_ and _cache_ folder are populated too, since we asked for the files not to be deleted
# if we did, an exception would have been raised, let's see this

computer_noautofetch = ComputedValues(
    folderLayout=layout,
    domain='alp',
    computed_vars=[ar.SWE],
    analysis_hour=0,
    autofetch_native=False
)
term1 = 15
computer_noautofetch.compute(date0, term1)


# if we want to compute a whole range of dates and terms, we simply use it in a loop
for term in range(4):
    computer.compute(date0, term)

# that's it!

# the computer remembers the list of the file it has computed
print(computer.computed_files)

# and if we want to concatenate all the files the computer remembers:
computer.concat_files_and_forget("first_concatenation")
# the argument given to the method will be inserted in the filename
# (so when we'll want to concatenate monthly files for instance we can give him a string representing the month)

# now the list of computed files is empty
print(computer.computed_files)
# and if we check out the _final_ folder we find something interesting


# the code provides an iterator to iterate over a range of dates and terms
for date_, term in dateiterator(
        date_start=date(2020, 1, 1),
        date_end=date(2021, 3, 1),
        first_term=2,
        last_term=24,
        delta_terms=2):
    print(date_, term)
# you can call computer.compute in this loop to get the results for all the dates/terms you wish
