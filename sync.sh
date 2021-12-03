#!/bin/bash

rsync \
	-av \
	--exclude /.git/ \
	--delete \
	/home/hugo/Projets/extracthendrix/ merzisenh@sxcen.cnrm.meteo.fr:~/RSYNCED_CODES/extracthendrix/
