# Extraction de données sur Hendrix



## Contribuer au développement sans (se) faire de sacs de noeuds

Le code est fait pour tourner sur un serveur toulousain ayant accès à Hendrix - en pratique pour nous c'est *sxcen*.

Il est pertinent, si d'autres codes utilisent extracthendrix pour la lecture des données, d'avoir deux versions de *extracthendrix* sur *sxcen*, une version "de production" et une version "de développement", afin d'éviter de casser les codes dépendant de la librairie lorsqu'on développe (Hugo: je parle d'expérience...).

### Exemple de la configuration de Hugo sur sxcen

Sur mon compte, la production de figures pour Sytron s'appuie sur extracthendrix pour la lecture des fichiers de la chaîne S2M option sytron, cette production est lancée tous les jours à heures fixes par un cron. Je veux pouvoir développer sur extracthendrix sans prendre le risque de casser cette production, et de ne mettre à jour cette production de fichiers Sytron pour utiliser la dernière version d'extracthendrix que lorsque je le décide.

Ma configuration est la suivante:
- le code figé d'extracthendrix est dans le dossier `$HOME/PRODUCTION/extracthendrix` - a.k.a `$HENDRIX_PROD` (obtenu en faisant un `git clone https://git.meteo.fr/cnrm-cen/louisletoumelin/extracthendrix/` *(TODO: ça serait pas mal d'avoir un tag sur la version en question - et un tag correspondant sur le code sytron)*
- le code figé est installé dans l'environnement python par défaut de sxcen `pip install --user $HENDRIX_PROD`
- pour développer, il y a une autre version du code dans le dossier *$HOME/RSYNCED_CODES/extracthendrix* (a.k.a *$HENDRIX_DEV*). Ce code est synchronisé par rsync (pas de git clone sur sxcen donc) avec le code figurant sur mon ordinateur portable, ou j'ai un environnement de développement qui me convient bien *(seul bémol: ça pose des problèmes pour développer en télétravail ou le seul mode de connexion possible à sxcen est telnet)*
- le développement se fait dans un environnement virtuel astucieusement nommé *develop* (`source $HOME/virtual/develop/activate` pour le lancer)
- depuis l\'environnement develop, faire `pip install -e $HENDRIX_DEV` pour installer le code en mode développement (l'option *-e* installe le code en mode dev, c'est-à-dire que toute modification du code sera imméditement répercutée dans l'environnement python)

Et voilà, on peut ainsi développer tranquilement dans notre environnement develop sans rien casser des codes qui dépendent de extracthendrix.