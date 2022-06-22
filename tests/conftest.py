import sys
import os


import pytest


class Helpers:

    @staticmethod
    def symlink_files(test_data_folder, test_folder, subfolder, type_):
        """
        type_: type de dossier de travail de extracthendrix (_native_, _cache_, _computed_, _final-)
        test_data_folder: le dossier contenant les données pour les tests
        subfolder: le sous-dossier du précédent contenant les données pour un test
        Crée un lien symbolique dans les dossi
        """
        native_data_loc = os.path.join(test_data_folder, subfolder, type_)
        list_native_files = os.listdir(native_data_loc)
        for filename in list_native_files:
            os.symlink(
                os.path.join(native_data_loc, filename),
                os.path.join(test_folder, type_, filename)
            )


@pytest.fixture
def helpers():
    return Helpers
