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

REVISION_CMD = /usr/bin/svnversion -n . | /bin/sed -e 's/^[0-9]*:\([0-9]*\).*/\1/'
REVISION = FotoPreProcessor-rev$(shell printf "%05i" $(shell $(REVISION_CMD)))

.PHONY : translation_de
translation_de:
	@/usr/bin/pylupdate4 -noobsolete FotoPreProcessor*.py -ts i18n/FotoPreProcessor.de.ts
	@/usr/bin/linguist i18n/FotoPreProcessor.de.ts

tarball:
	@/usr/bin/sha512sum $(FILES) > checksums.sha512
	@/usr/bin/md5sum $(FILES) > checksums.md5
	@/bin/tar -cvzf "$(REVISION).tar.gz" --transform 's,^,$(REVISION)/,' $(FILES) checksums.md5 checksums.sha512 
 	@/usr/bin/gpg -b --use-agent "$(REVISION).tar.gz"
	@/bin/chmod 644 "$(REVISION).tar.gz" "$(REVISION).tar.gz.sig"
	@/usr/bin/scp "$(REVISION).tar.gz" "$(REVISION).tar.gz" abelbeck@download.savannah.gnu.org:releases/fotopreprocessor/

