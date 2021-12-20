#!/bin/bash

rsync \
	-av \
	--exclude /.git/ \
	--delete \
	/home/hugo/Projets/01_plomberie/extracthendrix/ merzisenh@sxcen.cnrm.meteo.fr:/home/merzisenh/RSYNCED_CODES/extracthendrix/
