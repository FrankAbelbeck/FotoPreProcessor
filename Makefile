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

.PHONY : translation_de

translation_de:
	@/usr/bin/pylupdate4 -noobsolete FotoPreProcessor*.py -ts i18n/FotoPreProcessor.de.ts
	@/usr/bin/linguist i18n/FotoPreProcessor.de.ts
