#!/bin/bash

rsync \
	-av \
	--exclude /.git/ \
	--delete \
	/home/letoumelinl/extracthendrix/ letoumelinl@sxcen.cnrm.meteo.fr://cnrm/cen/users/NO_SAVE/letoumelinl/extracthendrix
