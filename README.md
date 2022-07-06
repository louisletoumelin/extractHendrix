# ExtractHendrix

ExtractHendrix is a package to download model outputs on Hendrix as it simplest.

- **Developers:** Louis Le Toumelin, Hugo Merzisen, Sabine Radanovics
- **Mails:** louis.letoumelin@meteo.fr, hugo.merzisen@meteo.fr, sabine.radanovics@meteo.fr
- **Group:** CEN / CNRM / Météo-France/ CNRS



Install (on Météo-France network)
----------------------

    git clone https://git.meteo.fr/cnrm-cen/louisletoumelin/extracthendrix

    pip install extracthendrix


Requirements
----------------------
- Météo-France packages: epygram, vortex

- General packages: numpy, pandas, xarray

- For testing: pytest


Example
----------------------


    from extracthendrix import execute

    config_user = dict(
        work_folder="path/to/my/folder/",
        model="AROME",
        domain=["alp", "corsica", "pyr", "switzerland"],
        variables=['Tair', Tmax', 'Qair', 'SWE', 'snow_density', 'snow_albedo'],
        email_address="louis.letoumelin@meteo.fr",
        start_date=datetime(2018, 10, 31),
        end_date=datetime(2018, 10, 31),
        groupby=('timeseries', 'daily'),
        run=0,
        delta_t=1,
        start_term=6,
        end_term=29)

    execute(config_user)

For developers
----------------------
[FR]

## Contribuer au développement sans (se) faire de sacs de noeuds

Le code est fait pour tourner sur un serveur toulousain ayant accès à Hendrix - en pratique pour nous c'est *sxcen*.

Il est pertinent, si d'autres codes utilisent extracthendrix pour la lecture des données, d'avoir deux versions de *extracthendrix* sur *sxcen*, une version "de production" et une version "de développement", afin d'éviter de casser les codes dépendant de la librairie lorsqu'on développe (Hugo: je parle d'expérience...).

### Exemple de la configuration de Hugo sur sxcen

Sur mon compte, la production de figures pour Sytron s'appuie sur extracthendrix pour la lecture des fichiers de la chaîne S2M option sytron, cette production est lancée tous les jours à heures fixes par un cron. Je veux pouvoir développer sur extracthendrix sans prendre le risque de casser cette production, et de ne mettre à jour cette production de fichiers Sytron pour utiliser la dernière version d'extracthendrix que lorsque je le décide.

Ma configuration est la suivante:
- le code figé d'extracthendrix est dans le dossier `$HOME/PRODUCTION/extracthendrix` - a.k.a `$HENDRIX_PROD` (obtenu en faisant un `git clone https://git.meteo.fr/cnrm-cen/louisletoumelin/extracthendrix/`
- le code figé est installé dans l'environnement python par défaut de sxcen `pip install --user $HENDRIX_PROD`
- pour développer, il y a une autre version du code dans le dossier *$HOME/RSYNCED_CODES/extracthendrix* (a.k.a *$HENDRIX_DEV*). Ce code est synchronisé par rsync (pas de git clone sur sxcen donc) avec le code figurant sur mon ordinateur portable, ou j'ai un environnement de développement qui me convient bien *(seul bémol: ça pose des problèmes pour développer en télétravail ou le seul mode de connexion possible à sxcen est telnet)*
- le développement se fait dans un environnement virtuel astucieusement nommé *develop* (`source $HOME/virtual/develop/activate` pour le lancer)
- depuis l\'environnement develop, faire `pip install -e $HENDRIX_DEV` pour installer le code en mode développement (l'option *-e* installe le code en mode dev, c'est-à-dire que toute modification du code sera imméditement répercutée dans l'environnement python)
- le projet contient un fichier *sxcen_python_env*. J'ai fait le choix de mettre les dépendances requises dans ce fichier plutôt que dans le setup.py car ce ne sont pas des dépendances du projet lui-même mais des dépendances de snowtools, epygram ou vortex (`pip install -r sxcen_python_env` depuis l'environnement virtuel pour installer toutes les librairies nécessaires)
- note: réinstaller tout le contenu de l'environnement par défaut avec le duo pip freeze / pip install  ne fonctionne pas, un tas de dépendances indiquées dans le pip freeze (peut-être des dépendances locales) ne sont pas trouvées sur pipy.

Et voilà, on peut ainsi développer tranquilement dans notre environnement develop sans rien casser des codes qui dépendent de extracthendrix.
