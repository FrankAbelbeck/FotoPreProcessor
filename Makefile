# Makefile for translation and packaging tasks
# Copyright (C) 2012 Frank Abelbeck <frank.abelbeck@googlemail.com>
# 
# This file is part of the FotoPreProcessor program "FotoPreProcessor.py".
# 
# This program is free software: you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation, either version 3 of the License, or
# (at your option) any later version.
# 
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
# 
# You should have received a copy of the GNU General Public License
# along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
# $Id$

FILES=../FotoPreProcessor/FotoPreProcessor.py \
../FotoPreProcessor/FotoPreProcessorItem.py \
../FotoPreProcessor/FotoPreProcessorTools.py \
../FotoPreProcessor/FotoPreProcessorWidgets.py \
../FotoPreProcessor/FotoPreProcessorOSM.html \
../FotoPreProcessor/FotoPreProcessor.exiftool \
../FotoPreProcessor/Makefile \
../FotoPreProcessor/i18n/FotoPreProcessor.de.qm \
../FotoPreProcessor/i18n/FotoPreProcessor.de.ts \
../FotoPreProcessor/icons/Marker2.png \
../FotoPreProcessor/icons/changed.png \
../FotoPreProcessor/icons/unknownPicture2.png \
../FotoPreProcessor/COPYING \
../FotoPreProcessor/README

.PHONY : translation_de
translation_de:
	@/usr/bin/pylupdate4 -noobsolete FotoPreProcessor*.py -ts i18n/FotoPreProcessor.de.ts
	@/usr/bin/linguist i18n/FotoPreProcessor.de.ts


tarball:
	@/usr/bin/sha512sum $(FILES) > ../FotoPreProcessor/checksums.sha512
	@/usr/bin/md5sum $(FILES) > ../FotoPreProcessor/checksums.md5
	@/bin/tar -cvzf FotoPreProcessor-rev"$(shell /usr/bin/svnversion -n .)".tar.gz $(FILES) ../FotoPreProcessor/checksums.md5 ../FotoPreProcessor/checksums.sha512

