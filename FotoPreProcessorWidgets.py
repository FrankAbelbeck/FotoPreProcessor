#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FotoPreProcessorWidgets: custom dock widgets and application/settings dialogs
Copyright (C) 2012 Frank Abelbeck <frank.abelbeck@googlemail.com>

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

$Id$
"""

import subprocess,sys,os.path,codecs,re,time

from PyQt4 import QtGui, QtCore

import FotoPreProcessorTools


class FPPGeoTaggingDock(QtGui.QDockWidget):
	""""Class for the GeoTagging Dock Widget."""
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtGui.QDockWidget.__init__(self,QtCore.QCoreApplication.translate(u"DockWidgets",u"GeoTagging"))
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		#
		# setup GUI
		#
		button_lookUp = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Look-Up..."))
		box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset)
		box_stdButtons.addButton(button_lookUp,QtGui.QDialogButtonBox.ActionRole)
		self.button_reset = box_stdButtons.button(QtGui.QDialogButtonBox.Reset)
		
		self.spinbox_latitude = QtGui.QDoubleSpinBox()
		self.spinbox_latitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_latitude.setRange(-85,85)
		self.spinbox_latitude.setDecimals(8)
		self.spinbox_latitude.setSuffix(u" °")
		self.spinbox_latitude.setSingleStep(1)
		self.spinbox_latitude.setWrapping(True)
		self.spinbox_latitude.setSpecialValueText(QtCore.QCoreApplication.translate(u"DockWidgets",u"undefined"))
		self.spinbox_latitude.setKeyboardTracking(False)
		
		self.spinbox_longitude = QtGui.QDoubleSpinBox()
		self.spinbox_longitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_longitude.setRange(-180,180)
		self.spinbox_longitude.setDecimals(8)
		self.spinbox_longitude.setSuffix(u" °")
		self.spinbox_longitude.setSingleStep(1)
		self.spinbox_longitude.setWrapping(True)
		self.spinbox_longitude.setSpecialValueText(QtCore.QCoreApplication.translate(u"DockWidgets",u"undefined"))
		self.spinbox_longitude.setKeyboardTracking(False)
		
		self.spinbox_elevation = QtGui.QDoubleSpinBox()
		self.spinbox_elevation.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_elevation.setRange(-11000,9000)
		self.spinbox_elevation.setDecimals(1)
		self.spinbox_elevation.setSuffix(u" m")
		self.spinbox_elevation.setSingleStep(1)
		self.spinbox_elevation.setKeyboardTracking(False)
		
		layout_coordinates = QtGui.QFormLayout()
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Latitude:"),
			self.spinbox_latitude
		)
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Longitude:"),
			self.spinbox_longitude
		)
		layout_coordinates.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Elevation:"),
			self.spinbox_elevation
		)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_coordinates)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.connect(
			button_lookUp,
			QtCore.SIGNAL('clicked()'),
			self.lookUpCoordinates
		)
		self.connect(
			self.button_reset,
			QtCore.SIGNAL('clicked()'),
			self.triggerReset
		)
		self.connect(
			self.spinbox_latitude,
			QtCore.SIGNAL('editingFinished()'),
			self.updateData
		)
		self.connect(
			self.spinbox_longitude,
			QtCore.SIGNAL('editingFinished()'),
			self.updateData
		)
		self.connect(
			self.spinbox_elevation,
			QtCore.SIGNAL('editingFinished()'),
			self.updateData
		)
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
			settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
			
			(latitude,ok) = settings.value(u"DefaultLatitude",52.374444).toFloat()
			if not ok: latitude = 52.374444
			
			longitude,ok = settings.value(u"DefaultLongitude",9.738611).toFloat()
			if not ok: longitude = 9.738611
			
			dlg.setLocation(latitude,longitude,0.0)
		
		if dlg.exec_() == QtGui.QDialog.Accepted:
			try:
				(latitude,longitude,elevation) = dlg.location()
				self.setLocation(latitude,longitude,elevation)
				self.updateData()
			except:
				pass
	
	
	def triggerReset(self):
		self.emit(QtCore.SIGNAL("dockResetTriggered()"))
	
	
	def updateData(self):
		(latitude,longitude,elevation) = self.location()
		if (latitude != None) and (longitude != None):
			self.emit(
				QtCore.SIGNAL("dockDataUpdated(PyQt_PyObject)"),
				(latitude,longitude,elevation)
			)
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))



class FPPTimezonesDock(QtGui.QDockWidget):
	""""Class for the Timezone Correction Dock Widget."""
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Parameter timezoneNames is used to populate the timezone combo boxes.
It should be a tuple of valid timezone names like "Europe/Berlin".

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtGui.QDockWidget.__init__(self,QtCore.QCoreApplication.translate(u"DockWidgets",u"Timezone Correction"))
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.tz = FotoPreProcessorTools.FPPTimezone()
		self.tz.loadTimezoneDB()
		
		#
		# setup GUI
		#
		self.button_fromTz = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"by location"))
		self.button_fromTz.setToolTip(QtCore.QCoreApplication.translate(u"DockWidgets",u"Use given coordinates to estimate timezone."))

		self.button_toTz = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"by location"))
		self.button_toTz.setToolTip(QtCore.QCoreApplication.translate(u"DockWidgets",u"Use given coordinates to estimate timezone."))
		
		self.combo_fromTz = QtGui.QComboBox()
		self.combo_toTz = QtGui.QComboBox()
		
		self.combo_fromTz.addItems(self.tz.timezoneNames())
		self.combo_toTz.addItems(self.tz.timezoneNames())
		
		box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset)
		self.button_reset = box_stdButtons.button(QtGui.QDialogButtonBox.Reset)
		
		layout_fromTz = QtGui.QHBoxLayout()
		layout_fromTz.addWidget(self.combo_fromTz)
		layout_fromTz.addWidget(self.button_fromTz)
		
		layout_toTz = QtGui.QHBoxLayout()
		layout_toTz.addWidget(self.combo_toTz)
		layout_toTz.addWidget(self.button_toTz)
		
		layout_timezones= QtGui.QFormLayout()
		layout_timezones.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"From:"),
			layout_fromTz
		)
		layout_timezones.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Shift to:"),
			layout_toTz
		)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_timezones)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.connect(
			self.button_reset,
			QtCore.SIGNAL('clicked()'),
			self.triggerReset
		)
		self.connect(
			self.combo_fromTz,
			QtCore.SIGNAL('activated(int)'),
			self.updateData
		)
		self.connect(
			self.combo_toTz,
			QtCore.SIGNAL('activated(int)'),
			self.updateData
		)
		self.connect(
			self.button_fromTz,
			QtCore.SIGNAL('clicked()'),
			self.setFromTimezoneByCoordinates
		)
		self.connect(
			self.button_toTz,
			QtCore.SIGNAL('clicked()'),
			self.setToTimezoneByCoordinates
		)
		self.setTimezones()
		self.setLocation()
	
	
	def setTimezones(self,fromTz=None,toTz=None):
		if fromTz == None: fromTz = u"UTC"
		if toTz == None:   toTz   = u"UTC"
		try:
			int_fromTz = self.tz.timezoneIndex(unicode(fromTz))
			int_toTz   = self.tz.timezoneIndex(unicode(toTz))
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
		return (unicode(self.combo_fromTz.currentText()),unicode(self.combo_toTz.currentText()))
	
	
	def triggerReset(self):
		self.emit(QtCore.SIGNAL("dockResetTriggered()"))
	
	
	def updateData(self,value=None):
		try:
			fromTz = unicode(self.combo_fromTz.currentText())
			toTz = unicode(self.combo_toTz.currentText())
			self.emit(QtCore.SIGNAL("dockDataUpdated(PyQt_PyObject)"),(fromTz,toTz))
		except:
			pass
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))



class FPPKeywordsDock(QtGui.QDockWidget):
	""""Class for the Keywords Dock Widget."""
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtGui.QDockWidget.__init__(self,QtCore.QCoreApplication.translate(u"DockWidgets",u"Keywords"))
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBKeywords = FotoPreProcessorTools.FPPStringDB()
		try:    self.DBKeywords.loadList([unicode(i) for i in settings.value(u"Keywords",list()).toStringList()])
		except: pass
		
		#
		# setup GUI
		#
		#---------------------------------------------------------------
		# Keywords dock
		#---------------------------------------------------------------
		self.list_keywords = QtGui.QListWidget()
		self.list_keywords.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		
		self.button_add = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Add..."))
		self.button_remove = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Remove"))
		
		box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset)
		box_stdButtons.addButton(self.button_add,QtGui.QDialogButtonBox.ActionRole)
		box_stdButtons.addButton(self.button_remove,QtGui.QDialogButtonBox.ActionRole)
		self.button_reset = box_stdButtons.button(QtGui.QDialogButtonBox.Reset)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.list_keywords)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.connect(
			self.list_keywords,
			QtCore.SIGNAL('itemSelectionChanged()'),
			self.updateRemoveButtonState
		)
		self.connect(
			self.button_add,
			QtCore.SIGNAL('clicked()'),
			self.addKeyword
		)
		self.connect(
			self.button_remove,
			QtCore.SIGNAL('clicked()'),
			self.removeKeyword
		)
		self.connect(
			self.button_reset,
			QtCore.SIGNAL('clicked()'),
			self.triggerReset
		)
		self.setKeywords()
	
	
	def addKeyword(self):
		tpl_keywords = self.DBKeywords.strings()
		(keyword,ok) = QtGui.QInputDialog.getItem(self,
			QtCore.QCoreApplication.translate(u"Dialog",u"Add new Keyword"),
			QtCore.QCoreApplication.translate(u"Dialog",u"Please provide a keyword for the selected images:"),
			tpl_keywords,0,True
		)
		if ok:
			keyword = unicode(keyword)
			if not keyword in self.set_keywords:
				self.DBKeywords.add(keyword)
				self.set_keywords.add(keyword)
				self.list_keywords.addItem(keyword)
				self.list_keywords.sortItems()
				self.emit(QtCore.SIGNAL("dockKeywordAdded(PyQt_PyObject)"),keyword)
				self.updateRemoveButtonState()
			else:
				answer = QtGui.QMessageBox.information(
					self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Keyword Already Exists"),
					QtCore.QCoreApplication.translate(u"Dialog",u"Such a keyword is already in the list and hence will be ignored.")
				)
	
	
	def removeKeyword(self):
		for item in self.list_keywords.selectedItems():
			self.list_keywords.takeItem(self.list_keywords.row(item))
			self.set_keywords.remove(unicode(item.text()))
			self.emit(QtCore.SIGNAL("dockKeywordRemoved(PyQt_PyObject)"),unicode(item.text()))
		self.list_keywords.sortItems()
		self.updateRemoveButtonState()
	
	
	def setKeywords(self,keywords=tuple()):
		try:
			self.set_keywords = set([unicode(i) for i in keywords])
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
		self.emit(QtCore.SIGNAL("dockResetTriggered()"))
	
	
	def updateRemoveButtonState(self):
		self.button_remove.setEnabled(len(self.list_keywords.selectedItems()) > 0)
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))
	
	
	def closeEvent(self,event=None):
		"""Save keywords DB to the file "FotoPreProcessor.keywords"."""
		if self.DBKeywords.wasChanged():
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
			keywords = list(self.DBKeywords.strings())
			if len(keywords) == 1: keywords = keywords[0]
			settings.setValue(u"Keywords",keywords)
		event.accept()



class FPPCopyrightDock(QtGui.QDockWidget):
	""""Class for the Copyright Dock Widget."""
	
	def __init__(self):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtGui.QDockWidget.__init__(self,QtCore.QCoreApplication.translate(u"DockWidgets",u"Copyright Notice"))
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBCopyright = FotoPreProcessorTools.FPPStringDB()
		try:    self.DBCopyright.loadList([unicode(i) for i in settings.value(u"Copyright",list()).toStringList()])
		except: pass
		
		self.edit_copyright = QtGui.QLineEdit()
		self.completer = QtGui.QCompleter(self.DBCopyright.strings(),self.edit_copyright)
		self.edit_copyright.setCompleter(self.completer)
		
		box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Reset)
		self.button_reset = box_stdButtons.button(QtGui.QDialogButtonBox.Reset)
		
		layout_copyright = QtGui.QFormLayout()
		layout_copyright.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Photographer:"),
			self.edit_copyright
		)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_copyright)
		layout.addWidget(box_stdButtons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.connect(
			self.button_reset,
			QtCore.SIGNAL('clicked()'),
			self.triggerReset
		)
		self.connect(
			self.edit_copyright,
			QtCore.SIGNAL('editingFinished()'),
			self.updateData
		)
		self.setCopyright()
	
	
	def setCopyright(self,notice=unicode()):
		try:
			notice = unicode(notice)
			if len(notice) > 0:
				self.edit_copyright.setText(notice)
				self.DBCopyright.add(notice)
				self.completer.model().setStringList(self.DBCopyright.strings())
		except:
			pass
	
	
	def copyright(self):
		return unicode(self.edit_copyright.text())
	
	
	def triggerReset(self,button=None):
		self.emit(QtCore.SIGNAL("dockResetTriggered()"))
	
	
	def updateData(self):
		notice = unicode(self.edit_copyright.text())
		self.emit(QtCore.SIGNAL("dockDataUpdated(PyQt_PyObject)"),notice)
		self.DBCopyright.add(notice)
		self.completer.model().setStringList(self.DBCopyright.strings())
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))
	
	
	def closeEvent(self,event=None):
		"""Save copyright strings DB to the file "FotoPreProcessor.copyright"."""
		if self.DBCopyright.wasChanged():
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
			copyrights = list(self.DBCopyright.strings())
			if len(copyrights) == 1: copyrights = copyrights[0]
			settings.setValue(u"Copyright",copyrights)
		event.accept()



class FPPApplyChangesDialog(QtGui.QDialog):
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtGui.QDialog.__init__(self,parent)
		self.progressbar = QtGui.QProgressBar()
		self.konsole = QtGui.QPlainTextEdit()
		self.konsole.setReadOnly(True)
		
		self.box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel)
		self.button_execute = self.box_stdButtons.addButton(
			QtCore.QCoreApplication.translate(u"Dialog",u"Execute"),
			QtGui.QDialogButtonBox.ActionRole
		)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.progressbar)
		layout.addWidget(self.konsole)
		layout.addWidget(self.box_stdButtons)
		
		self.setLayout(layout)
	
		self.connect(
			self.button_execute,
			QtCore.SIGNAL('clicked()'),
			self.execute
		)
		self.connect(
			self.box_stdButtons,
			QtCore.SIGNAL('rejected()'),
			self.cancelOp
		)
		self.lst_commands = list()
		
		self.progressbar.hide()
		self.setStyleSheet(u":disabled { color: gray; }")
		self.bool_isRunning = None
	
	
	def addCommand(self,command=tuple()):
		try:
			self.lst_commands.append(tuple(command))
			self.konsole.appendPlainText(u" ".join(tuple(command))+u"\n")
		except:
			pass
	
	
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
	
	
	def execute(self):
		self.box_stdButtons.removeButton(self.button_execute)
		
		self.progressbar.reset()
		self.progressbar.setRange(0,len(self.lst_commands))
		self.progressbar.setFormat(u"%v/%m")
		self.progressbar.show()
		self.konsole.clear()
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
		
		self.bool_isRunning = True
		for command in self.lst_commands:
			if not self.bool_isRunning:
				break
			try:
				self.konsole.appendPlainText(subprocess.check_output(command))
			except:
				pass
			self.progressbar.setValue(self.progressbar.value()+1)
			QtCore.QCoreApplication.processEvents() # make cancel button responsive...?
		
		if self.bool_isRunning:
			# command execution finished: remove cancel button, add close button
			# signal via isRunning that "close" should result in accept()
			self.bool_isRunning = False
			self.progressbar.hide()
			self.box_stdButtons.removeButton(self.box_stdButtons.button(QtGui.QDialogButtonBox.Cancel))
			self.box_stdButtons.addButton(QtGui.QDialogButtonBox.Close)
		else:
			# command execution was cancelled: close dialog, reject()
			self.reject()



class FPPSettingsDialog(QtGui.QDialog):
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtGui.QDialog.__init__(self,parent)
		self.bool_clearKeywords = False
		self.bool_clearCopyright = False
		self.settings = QtCore.QSettings()
		self.settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
		
		filesystemmodel = QtGui.QFileSystemModel()
		filesystemmodel.setFilter(QtCore.QDir.NoDotAndDotDot | QtCore.QDir.AllDirs)
		filesystemmodel.setRootPath("/")
		
		filecompleter = QtGui.QCompleter()
		filecompleter.setModel(filesystemmodel)
		
		self.edit_exiftool = QtGui.QLineEdit()
		self.edit_exiftool.setCompleter(filecompleter)
		
		self.edit_gimp = QtGui.QLineEdit()
		self.edit_gimp.setCompleter(filecompleter)
		
		button_find_exiftool = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"..."))
		button_find_gimp = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"..."))
		
		#self.edit_naming = QtGui.QLineEdit()
		#self.label_naming = QtGui.QLabel()
		#self.button_help_naming = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"Help"))
		
		self.spinbox_stepsize = QtGui.QSpinBox()
		self.spinbox_stepsize.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_stepsize.setRange(1,1024)
		
		self.spinbox_readsize = QtGui.QSpinBox()
		self.spinbox_readsize.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_readsize.setRange(1,10240)
		
		self.spinbox_latitude = QtGui.QDoubleSpinBox()
		self.spinbox_latitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_latitude.setRange(-85,85)
		self.spinbox_latitude.setDecimals(8)
		self.spinbox_latitude.setSuffix(u" °")
		self.spinbox_latitude.setSingleStep(1)
		self.spinbox_latitude.setWrapping(True)
		self.spinbox_latitude.setKeyboardTracking(False)
		
		self.spinbox_longitude = QtGui.QDoubleSpinBox()
		self.spinbox_longitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spinbox_longitude.setRange(-180,180)
		self.spinbox_longitude.setDecimals(8)
		self.spinbox_longitude.setSuffix(u" °")
		self.spinbox_longitude.setSingleStep(1)
		self.spinbox_longitude.setWrapping(True)
		self.spinbox_longitude.setKeyboardTracking(False)
		
		button_lookUp = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Look-Up..."))
		button_lookUp.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.MinimumExpanding)
		
		box_stdButtons = QtGui.QDialogButtonBox(
			QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel | QtGui.QDialogButtonBox.Reset
		)
		self.button_reset = box_stdButtons.button(QtGui.QDialogButtonBox.Reset)
		
		#-----------------------------------------------------------------------
		
		group_paths = QtGui.QGroupBox(QtCore.QCoreApplication.translate(u"Dialog",u"Program Paths"))
		layout_exiftool = QtGui.QHBoxLayout()
		layout_exiftool.addWidget(self.edit_exiftool)
		layout_exiftool.addWidget(button_find_exiftool)
		layout_gimp = QtGui.QHBoxLayout()
		layout_gimp.addWidget(self.edit_gimp)
		layout_gimp.addWidget(button_find_gimp)
		layout_paths = QtGui.QFormLayout()
		layout_paths.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"Exiftool:"),layout_exiftool)
		layout_paths.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"The GIMP:"),layout_gimp)
		group_paths.setLayout(layout_paths)
		
		#-----------------------------------------------------------------------
		
		#group_naming = QtGui.QGroupBox(QtCore.QCoreApplication.translate(u"Dialog",u"Naming Scheme"))
		#layout_naming_edit = QtGui.QVBoxLayout()
		#layout_naming_edit.addWidget(self.edit_naming)
		#layout_naming_edit.addWidget(self.label_naming)
		#layout_naming = QtGui.QHBoxLayout()
		#layout_naming.addLayout(layout_naming_edit)
		#layout_naming.addWidget(self.button_help_naming)
		#group_naming.setLayout(layout_naming)
		#group_naming.setEnabled(False)
		
		#-----------------------------------------------------------------------
		
		group_tuning = QtGui.QGroupBox(QtCore.QCoreApplication.translate(u"Dialog",u"Performance Parameters"))
		layout_tuning = QtGui.QFormLayout()
		layout_tuning.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"Image files read at once:"),self.spinbox_stepsize)
		layout_tuning.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"Characters read at once:"),self.spinbox_readsize)
		group_tuning.setLayout(layout_tuning)
		
		#-----------------------------------------------------------------------
		
		group_geotag = QtGui.QGroupBox(QtCore.QCoreApplication.translate(u"Dialog",u"GeoTagging"))
		layout_coords = QtGui.QFormLayout()
		layout_coords.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"Default latitude:"),self.spinbox_latitude)
		layout_coords.addRow(QtCore.QCoreApplication.translate(u"Dialog",u"Default longitude:"),self.spinbox_longitude)
		layout_geotag = QtGui.QHBoxLayout()
		layout_geotag.addLayout(layout_coords)
		layout_geotag.addWidget(button_lookUp)
		group_geotag.setLayout(layout_geotag)
		
		#-----------------------------------------------------------------------
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(group_paths)
		#layout.addWidget(group_naming)
		layout.addWidget(group_tuning)
		layout.addWidget(group_geotag)
		layout.addWidget(box_stdButtons)
		
		self.setLayout(layout)
		
		#-----------------------------------------------------------------------
		
		self.connect(
			box_stdButtons,
			QtCore.SIGNAL('accepted()'),
			self.applyChangesAndAccept
		)
		self.connect(
			box_stdButtons,
			QtCore.SIGNAL('rejected()'),
			self.reject
		)
		self.connect(
			self.button_reset,
			QtCore.SIGNAL('clicked()'),
			self.resetValues
		)
		self.connect(
			button_lookUp,
			QtCore.SIGNAL('clicked()'),
			self.lookUpCoordinates
		)
		self.connect(
			self.edit_exiftool,
			QtCore.SIGNAL('editingFinished()'),
			self.exiftoolChanged
		)
		self.connect(
			self.edit_gimp,
			QtCore.SIGNAL('editingFinished()'),
			self.gimpChanged
		)
		self.connect(
			button_find_exiftool,
			QtCore.SIGNAL('clicked()'),
			self.selectExiftool
		)
		self.connect(
			button_find_gimp,
			QtCore.SIGNAL('clicked()'),
			self.selectTheGimp
		)
		self.connect(
			self.spinbox_stepsize,
			QtCore.SIGNAL('editingFinished()'),
			self.stepsizeChanged
		)
		self.connect(
			self.spinbox_readsize,
			QtCore.SIGNAL('editingFinished()'),
			self.readsizeChanged
		)
		
		self.connect(
			self.spinbox_latitude,
			QtCore.SIGNAL('editingFinished()'),
			self.latitudeChanged
		)
		self.connect(
			self.spinbox_longitude,
			QtCore.SIGNAL('editingFinished()'),
			self.longitudeChanged
		)
		#-----------------------------------------------------------------------
		
		self.setStyleSheet(u":disabled { color: gray; }")
		self.resetValues()
	
	
	def resetValues(self):
		(value,ok) = self.settings.value(u"StepSize",4).toInt()
		if ok: int_stepsize = value
		else:  int_stepsize = 4
		
		(value,ok) = self.settings.value(u"ReadSize",1024).toInt()
		if ok: int_readsize = value
		else:  int_readsize = 1024
		
		(value,ok) = self.settings.value(u"DefaultLatitude",52.374444).toFloat()
		if ok: float_latitude = value
		else:  float_latitude = 52.374444
		
		(value,ok) = self.settings.value(u"DefaultLongitude",9.738611).toFloat()
		if ok: float_longitude = value
		else:  float_longitude = 9.738611
		
		self.edit_exiftool.setText(self.settings.value(u"ExiftoolPath",u"/usr/bin/exiftool").toString())
		self.edit_gimp.setText(self.settings.value(u"TheGimpPath",u"/usr/bin/gimp").toString())
		self.spinbox_stepsize.setValue(int_stepsize)
		self.spinbox_readsize.setValue(int_readsize)
		self.spinbox_latitude.setValue(float_latitude)
		self.spinbox_longitude.setValue(float_longitude)
		
		self.button_reset.setEnabled(False)
	
	
	def applyChangesAndAccept(self):
		self.settings.setValue(u"StepSize",self.spinbox_stepsize.value())
		self.settings.setValue(u"ReadSize",self.spinbox_readsize.value())
		self.settings.setValue(u"ExiftoolPath",self.edit_exiftool.text())
		self.settings.setValue(u"TheGimpPath",self.edit_gimp.text())
		self.settings.setValue(u"DefaultLatitude",self.spinbox_latitude.value())
		self.settings.setValue(u"DefaultLongitude",self.spinbox_longitude.value())
		self.button_reset.setEnabled(False)
		self.accept()
	
	
	def exiftoolChanged(self):
		self.button_reset.setEnabled(
			self.edit_exiftool.text() != self.settings.value(u"ExiftoolPath",u"/usr/bin/exiftool").toString()
		)
	
	
	def gimpChanged(self):
		self.button_reset.setEnabled(
			self.edit_gimp.text() != self.settings.value(u"TheGimpPath",u"/usr/bin/gimp").toString()
		)
	
	
	def selectExiftool(self):
		path = QtGui.QFileDialog.getOpenFileName(self,
			QtCore.QCoreApplication.translate(u"Dialog",u"Select Exiftool Executable"),
			self.edit_exiftool.text(),
			u"",u"",
			QtGui.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.edit_exiftool.setText(path)
	
	
	def selectTheGimp(self):
		path = QtGui.QFileDialog.getOpenFileName(self,
			QtCore.QCoreApplication.translate(u"Dialog",u"Select The GIMP Executable"),
			self.edit_gimp.text(),
			u"",u"",
			QtGui.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.edit_exiftool.setText(path)
	
	
	def stepsizeChanged(self):
		(value,ok) = self.settings.value(u"StepSize",4).toInt()
		if not ok: value = 4
		self.button_reset.setEnabled( self.spinbox_stepsize.value() != value )
	
	
	def readsizeChanged(self):
		(value,ok) = self.settings.value(u"ReadSize",1024).toInt()
		if not ok: value = 1024
		self.button_reset.setEnabled( self.spinbox_readsize.value() != value )
	
	
	def latitudeChanged(self):
		(value,ok) = self.settings.value(u"DefaultLatitude",52.374444).toFloat()
		if not ok: value = 52.374444
		self.button_reset.setEnabled( self.spinbox_latitude.value() != value )
	
	
	def longitudeChanged(self):
		(value,ok) = self.settings.value(u"DefaultLongitude",9.738611).toFloat()
		if not ok: value = 9.738611
		self.button_reset.setEnabled( self.spinbox_longitude.value() != value )
	
	
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
		
		if dlg.exec_() == QtGui.QDialog.Accepted:
			try:
				(latitude,longitude,elevation) = dlg.location()
				latitude = float(latitude)
				longitude = float(longitude)
			except:
				latitude = self.spinbox_latitude.minimum()
				longitude = self.spinbox_longitude.minimum()
			self.spinbox_latitude.setValue(latitude)
			self.spinbox_longitude.setValue(longitude)



class FPPAboutDialog(QtGui.QDialog):
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, construct GUI."""
		QtGui.QDialog.__init__(self,parent)
		
		label_icon = QtGui.QLabel()
		label_icon.setPixmap(QtGui.QPixmap(
			os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"icons",u"FPP.png")
		))
		
		int_revision = 0
		for filename in (u"FotoPreProcessor.py",u"FotoPreProcessorItem.py",u"FotoPreProcessorTools.py",u"FotoPreProcessorWidgets.py"):
			with codecs.open(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),filename),u"r") as f:
				for line in f:
					if line.startswith("$Id"):
						rev = int(re.match(r'^\$Id:\ .*\ (\d+)\ .*',line).groups()[0])
						if rev > int_revision: int_revision = rev
		ustr_revision = unicode(int_revision)
		
		label_info = QtGui.QLabel()
		label_info.setText(QtCore.QCoreApplication.translate(u"Dialog",u"""<h4>FotoPreProcessor</h4>
<p>PyQt4-based (EXIF) metadata management of images in a directory.</p>
<p>Copyright (C) 2012 Frank Abelbeck &#60;frank.abelbeck@googlemail.com&#62;</p>
<p>Revision %1</p>""").arg(ustr_revision))
		
		widget_info = QtGui.QWidget()
		layout_info = QtGui.QHBoxLayout()
		layout_info.addWidget(label_icon)
		layout_info.addWidget(label_info)
		widget_info.setLayout(layout_info)
		
		widget_license = QtGui.QPlainTextEdit()
		widget_license.setReadOnly(True)
		with open(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"COPYING"),u"r") as f:
			widget_license.setPlainText(f.read())
		
		tabwidget = QtGui.QTabWidget()
		tabwidget.addTab(widget_info,QtCore.QCoreApplication.translate(u"Dialog",u"General Information"))
		tabwidget.addTab(widget_license,QtCore.QCoreApplication.translate(u"Dialog",u"License"))
		
		box_stdButtons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Close)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(tabwidget)
		layout.addWidget(box_stdButtons)
		
		self.setLayout(layout)
		
		self.connect(
			box_stdButtons,
			QtCore.SIGNAL('rejected()'),
			self.accept
		)


