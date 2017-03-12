#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FotoPreProcessorWidgets: custom dock widgets and application/settings dialogs
Copyright (C) 2012-2017 Frank Abelbeck <frank.abelbeck@googlemail.com>

This file is part of the FotoPreProcessor program "FotoPreProcessor.py".

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

2015-06-16: migration to Python3
2015-10-25: upgrade to new signal/slot mechanism, file naming now configurable
2015-10-26: flexible file naming activated
2017-03-11: ported to PyQt5
"""

import subprocess,sys,os.path,codecs,re,time,yaml

from PyQt5 import QtGui, QtWidgets, QtCore

import FotoPreProcessorTools


class FPPGeoTaggingDock(QtWidgets.QDockWidget):
	""""Class for the GeoTagging Dock Widget."""
		
	# new signal/slot mechanism: define custom signals (must be defined as class vars!)
	dockResetTriggered = QtCore.pyqtSignal()
	dockDataUpdated = QtCore.pyqtSignal(float,float,float)
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtWidgets.QDockWidget.__init__(self,QtCore.QCoreApplication.translate("DockWidgets","GeoTagging"))
		
		self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		#
		# setup GUI
		#
		button_lookUp = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","Look-Up... (m)"))
		button_lookUp.setShortcut(QtGui.QKeySequence("m"))
		
		box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Reset)
		box_stdButtons.addButton(button_lookUp,QtWidgets.QDialogButtonBox.ActionRole)
		self.button_reset = box_stdButtons.button(QtWidgets.QDialogButtonBox.Reset)
		
		self.spinbox_latitude = QtWidgets.QDoubleSpinBox()
		self.spinbox_latitude.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_latitude.setRange(-85,85)
		self.spinbox_latitude.setDecimals(8)
		self.spinbox_latitude.setSuffix(" °")
		self.spinbox_latitude.setSingleStep(1)
		self.spinbox_latitude.setWrapping(True)
		self.spinbox_latitude.setSpecialValueText(QtCore.QCoreApplication.translate("DockWidgets","undefined"))
		self.spinbox_latitude.setKeyboardTracking(False)
		
		self.spinbox_longitude = QtWidgets.QDoubleSpinBox()
		self.spinbox_longitude.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_longitude.setRange(-180,180)
		self.spinbox_longitude.setDecimals(8)
		self.spinbox_longitude.setSuffix(" °")
		self.spinbox_longitude.setSingleStep(1)
		self.spinbox_longitude.setWrapping(True)
		self.spinbox_longitude.setSpecialValueText(QtCore.QCoreApplication.translate("DockWidgets","undefined"))
		self.spinbox_longitude.setKeyboardTracking(False)
		
		self.spinbox_elevation = QtWidgets.QDoubleSpinBox()
		self.spinbox_elevation.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_elevation.setRange(-11000,9000)
		self.spinbox_elevation.setDecimals(1)
		self.spinbox_elevation.setSuffix(" m")
		self.spinbox_elevation.setSingleStep(1)
		self.spinbox_elevation.setKeyboardTracking(False)
		
		layout_coordinates = QtWidgets.QFormLayout()
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","Latitude:"),
			self.spinbox_latitude
		)
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","Longitude:"),
			self.spinbox_longitude
		)
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","Elevation:"),
			self.spinbox_elevation
		)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addLayout(layout_coordinates)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtWidgets.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		button_lookUp.clicked.connect(self.lookUpCoordinates)
		self.button_reset.clicked.connect(self.triggerReset)
		self.spinbox_latitude.editingFinished.connect(self.updateData)
		self.spinbox_longitude.editingFinished.connect(self.updateData)
		self.spinbox_elevation.editingFinished.connect(self.updateData)
		self.setLocation()
	
	
	def setLocation(self,latitude=None,longitude=None,elevation=None):
		try:    latitude  = float(latitude)
		except: latitude  = self.spinbox_latitude.minimum()
		try:    longitude = float(longitude)
		except: longitude = self.spinbox_longitude.minimum()
		try:    elevation = float(elevation)
		except: elevation = 0.0
		self.spinbox_latitude.setValue(latitude)
		self.spinbox_longitude.setValue(longitude)
		self.spinbox_elevation.setValue(elevation)
		self.float_latitude  = latitude
		self.float_longitude = longitude
		self.float_elevation = elevation
	
	
	def location(self):
		latitude  = self.spinbox_latitude.value()
		longitude = self.spinbox_longitude.value()
		elevation = self.spinbox_elevation.value()
		if latitude <= self.spinbox_latitude.minimum():   latitude = None
		if longitude <= self.spinbox_longitude.minimum(): longitude = None
		return (latitude,longitude,elevation)
	

	def lookUpCoordinates(self):
		(latitude,longitude,elevation) = self.location()
		dlg = FotoPreProcessorTools.FPPGeoTaggingDialog()
		
		if latitude != None and longitude != None:
			dlg.setLocation(latitude,longitude,elevation)
		else:
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
			
			try:    latitude = float(settings.value("DefaultLatitude",52.374444))
			except: latitude = 52.374444
			
			try:    longitude = float(settings.value("DefaultLongitude",9.738611))
			except: longitude = 9.738611
			
			dlg.setLocation(latitude,longitude,0.0)
		
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			try:
				(latitude,longitude,elevation) = dlg.location()
				self.setLocation(latitude,longitude,elevation)
				self.updateData()
			except:
				pass
	
	
	def triggerReset(self):
		self.dockResetTriggered.emit()
	
	
	def updateData(self):
		(latitude,longitude,elevation) = self.location()
		if (latitude != None) and (longitude != None):
			self.dockDataUpdated.emit(latitude,longitude,elevation)
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))



class FPPTimezonesDock(QtWidgets.QDockWidget):
	""""Class for the Timezone Correction Dock Widget."""
	
	# new signal/slot mechanism: define custom signals
	dockResetTriggered = QtCore.pyqtSignal()
	dockDataUpdated = QtCore.pyqtSignal(str,str)
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Parameter timezoneNames is used to populate the timezone combo boxes.
It should be a tuple of valid timezone names like "Europe/Berlin".

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtWidgets.QDockWidget.__init__(self,QtCore.QCoreApplication.translate("DockWidgets","Timezone Correction"))
		
		self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.tz = FotoPreProcessorTools.FPPTimezone()
		self.tz.loadTimezoneDB()
		
		#
		# setup GUI
		#
		self.button_fromTz = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","by location"))
		self.button_fromTz.setToolTip(QtCore.QCoreApplication.translate("DockWidgets","Use given coordinates to estimate timezone."))

		self.button_toTz = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","by location"))
		self.button_toTz.setToolTip(QtCore.QCoreApplication.translate("DockWidgets","Use given coordinates to estimate timezone."))
		
		self.combo_fromTz = QtWidgets.QComboBox()
		self.combo_toTz = QtWidgets.QComboBox()
		
		self.combo_fromTz.addItems(self.tz.timezoneNames())
		self.combo_toTz.addItems(self.tz.timezoneNames())
		
		box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Reset)
		self.button_reset = box_stdButtons.button(QtWidgets.QDialogButtonBox.Reset)
		
		layout_fromTz = QtWidgets.QHBoxLayout()
		layout_fromTz.addWidget(self.combo_fromTz)
		layout_fromTz.addWidget(self.button_fromTz)
		
		layout_toTz = QtWidgets.QHBoxLayout()
		layout_toTz.addWidget(self.combo_toTz)
		layout_toTz.addWidget(self.button_toTz)
		
		layout_timezones= QtWidgets.QFormLayout()
		layout_timezones.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","From:"),
			layout_fromTz
		)
		layout_timezones.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","Shift to:"),
			layout_toTz
		)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addLayout(layout_timezones)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtWidgets.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.button_reset.clicked.connect(self.triggerReset)
		self.combo_fromTz.activated.connect(self.updateData)
		self.combo_toTz.activated.connect(self.updateData)
		self.button_fromTz.clicked.connect(self.setFromTimezoneByCoordinates)
		self.button_toTz.clicked.connect(self.setToTimezoneByCoordinates)
		
		self.setTimezones()
		self.setLocation()
	
	
	def setTimezones(self,fromTz=None,toTz=None):
		if fromTz == None: fromTz = "UTC"
		if toTz == None:   toTz   = "UTC"
		try:
			int_fromTz = self.tz.timezoneIndex(str(fromTz))
			int_toTz   = self.tz.timezoneIndex(str(toTz))
		except:
			pass
		else:
			self.combo_fromTz.setCurrentIndex(int_fromTz)
			self.combo_toTz.setCurrentIndex(int_toTz)
	
	
	def setFromTimezoneByCoordinates(self):
		try:
			self.combo_fromTz.setCurrentIndex(
				self.tz.timezoneIndex(
					self.tz.timezoneName(
						self.float_latitude,self.float_longitude
					)
				)
			)
			self.updateData()
		except:
			pass
	
	
	def setToTimezoneByCoordinates(self):
		try:
			self.combo_toTz.setCurrentIndex(
				self.tz.timezoneIndex(
					self.tz.timezoneName(
						self.float_latitude,self.float_longitude
					)
				)
			)
			self.updateData()
		except:
			pass
	
	
	def setLocation(self,latitude=None,longitude=None):
		try:
			self.float_latitude  = float(latitude)
			self.float_longitude = float(longitude)
			self.button_fromTz.setEnabled(True)
			self.button_toTz.setEnabled(True)
		except:
			self.float_latitude  = None
			self.float_longitude = None
			self.button_fromTz.setEnabled(False)
			self.button_toTz.setEnabled(False)
	
	
	def timezones(self):
		return (str(self.combo_fromTz.currentText()),str(self.combo_toTz.currentText()))
	
	
	def triggerReset(self):
		self.dockResetTriggered.emit()
	
	
	def updateData(self,value=None):
		try:
			fromTz = str(self.combo_fromTz.currentText())
			toTz = str(self.combo_toTz.currentText())
			self.dockDataUpdated.emit(fromTz,toTz)
		except:
			pass
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))



class FPPKeywordsDock(QtWidgets.QDockWidget):
	""""Class for the Keywords Dock Widget."""
	# new signal/slot mechanism: define custom signals
	dockResetTriggered = QtCore.pyqtSignal()
	dockKeywordAdded = QtCore.pyqtSignal(str)
	dockKeywordRemoved = QtCore.pyqtSignal(str)
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtWidgets.QDockWidget.__init__(self,QtCore.QCoreApplication.translate("DockWidgets","Keywords"))
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
		
		self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBKeywords = FotoPreProcessorTools.FPPStringDB()
		try:    self.DBKeywords.loadList([str(i) for i in settings.value("Keywords",list())])
		except: pass
		
		#
		# setup GUI
		#
		#---------------------------------------------------------------
		# Keywords dock
		#---------------------------------------------------------------
		self.list_keywords = QtWidgets.QListWidget()
		self.list_keywords.setSelectionMode(QtWidgets.QAbstractItemView.ExtendedSelection)
		
		self.button_add = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","Add... (k)"))
		self.button_remove = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","Remove"))
		
		self.button_add.setShortcut(QtGui.QKeySequence("k"))
		
		box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Reset)
		box_stdButtons.addButton(self.button_add,QtWidgets.QDialogButtonBox.ActionRole)
		box_stdButtons.addButton(self.button_remove,QtWidgets.QDialogButtonBox.ActionRole)
		self.button_reset = box_stdButtons.button(QtWidgets.QDialogButtonBox.Reset)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.list_keywords)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtWidgets.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.list_keywords.itemSelectionChanged.connect(self.updateRemoveButtonState)
		self.button_add.clicked.connect(self.addKeyword)
		self.button_remove.clicked.connect(self.removeKeyword)
		self.button_reset.clicked.connect(self.triggerReset)
		
		self.setKeywords()
		
	
	def addKeyword(self):
		tpl_keywords = self.DBKeywords.strings()
		(keyword,ok) = QtWidgets.QInputDialog.getItem(self,
			QtCore.QCoreApplication.translate("Dialog","Add new Keyword"),
			QtCore.QCoreApplication.translate("Dialog","Please provide a keyword for the selected images:"),
			tpl_keywords,0,True
		)
		if ok:
			keyword = str(keyword)
			if not keyword in self.set_keywords:
				self.DBKeywords.add(keyword)
				self.set_keywords.add(keyword)
				self.list_keywords.addItem(keyword)
				self.list_keywords.sortItems()
				self.dockKeywordAdded.emit(keyword)
				self.updateRemoveButtonState()
			else:
				answer = QtWidgets.QMessageBox.information(
					self,
					QtCore.QCoreApplication.translate("Dialog","Keyword Already Exists"),
					QtCore.QCoreApplication.translate("Dialog","Such a keyword is already in the list and hence will be ignored.")
				)
	
	
	def removeKeyword(self):
		for item in self.list_keywords.selectedItems():
			self.list_keywords.takeItem(self.list_keywords.row(item))
			self.set_keywords.remove(str(item.text()))
			self.dockKeywordRemoved.emit(str(item.text()))
		self.list_keywords.sortItems()
		self.updateRemoveButtonState()
	
	
	def setKeywords(self,keywords=tuple()):
		try:
			self.set_keywords = set([str(i) for i in keywords])
			self.list_keywords.clear()
			self.list_keywords.addItems(tuple(self.set_keywords))
			self.list_keywords.sortItems()
			for keyword in self.set_keywords:
				self.DBKeywords.add(keyword)
			self.updateRemoveButtonState()
		except:
			pass
	
	
	def keywords(self):
		return tuple(self.set_keywords)
	
	
	def triggerReset(self,button=None):
		self.dockResetTriggered.emit()
	
	
	def updateRemoveButtonState(self):
		self.button_remove.setEnabled(len(self.list_keywords.selectedItems()) > 0)
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))
	
	
	def closeEvent(self,event=None):
		"""Save keywords DB to the file "FotoPreProcessor.keywords"."""
		if self.DBKeywords.wasChanged():
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
			keywords = list(self.DBKeywords.strings())
			if len(keywords) == 1: keywords = keywords[0]
			settings.setValue("Keywords",keywords)
		event.accept()



class FPPCopyrightDock(QtWidgets.QDockWidget):
	""""Class for the Copyright Dock Widget."""
	
	# new signal/slot mechanism: define custom signals
	dockResetTriggered = QtCore.pyqtSignal()
	dockDataUpdated = QtCore.pyqtSignal(str)
	dockKeywordRemoved = QtCore.pyqtSignal(str)
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtWidgets.QDockWidget.__init__(self,QtCore.QCoreApplication.translate("DockWidgets","Copyright Notice"))
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
		
		self.setFeatures(QtWidgets.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBCopyright = FotoPreProcessorTools.FPPStringDB()
		try:    self.DBCopyright.loadList([str(i) for i in settings.value("Copyright",list())])
		except: pass
		
		self.edit_copyright = QtWidgets.QLineEdit()
		self.completer = QtWidgets.QCompleter(self.DBCopyright.strings(),self.edit_copyright)
		self.edit_copyright.setCompleter(self.completer)
		
		box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Reset)
		self.button_reset = box_stdButtons.button(QtWidgets.QDialogButtonBox.Reset)
		
		layout_copyright = QtWidgets.QFormLayout()
		layout_copyright.addRow(
			QtCore.QCoreApplication.translate("DockWidgets","Photographer:"),
			self.edit_copyright
		)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addLayout(layout_copyright)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtWidgets.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.button_reset.clicked.connect(self.triggerReset)
		self.edit_copyright.editingFinished.connect(self.updateData)
		
		self.setCopyright()

	
	
	def setCopyright(self,notice=str()):
		try:
			notice = str(notice)
			if len(notice) > 0:
				self.DBCopyright.add(notice)
				self.completer.model().setStringList(self.DBCopyright.strings())
			self.edit_copyright.setText(notice) # moved to this pos so that it gets in any case
		except:
			pass
	
	
	def copyright(self):
		return str(self.edit_copyright.text())
	
	
	def triggerReset(self,button=None):
		self.dockResetTriggered.emit()
	
	
	def updateData(self):
		notice = str(self.edit_copyright.text())
		self.dockDataUpdated.emit(notice)
		self.DBCopyright.add(notice)
		self.completer.model().setStringList(self.DBCopyright.strings())
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))
	
	
	def closeEvent(self,event=None):
		"""Save copyright strings DB to the file "FotoPreProcessor.copyright"."""
		if self.DBCopyright.wasChanged():
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
			copyrights = list(self.DBCopyright.strings())
			if len(copyrights) == 1: copyrights = copyrights[0]
			settings.setValue("Copyright",copyrights)
		event.accept()



class FPPApplyChangesDialog(QtWidgets.QDialog):
	
	def __init__(self,ustr_path_exiftool,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtWidgets.QDialog.__init__(self,parent)
		self.progressbar = QtWidgets.QProgressBar()
		self.konsole = QtWidgets.QPlainTextEdit()
		self.konsole.setReadOnly(True)
		
		self.box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Cancel)
		self.button_execute = self.box_stdButtons.addButton(
			QtCore.QCoreApplication.translate("Dialog","Execute"),
			QtWidgets.QDialogButtonBox.ActionRole
		)
		self.button_add = self.box_stdButtons.addButton(
			QtCore.QCoreApplication.translate("Dialog","Add FFP file(s)"),
			QtWidgets.QDialogButtonBox.ActionRole
		)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(self.progressbar)
		layout.addWidget(self.konsole)
		layout.addWidget(self.box_stdButtons)
		
		self.setLayout(layout)
		
		self.button_execute.clicked.connect(self.execute)
		self.button_add.clicked.connect(self.addChangesFiles)
		self.box_stdButtons.rejected.connect(self.cancelOp)
		
		self.progressbar.hide()
		
		self.lst_commands = list()
		self.setStyleSheet(":disabled { color: gray; }")
		self.bool_isRunning = None
		self.dict_parameters = dict()
		self.ustr_path_exiftool = ustr_path_exiftool
	
	
	def addChangesFiles(self):
		filenames = QtWidgets.QFileDialog.getOpenFileNames(self)
		for filename in filenames:
			try:
				with open(filename,"r") as f:
					self.addParameters(yaml.safe_load(f))
			except FileNotFoundError:
				pass
	
	
	def calculate_commands(self):
		self.konsole.clear()
		self.lst_commands = list()
		for name,parameters in self.dict_parameters.items():
			command = [self.ustr_path_exiftool,"-P","-overwrite_original"]
			command.extend(parameters)
			command.append(name)
			self.konsole.appendPlainText(" ".join(command)+"\n")
			self.lst_commands.append(command)
		
		if len(self.dict_parameters) > 0:
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
			if settings.value("NamingEnabled",True) in ("true",True):
				# settings say files should be renamed: extract naming scheme
				namingScheme = settings.value("NamingScheme",FPPSettingsDialog.DEFAULT_NAMING_SCHEME)
				# construct command to rename all files;
				# naming scheme is given as a string of exiftool parameters:
				# split along whitespace characters
				command = [ self.ustr_path_exiftool,
					"-config",str(os.path.join(sys.path[0],"FotoPreProcessor.exiftool")),
					"-P",
					"-overwrite_original"
				]
#					"-d","%Y%m%d-%H%M%S",
#					"-FileName<${DateTimeOriginal}%-2nc-${FPPModel}.%le"
#				]
				command.extend(namingScheme.split())
				# parameter dict keys = all known files
				command.extend(self.dict_parameters.keys())
				# append command
				self.konsole.appendPlainText(" ".join(command)+"\n")
				self.lst_commands.append(command)
		else:
			# files not yet recorded: display hint
			self.konsole.appendHtml("<i>"+QtCore.QCoreApplication.translate("Dialog","There are no changes to apply.\nEither load a changes file or edit some pictures.")+"</i>\n")
	
	
	def addParameters(self,parameters):
		self.dict_parameters.update(parameters)
		self.calculate_commands()
	
	
	def cancelOp(self):
		if self.bool_isRunning == None:
			# dialog is in preview mode: cancel dialog
			self.reject()
			
		elif self.bool_isRunning == False:
			# dialog has executed commands: accept dialog
			self.accept()
			
		elif self.bool_isRunning == True:
			# dialog is executing commands: stop it via isRunning variable
			self.bool_isRunning = False
	
	
	def closeEvent(self,event=None):
		"""Catch close-by-upper-right-cross aka window close command.
This calls cancelOp to handle different states of command execution."""
		self.cancelOp()
	
	def execute(self):
		self.box_stdButtons.removeButton(self.button_execute)
		self.box_stdButtons.removeButton(self.button_add)
		self.progressbar.reset()
		self.progressbar.setRange(1,len(self.lst_commands))
		self.progressbar.setFormat("%v/%m")
		self.progressbar.show()
		self.konsole.clear()
		
		self.bool_isRunning = True
		for command in self.lst_commands:
			if not self.bool_isRunning:
				break
			try:
				self.konsole.appendPlainText(subprocess.check_output(command).decode())
			except:
				print("error while appending exiftool output:",sys.exc_info())
			self.progressbar.setValue(self.progressbar.value()+1)
			QtCore.QCoreApplication.processEvents() # make cancel button responsive...?
		
		if self.bool_isRunning:
			# command execution finished: remove cancel button, add close button
			# signal via isRunning that "close" should result in accept()
			self.bool_isRunning = False
			self.progressbar.hide()
			self.box_stdButtons.removeButton(self.box_stdButtons.button(QtWidgets.QDialogButtonBox.Cancel))
			self.box_stdButtons.addButton(QtWidgets.QDialogButtonBox.Close)
		else:
			# command execution was cancelled: close dialog, reject()
			self.reject()



class FPPSettingsDialog(QtWidgets.QDialog):
	
	DEFAULT_NAMING_SCHEME = "-d %Y%m%d-%H%M%S -FileName<${DateTimeOriginal}%-2nc-${FPPModel}.%le"
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtWidgets.QDialog.__init__(self,parent)
		self.bool_clearKeywords = False
		self.bool_clearCopyright = False
		self.settings = QtCore.QSettings()
		self.settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
		
		filesystemmodel = QtWidgets.QFileSystemModel()
		filesystemmodel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
		filesystemmodel.setRootPath("/")
		
		filecompleter = QtWidgets.QCompleter()
		filecompleter.setModel(filesystemmodel)
		
		self.edit_exiftool = QtWidgets.QLineEdit()
		self.edit_exiftool.setCompleter(filecompleter)
		
		self.edit_gimp = QtWidgets.QLineEdit()
		self.edit_gimp.setCompleter(filecompleter)
		
		button_find_exiftool = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("Dialog","..."))
		button_find_gimp = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("Dialog","..."))
		
		self.check_naming = QtWidgets.QCheckBox(QtCore.QCoreApplication.translate("Dialog","Rename files according to naming scheme below\nWARNING: an erroneous input may lead to damaged image files!"))
		self.edit_naming = QtWidgets.QLineEdit()
		self.edit_naming.setToolTip(QtCore.QCoreApplication.translate("Dialog","Enter filename related exiftool parameters, \ne.g. -d DATEFORMAT -FileName<NAMEFORMAT."))
		self.button_reset_naming = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("Dialog","Default"))
		
		self.spinbox_stepsize = QtWidgets.QSpinBox()
		self.spinbox_stepsize.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_stepsize.setRange(1,1024)
		
		self.spinbox_readsize = QtWidgets.QDoubleSpinBox() # 2013-01-08: due to limits of integer-based spinbox
		self.spinbox_readsize.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_readsize.setRange(1,10**20)
		self.spinbox_readsize.setDecimals(0) # emulate integer spin box for big ints
		self.spinbox_readsize.setSingleStep(2**5) # big ints, make step size multiple of 2
		
		self.spinbox_latitude = QtWidgets.QDoubleSpinBox()
		self.spinbox_latitude.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_latitude.setRange(-85,85)
		self.spinbox_latitude.setDecimals(8)
		self.spinbox_latitude.setSuffix(" °")
		self.spinbox_latitude.setSingleStep(1)
		self.spinbox_latitude.setWrapping(True)
		self.spinbox_latitude.setKeyboardTracking(False)
		
		self.spinbox_longitude = QtWidgets.QDoubleSpinBox()
		self.spinbox_longitude.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.Fixed)
		self.spinbox_longitude.setRange(-180,180)
		self.spinbox_longitude.setDecimals(8)
		self.spinbox_longitude.setSuffix(" °")
		self.spinbox_longitude.setSingleStep(1)
		self.spinbox_longitude.setWrapping(True)
		self.spinbox_longitude.setKeyboardTracking(False)
		
		button_lookUp = QtWidgets.QPushButton(QtCore.QCoreApplication.translate("DockWidgets","Look-Up..."))
		button_lookUp.setSizePolicy(QtWidgets.QSizePolicy.MinimumExpanding,QtWidgets.QSizePolicy.MinimumExpanding)
		
		box_stdButtons = QtWidgets.QDialogButtonBox(
			QtWidgets.QDialogButtonBox.Ok | QtWidgets.QDialogButtonBox.Cancel | QtWidgets.QDialogButtonBox.Reset
		)
		self.button_reset = box_stdButtons.button(QtWidgets.QDialogButtonBox.Reset)
		
		#-----------------------------------------------------------------------
		
		group_paths = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate("Dialog","Program Paths"))
		layout_exiftool = QtWidgets.QHBoxLayout()
		layout_exiftool.addWidget(self.edit_exiftool)
		layout_exiftool.addWidget(button_find_exiftool)
		layout_gimp = QtWidgets.QHBoxLayout()
		layout_gimp.addWidget(self.edit_gimp)
		layout_gimp.addWidget(button_find_gimp)
		layout_paths = QtWidgets.QFormLayout()
		layout_paths.addRow(QtCore.QCoreApplication.translate("Dialog","Exiftool:"),layout_exiftool)
		layout_paths.addRow(QtCore.QCoreApplication.translate("Dialog","The GIMP:"),layout_gimp)
		group_paths.setLayout(layout_paths)
		
		#-----------------------------------------------------------------------
		
		group_naming = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate("Dialog","File Naming"))
		layout_naming = QtWidgets.QVBoxLayout()
		layout_naming.addWidget(self.check_naming)
		layout_naming_edit = QtWidgets.QHBoxLayout()
		layout_naming_edit.addWidget(self.edit_naming)
		layout_naming_edit.addWidget(self.button_reset_naming)
		layout_naming.addLayout(layout_naming_edit)
		group_naming.setLayout(layout_naming)
		self.check_naming.setChecked(True)
		
		#-----------------------------------------------------------------------
		
		group_tuning = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate("Dialog","Performance Parameters"))
		layout_tuning = QtWidgets.QFormLayout()
		layout_tuning.addRow(QtCore.QCoreApplication.translate("Dialog","Image files read at once:"),self.spinbox_stepsize)
		layout_tuning.addRow(QtCore.QCoreApplication.translate("Dialog","Characters read at once:"),self.spinbox_readsize)
		group_tuning.setLayout(layout_tuning)
		
		#-----------------------------------------------------------------------
		
		group_geotag = QtWidgets.QGroupBox(QtCore.QCoreApplication.translate("Dialog","GeoTagging"))
		layout_coords = QtWidgets.QFormLayout()
		layout_coords.addRow(QtCore.QCoreApplication.translate("Dialog","Default latitude:"),self.spinbox_latitude)
		layout_coords.addRow(QtCore.QCoreApplication.translate("Dialog","Default longitude:"),self.spinbox_longitude)
		layout_geotag = QtWidgets.QHBoxLayout()
		layout_geotag.addLayout(layout_coords)
		layout_geotag.addWidget(button_lookUp)
		group_geotag.setLayout(layout_geotag)
		
		#-----------------------------------------------------------------------
		
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(group_paths)
		layout.addWidget(group_naming)
		layout.addWidget(group_tuning)
		layout.addWidget(group_geotag)
		layout.addWidget(box_stdButtons)
		
		self.setLayout(layout)
		
		#-----------------------------------------------------------------------
		
		box_stdButtons.accepted.connect(self.applyChangesAndAccept)
		box_stdButtons.rejected.connect(self.reject)
		self.button_reset.clicked.connect(self.resetValues)
		button_lookUp.clicked.connect(self.lookUpCoordinates)
		self.edit_exiftool.editingFinished.connect(self.exiftoolChanged)
		self.edit_gimp.editingFinished.connect(self.gimpChanged)
		button_find_exiftool.clicked.connect(self.selectExiftool)
		button_find_gimp.clicked.connect(self.selectTheGimp)
		self.spinbox_stepsize.editingFinished.connect(self.stepsizeChanged)
		self.spinbox_readsize.editingFinished.connect(self.readsizeChanged)
		self.spinbox_latitude.editingFinished.connect(self.latitudeChanged)
		self.spinbox_longitude.editingFinished.connect(self.longitudeChanged)
		self.check_naming.stateChanged.connect(self.checkNamingChanged)
		self.button_reset_naming.clicked.connect(self.resetNaming)
		self.edit_naming.editingFinished.connect(self.editNamingChanged)
		
		#-----------------------------------------------------------------------
		
		self.setStyleSheet(":disabled { color: gray; }")
		self.resetValues()
	
	
	def resetValues(self):
		try:    value = int(self.settings.value("StepSize",4))
		except: value = 4
		int_stepsize = value
		
		try:    value = int(self.settings.value("ReadSize",1024))
		except: value = 1024
		int_readsize = value
		
		try:    value = float(self.settings.value("DefaultLatitude",52.374444))
		except: value = 52.374444
		float_latitude = value
		
		try:    value = float(self.settings.value("DefaultLongitude",9.738611))
		except: value = 9.738611
		float_longitude = value
		
		self.edit_exiftool.setText(self.settings.value("ExiftoolPath","/usr/bin/exiftool"))
		self.edit_gimp.setText(self.settings.value("TheGimpPath","/usr/bin/gimp"))
		self.spinbox_stepsize.setValue(int_stepsize)
		self.spinbox_readsize.setValue(int_readsize)
		self.spinbox_latitude.setValue(float_latitude)
		self.spinbox_longitude.setValue(float_longitude)
		self.edit_naming.setText(self.settings.value("NamingScheme",self.DEFAULT_NAMING_SCHEME))
		self.check_naming.setChecked(self.settings.value("NamingEnabled",True) in ("true",True))
		self.button_reset.setEnabled(False)
	
	
	def applyChangesAndAccept(self):
		self.settings.setValue("StepSize",self.spinbox_stepsize.value())
		self.settings.setValue("ReadSize",self.spinbox_readsize.value())
		self.settings.setValue("ExiftoolPath",self.edit_exiftool.text())
		self.settings.setValue("TheGimpPath",self.edit_gimp.text())
		self.settings.setValue("DefaultLatitude",self.spinbox_latitude.value())
		self.settings.setValue("DefaultLongitude",self.spinbox_longitude.value())
		self.settings.setValue("NamingScheme",self.edit_naming.text())
		self.settings.setValue("NamingEnabled",self.check_naming.isChecked())
		self.button_reset.setEnabled(False)
		self.accept()
	
	
	def exiftoolChanged(self):
		self.button_reset.setEnabled(
			self.edit_exiftool.text() != self.settings.value("ExiftoolPath","/usr/bin/exiftool")
		)
	
	
	def gimpChanged(self):
		self.button_reset.setEnabled(
			self.edit_gimp.text() != self.settings.value("TheGimpPath","/usr/bin/gimp")
		)
	
	
	def selectExiftool(self):
		path = QtWidgets.QFileDialog.getOpenFileName(self,
			QtCore.QCoreApplication.translate("Dialog","Select Exiftool Executable"),
			self.edit_exiftool.text(),
			"","",
			QtWidgets.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.edit_exiftool.setText(path)
	
	
	def selectTheGimp(self):
		path = QtWidgets.QFileDialog.getOpenFileName(self,
			QtCore.QCoreApplication.translate("Dialog","Select The GIMP Executable"),
			self.edit_gimp.text(),
			"","",
			QtWidgets.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.edit_exiftool.setText(path)
	
	
	def stepsizeChanged(self):
		try:    value = int(self.settings.value("StepSize",4))
		except: value = 4
		self.button_reset.setEnabled( self.spinbox_stepsize.value() != value )
	
	
	def readsizeChanged(self):
		try:    value = int(self.settings.value("ReadSize",1024))
		except: value = 1024
		self.button_reset.setEnabled( self.spinbox_readsize.value() != value )
	
	
	def latitudeChanged(self):
		try:    value = float(self.settings.value("DefaultLatitude",52.374444))
		except: value = 52.374444
		self.button_reset.setEnabled( self.spinbox_latitude.value() != value )
	
	
	def longitudeChanged(self):
		try:    value = float(self.settings.value("DefaultLongitude",9.738611))
		except: value = 9.738611
		self.button_reset.setEnabled( self.spinbox_longitude.value() != value )
	
	
	def editNamingChanged(self):
		self.button_reset.setEnabled(
			self.edit_naming.text() != self.settings.value("NamingScheme",self.DEFAULT_NAMING_SCHEME)
		)
	
	def checkNamingChanged(self):
		self.edit_naming.setEnabled(self.check_naming.isChecked())
		self.button_reset_naming.setEnabled(self.check_naming.isChecked())
	
	
	def resetNaming(self):
		self.edit_naming.setText(self.DEFAULT_NAMING_SCHEME)
	
	
	def lookUpCoordinates(self):
		latitude = self.spinbox_latitude.value()
		longitude = self.spinbox_longitude.value()
		
		if latitude <= self.spinbox_latitude.minimum():   latitude = None
		if longitude <= self.spinbox_longitude.minimum(): longitude = None
		
		dlg = FotoPreProcessorTools.FPPGeoTaggingDialog()
		
		if latitude != None and longitude != None:
			dlg.setLocation(latitude,longitude,0.0)
		else:
			dlg.setLocation(52.374444,9.738611,0.0)
		
		if dlg.exec_() == QtWidgets.QDialog.Accepted:
			try:
				(latitude,longitude,elevation) = dlg.location()
				latitude = float(latitude)
				longitude = float(longitude)
			except:
				latitude = self.spinbox_latitude.minimum()
				longitude = self.spinbox_longitude.minimum()
			self.spinbox_latitude.setValue(latitude)
			self.spinbox_longitude.setValue(longitude)



class FPPAboutDialog(QtWidgets.QDialog):
	
	def __init__(self,version,parent=None):
		"""Constructor; initialise fields, construct GUI."""
		QtWidgets.QDialog.__init__(self,parent)
		
		label_icon = QtWidgets.QLabel()
		label_icon.setPixmap(QtGui.QPixmap(
			os.path.join(sys.path[0],"icons","FPP.png")
		))
		
		label_info = QtWidgets.QLabel()
		label_info.setText(QtCore.QCoreApplication.translate("Dialog","""<h4>FotoPreProcessor</h4>
<p>PyQt4-based (EXIF) metadata management of images in a directory.</p>
<p>Copyright (C) 2012-2015 Frank Abelbeck &#60;frank.abelbeck@googlemail.com&#62;</p>
<p>Version {version}</p>""").format(version=version))
		
		widget_info = QtWidgets.QWidget()
		layout_info = QtWidgets.QHBoxLayout()
		layout_info.addWidget(label_icon)
		layout_info.addWidget(label_info)
		widget_info.setLayout(layout_info)
		
		widget_license = QtWidgets.QPlainTextEdit()
		widget_license.setReadOnly(True)
		with open(os.path.join(sys.path[0],"COPYING"),"r") as f:
			widget_license.setPlainText(f.read())
		
		tabwidget = QtWidgets.QTabWidget()
		tabwidget.addTab(widget_info,QtCore.QCoreApplication.translate("Dialog","General Information"))
		tabwidget.addTab(widget_license,QtCore.QCoreApplication.translate("Dialog","License"))
		
		box_stdButtons = QtWidgets.QDialogButtonBox(QtWidgets.QDialogButtonBox.Close)
		
		layout = QtWidgets.QVBoxLayout()
		layout.addWidget(tabwidget)
		layout.addWidget(box_stdButtons)
		
		self.setLayout(layout)
		
		box_stdButtons.rejected.connect(self.accept)


