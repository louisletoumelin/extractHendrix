from datetime import timedelta, time, datetime, date
from pprint import pprint
from extracthendrix.generic import ComputedValues, FolderLayout, validity_date, dateiterator, AromeCacheManager
# TODO: generic c'est vraiment pas terrible comme nom faudrait trouver une idée plus parlante
# dir(an) pour voir les noms de variables disponibles - les points sont remplacés par des doubles __ (car interdits dans les noms de variables)
import extracthendrix.config.variables.arome_native as an
from extracthendrix.readers import AromeHendrixReader

layout = FolderLayout(
    work_folder='/home/merzisenh/NO_SAVE/hendrix_extractions/example_cache')
# crée le dossier pour l'extraction avec les sous-dossiers _native_, _cache_, _computed_, _final_
# et garde les emplacements de tout ce monde là en mémoire

arome_cache_manager = AromeCacheManager(
    layout,
    domain='alp',
    variables=[an.CLSTEMPERATURE, an.CLSVENT__MERIDIEN,
               an.CLSVENT__ZONAL, an.S090TEMPERATURE],
    model='AROME',
    runtime=time(0),
    delete_native=False,
    autofetch_native=False
)

date_ = date(2022, 6, 24)
term_ = 9
arome_cache_manager.put_in_cache(date_, term_)
# exception!  C'est normal, il ne trouve pas le fichier natif dont il a besoin

# On peut aller le chercher "à la main" en utilisant le "reader" adéquat

arome_reader = AromeHendrixReader(
    folderLayout=layout,
    model='AROME',
    runtime=time(0)
)

arome_reader.get_native_file(date_, term_)


arome_cache_manager.put_in_cache(date_, term_)
# ce coup ci ça marche!

# isn't it a lot of work to do to put some data in cache?
# Yes, but guess what, the "autofetch_native" argument of arome_cache_manager allows him to ask himself to a reader he instantiates like a big boy to fetch the data he needs


arome_cache_manager_autofetch = AromeCacheManager(
    layout,
    domain='alp',
    variables=[an.CLSTEMPERATURE, an.CLSVENT__MERIDIEN,
               an.CLSVENT__ZONAL, an.S090TEMPERATURE],
    model='AROME',
    runtime=time(0),
    delete_native=False,
    autofetch_native=True
)


date1 = date(2022, 6, 24)
term1 = 12
arome_cache_manager_autofetch.put_in_cache(date1, term1)
# this time everything rolls smoothly! Get some coffee while the program is downloading the FA  file on Hendrix

# checkout both the _native_ and _cache_ repositories - we have some new files out there!

# To make this magic happen, the cache manager, as we sayed, instantiates a "reader" to get the native files, it resides in the attribute "extractor" of the cache manager, let's check it out
print(arome_cache_manager_autofetch.extractor)
# TODO: add a nice __repr__ method to the AromeHendrixReader class to get a more useful description here
# (displaying the name of the class + the model_name, runtime, etc...)


# to get the file, the cache manager calls AromeHendrixReader.get_native_file
# checkout the code of this method: if the native file is already here, it doesn't download again but solely returns the filepath

# to get the native file path:
arome_cache_manager_autofetch.extractor.native_file_path(date1, term1)

# to get the cache file path:
arome_cache_manager_autofetch.get_cache_path(date1, term1)

# TODO: if we want to add support for multiple domains extraction, the cache path should include a string representing the domain


# the cache manager provides a method to read the variables values in the cache:
arome_cache_manager_autofetch.read_cache(date1, term1, an.CLSTEMPERATURE)
# check out the code: if the file is in cache, this method will read the cache file, if it's not, it will call put_in_cache to get it


# that's it for the cache, the next example will show how to use the ComputedValues class to execute whatever computations we need on the variables in cache


# TODO (maybe not right now but might be a good idea): the cache manager could be independant of the model it caches if it was given
# a reader at instantiation - something like:
# reader = AromeHendrixReader( .......)
# cache_manager = CacheManager( extractor = reader, ....)
# this way the code in CacheManager would be totally independant of the model we fetch and adding a new model to the system would only require to write a new reader
# we could wrap this slightly more complex instantiation in a function taking care of instantiating the right reader for the task
# cache_manager = init_cache_manager_with_reader(model=..., runtime=..., ...)
# (it's a common pattern known as the factory pattern)
