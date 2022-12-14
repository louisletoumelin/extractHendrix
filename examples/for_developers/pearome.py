from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, dateiterator
import extracthendrix.config.variables.pearome as pear
from datetime import date


layout = FolderLayout(work_folder='/home/merzisenh/NO_SAVE/extracthendrix')

computed_vars = [pear.Wind, pear.Wind_DIR]

computer = ComputedValues(layout, delete_native=False, domain='alp',
                          computed_vars=computed_vars, run=3, members=[1, 2])


date_start = date(2022, 6, 13)
date_end = date(2022, 6, 15)
first_term = 6
last_term = 24
delta_t = 6
run = 6


def shifting_to_next_day(run, previous, current):
    previous_day = validity_date(run, *previous).day
    current_day = validity_date(run, *current).day
    if previous_day == current_day:
        return None
    return validity_date(run, *previous).strftime("%Y_%m_%d")

# attention piège!! si un fichier existe déjà en cache avec d'autres variables,
# (issues d'une interro précédente), il n'est pas remplacé si on lit pour la même date, term


previous = (date_start, first_term)
for date_, term in dateiterator(date_start, date_end, first_term, last_term, delta_t):
    shifting = shifting_to_next_day(run, previous, (date_, term))
    if shifting:
        computer.concat_and_clean_computed_folder(shifting)
    computer.compute(date_, term)
    previous = (date_, term)
