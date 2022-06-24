from extracthendrix.readers import AromeHendrixReader
from datetime import date, time, datetime
import usevortex
from ftplib import FTP
import getpass
import ftplib
import os
from pprint import pprint as pp


native_files_folder = "/home/merzisenh/NO_SAVE/extracthendrix/_native_files_"


dateiterator = [
    (datetime(2019, 4, 10, 0, 0), 6),
    (datetime(2020, 4, 10, 0, 0), 7),
    (datetime(2020, 4, 10, 0, 0), 8),
    (datetime(2020, 4, 10, 0, 0), 9),
    (datetime(2020, 4, 10, 0, 0), 10),
    (datetime(2020, 4, 10, 0, 0), 11),
    (datetime(2020, 4, 10, 0, 0), 12)
]


ftp = FTP('hendrix.meteo.fr')
print("Connect to Hendrix")
login = input("Login: ")
password = getpass.getpass("Password: ")
ftp.login(login, password)


def get_prestaging_file_list(ftpconnection, dateterm_iterator, model_name, runtime):
    ftp = ftpconnection
    filelist = []
    notfound = []
    reader = AromeHendrixReader(
        model=model_name,
        runtime=runtime
    )
    for date_, term in dateterm_iterator:
        resdesc = reader._get_vortex_resource_description(date_, term)
        potential_locations = [usevortex.get_resources(
            getmode='locate', **resource_description) for resource_description in resdesc]
        for resource in potential_locations:
            path_file = resource[0].split(':')[1]
            file_name = path_file.split('/')[-1]
            path_folder = os.path.dirname(path_file)
            # Check that the file exist at the specified path
            try:
                ftp.cwd(path_folder)
            except ftplib.error_perm:
                notfound.append(path_folder)
            for file in ftp.nlst():
                if file_name in file:
                    path_to_file = os.path.join(path_folder, file)
                    print("Success", path_to_file)
                    filelist.append(path_to_file)
    return filelist, notfound


filelist, notfound = get_prestaging_file_list(
    ftp, dateiterator, 'AROME', time(hour=0))
