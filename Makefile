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

FILES = FotoPreProcessor.py \
FotoPreProcessorItem.py \
FotoPreProcessorTools.py \
FotoPreProcessorWidgets.py \
FotoPreProcessorOSM.html \
FotoPreProcessor.exiftool \
Makefile \
i18n/FotoPreProcessor.de.qm \
i18n/FotoPreProcessor.de.ts \
icons/Marker2.png \
icons/changed.png \
icons/unknownPicture2.png \
COPYING \
README

REVISION = $(shell /usr/bin/svnversion -n . | /bin/cut -d ':' -f 2)
TARBALL = FotoPreProcessor-rev$(shell printf "%05i" $(REVISION))

.PHONY : translation_de
translation_de:
	@/usr/bin/pylupdate4 -noobsolete FotoPreProcessor*.py -ts i18n/FotoPreProcessor.de.ts
	@/usr/bin/linguist i18n/FotoPreProcessor.de.ts

tarball:
	/usr/bin/sha512sum $(FILES) > checksums.sha512
	/usr/bin/md5sum $(FILES) > checksums.md5
	/bin/tar -cvzf $(TARBALL).tar.gz --transform 's,^,$(TARBALL)/,' $(FILES) checksums.md5 checksums.sha512 
 	/usr/bin/gpg -b --use-agent $(TARBALL).tar.gz
	/bin/chmod 644 $(TARBALL).tar.gz $(TARBALL).tar.gz.sig
	/usr/bin/scp $(TARBALL).tar.gz $(TARBALL).tar.gz.sig abelbeck@download.savannah.gnu.org:releases/fotopreprocessor/

