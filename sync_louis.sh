#!/bin/bash

rsync \
	-av \
	--exclude /.git/ \
	--delete \
	/home/letoumelinl/develop/extracthendrix/ letoumelinl@sxcen.cnrm.meteo.fr://home/letoumelinl/develop/extracthendrix/
