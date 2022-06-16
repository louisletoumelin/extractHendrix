from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, dateiterator
import extracthendrix.config.variables.pearome as pear
from datetime import date


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"
cache_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_cache_"
computed_vars_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_computed_"
final_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_final_"

layout = FolderLayout(native_files_folder=native_files_folder,
                      cache_folder=cache_folder,
                      computed_vars_folder=computed_vars_folder,
                      final_files_folder=final_files_folder
                      )

computed_vars = [pear.Wind, pear.Wind_DIR]

computer = ComputedValues(layout, delete_native=False, domain='alp',
                          computed_vars=computed_vars, analysis_hour=3, members=[1, 2])


date_start = date(2022, 6, 13)
date_end = date(2022, 6, 15)
first_term = 6
last_term = 24
delta_terms = 6
runtime = 6


def shifting_to_next_day(runtime, previous, current):
    previous_day = validity_date(runtime, *previous).day
    current_day = validity_date(runtime, *current).day
    if previous_day == current_day:
        return None
    return validity_date(runtime, *previous).strftime("%Y-%m-%d")

# attention piège!! si un fichier existe déjà en cache avec d'autres variables,
# (issues d'une interro précédente), il n'est pas remplacé si on lit pour la même date, term


previous = (date_start, first_term)
computed = {}
for date_, term in dateiterator(date_start, date_end, first_term, last_term, delta_terms):
    shifting = shifting_to_next_day(runtime, previous, (date_, term))
    if shifting:
        computer.concat_files_and_forget(shifting)
    computer.compute(date_, term)
    previous = (date_, term)
