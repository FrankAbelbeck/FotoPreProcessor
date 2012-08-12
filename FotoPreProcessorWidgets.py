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

import subprocess,sys,os.path

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
		self.button_lookUp = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Look-Up..."))
		self.button_reset  = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Reset"))
		
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
		
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addWidget(self.button_lookUp)
		layout_buttons.addWidget(self.button_reset)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_coordinates)
		layout.addLayout(layout_buttons)
		layout.setAlignment(QtCore.Qt.AlignTop)
		
		widget = QtGui.QWidget()
		widget.setLayout(layout)
		self.setWidget(widget)
		
		self.connect(
			self.button_lookUp,
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
		if latitude == self.spinbox_latitude.minimum():
			latitude = None
		if longitude == self.spinbox_longitude.minimum():
			longitude = None
		return (latitude,longitude,elevation)
	

	def lookUpCoordinates(self):
		(latitude,longitude,elevation) = self.location()
		dlg = FotoPreProcessorTools.FPPGeoTaggingDialog()
		
		if latitude != None and longitude != None:
			dlg.setLocation(latitude,longitude,elevation)
		else:
			dlg.setLocation(52.374444,9.738611,0.0)
		
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
	
	def __init__(self,timezoneNames=tuple()):
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
		
		self.button_reset = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Reset"))
		
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
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addStretch(1)
		layout_buttons.addWidget(self.button_reset)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_timezones)
		layout.addLayout(layout_buttons)
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
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBKeywords = FotoPreProcessorTools.FPPStringDB()
		self.DBKeywords.loadFile(os.path.join(sys.path[0],u"FotoPreProcessor.keywords"))
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
		
		self.button_reset = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Reset"))
		
		layout = QtGui.QVBoxLayout()
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addWidget(self.button_add)
		layout_buttons.addWidget(self.button_remove)
		layout_buttons.addWidget(self.button_reset)
		layout.addWidget(self.list_keywords)
		layout.addLayout(layout_buttons)
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
	
	
	def triggerReset(self):
		self.emit(QtCore.SIGNAL("dockResetTriggered()"))
	
	
	def updateRemoveButtonState(self):
		self.button_remove.setEnabled(len(self.list_keywords.selectedItems()) > 0)
	
	
	def setResetEnabled(self,state=True):
		self.button_reset.setEnabled(bool(state))
	
	
	def closeEvent(self,event=None):
		"""Save keywords DB to the file "FotoPreProcessor.keywords"."""
		self.DBKeywords.saveFile()
		event.accept()



class FPPCopyrightDock(QtGui.QDockWidget):
	""""Class for the Copyright Dock Widget."""
	
	def __init__(self,timezoneNames=tuple()):
		"""Constructor; initialise dock widget and setup its GUI elements.

Features: Floatable | Movable | Closable
Attributes: Delete on close"""
		QtGui.QDockWidget.__init__(self,QtCore.QCoreApplication.translate(u"DockWidgets",u"Copyright Notice"))
		
		self.setFeatures(QtGui.QDockWidget.AllDockWidgetFeatures)
		self.setAttribute(QtCore.Qt.WA_DeleteOnClose,False)
		
		self.DBCopyright = FotoPreProcessorTools.FPPStringDB()
		self.DBCopyright.loadFile(os.path.join(sys.path[0],u"FotoPreProcessor.copyright"))
		
		self.edit_copyright = QtGui.QLineEdit()
		self.completer = QtGui.QCompleter(self.DBCopyright.strings(),self.edit_copyright)
		self.edit_copyright.setCompleter(self.completer)
		
		self.button_reset = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"DockWidgets",u"Reset"))
		
		layout_copyright = QtGui.QFormLayout()
		layout_copyright.addRow(
			QtCore.QCoreApplication.translate(u"DockWidgets",u"Photographer:"),
			self.edit_copyright
		)
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addStretch(1)
		layout_buttons.addWidget(self.button_reset)
		
		layout = QtGui.QVBoxLayout()
		layout.addLayout(layout_copyright)
		layout.addLayout(layout_buttons)
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
			self.edit_copyright.setText(notice)
			self.DBCopyright.add(notice)
			self.completer.model().setStringList(self.DBCopyright.strings())
		except:
			pass
	
	
	def copyright(self):
		return unicode(self.edit_copyright.text())
	
	
	def triggerReset(self):
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
		self.DBCopyright.saveFile()
		event.accept()




class FPPApplyChangesDialog(QtGui.QDialog):
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtGui.QDialog.__init__(self,parent)
		self.progressbar = QtGui.QProgressBar()
		self.konsole = QtGui.QPlainTextEdit()
		self.konsole.setReadOnly(True)
		
		self.button_execute = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"Execute"))
		self.button_cancel = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"Cancel"))
		self.button_close = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"Dialog",u"Close"))
		
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addStretch(1)
		layout_buttons.addWidget(self.button_execute)
		layout_buttons.addWidget(self.button_cancel)
		layout_buttons.addWidget(self.button_close)
		
		layout = QtGui.QVBoxLayout()
		layout.addWidget(self.progressbar)
		layout.addWidget(self.konsole)
		layout.addLayout(layout_buttons)
		
		self.setLayout(layout)
	
		self.connect(
			self.button_execute,
			QtCore.SIGNAL('clicked()'),
			self.execute
		)
		self.connect(
			self.button_cancel,
			QtCore.SIGNAL('clicked()'),
			self.reject
		)
		self.connect(
			self.button_close,
			QtCore.SIGNAL('clicked()'),
			self.accept
		)
		self.lst_commands = list()
		self.button_close.setEnabled(False)
		self.button_close.hide()
		self.progressbar.hide()
	
	
	def addCommand(self,command=tuple()):
		try:
			self.lst_commands.append(tuple(command))
			self.konsole.appendPlainText(u" ".join(tuple(command))+u"\n")
		except:
			pass
	
	
	def execute(self):
		self.button_cancel.setEnabled(False)
		self.button_cancel.hide()
		self.button_execute.setEnabled(False)
		self.progressbar.reset()
		self.progressbar.setRange(0,len(self.lst_commands))
		self.progressbar.show()
		self.konsole.clear()
		
		for command in self.lst_commands:
			self.progressbar.setValue(self.progressbar.value()+1)
			self.konsole.appendPlainText(subprocess.check_output(command))
		
		self.button_execute.hide()
		self.progressbar.hide()
		self.button_close.setEnabled(True)
		self.button_close.show()



#class FPPSettingsDialog(QtGui.QDialog):
	
	#def __init__(self,parent=None):
		#"""Constructor; initialise fields, load bookmarks and construct GUI."""
		#QtGui.QDialog.__init__(self,parent)
		##
		## to set up:
		##  - path to exiftool
		##  - keyword database
		##  - copyright database
		##  - location database
		##  - default parameters for certain cameras?
		##  - file naming scheme?
		#pass


