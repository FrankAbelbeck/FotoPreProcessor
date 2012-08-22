#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FotoPreProcessor: manage (EXIF) metadata of images in a directory
Copyright (C) 2012 Frank Abelbeck <frank.abelbeck@googlemail.com>

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

# FPP displays image files in a given directory and allows extended selection;
# meant for batch manipulation of orientation, location, timestamp, keywords,
# copyright notice and filename.
#
# 2012-08-10: initial release as "works for me" version

import sys,os,subprocess,time,pytz,datetime,codecs,xml.dom.minidom,base64,re

from PyQt4 import QtGui, QtCore

import FotoPreProcessorWidgets,FotoPreProcessorItem


class FPPMainWindow(QtGui.QMainWindow):	
	"""Main window class. Core element of the HQ."""
	
	def __init__(self):
		"""Constructor: initialise fields, load timezone DB and construct GUI ."""
		QtGui.QMainWindow.__init__(self)
		self.dct_iconsize = {
			u" 32x32":   QtCore.QSize( 32, 32),
			u" 64x64":   QtCore.QSize( 64, 64),
			u"128x128": QtCore.QSize(128,128),
			u"160x160": QtCore.QSize(160,160)
		}
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
		#
		# read settings
		#
		if settings.value(u"ConfigureAtStartup",True).toBool() == True:
			# this seems to be the first time FPP is run: configure...
			dlg = FotoPreProcessorWidgets.FPPSettingsDialog()
			if dlg.exec_() == QtGui.QDialog.Accepted:
				settings.setValue(u"ConfigureAtStartup",False)
				self.bool_ready = True
			else:
				# not properly configured -> display warning message
				answer = QtGui.QMessageBox.critical(
					self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Initial Configuration Cancelled"),
					QtCore.QCoreApplication.translate(u"Dialog",u"The program was not properly configured and thus is terminated."),
					QtGui.QMessageBox.Ok
				)
				self.bool_ready = False
		else:
			self.bool_ready = True
		
		if self.bool_ready:
			# executing third-party programs is always a security nightmare...
			# but in a multi-platform application it is not feasible to check
			# all possible versions of The Gimp and Exiftool...
			#
			# therefore it is just checked that the executables are regular
			# files; let's hope the user knows what he does...
			self.ustr_path_exiftool = self.sanitiseExecutable(
				unicode(settings.value(u"ExiftoolPath",u"/usr/bin/exiftool").toString())
			)
			self.ustr_path_gimp = self.sanitiseExecutable(
				unicode(settings.value(u"TheGimpPath",u"/usr/bin/gimp").toString())
			)
			
			(self.int_stepsize,ok) = settings.value(u"StepSize",4).toInt()
			if not ok: self.int_stepsize = 4
			
			(self.int_readsize,ok) = settings.value(u"ReadSize",1024).toInt()
			if not ok: self.int_readsize = 1024
			
			(self.float_readdelay,ok) = settings.value(u"ReadDelay",0.0001).toFloat()
			if not ok: self.float_readdelay = 0.0001
			
			#
			# write settings back; this way we get a basic config file at first start
			#
			settings.setValue(u"ExiftoolPath",self.ustr_path_exiftool)
			settings.setValue(u"TheGimpPath",self.ustr_path_gimp)
			settings.setValue(u"StepSize",self.int_stepsize)
			settings.setValue(u"ReadSize",self.int_readsize)
			
			self.ustr_path = unicode()
			
			self.setupGUI()
			self.updateImageList()
	
	
	def sanitiseExecutable(self,path=unicode()):
		returnPath = unicode()
		path = unicode(path)
		try:
			if os.path.isfile(path) and os.access(path,os.X_OK):
				returnPath = path
		except:
			pass
		return returnPath
	
	
	def isReady(self):
		return self.bool_ready
	
	
	def setupGUI(self):
		"""Setup GUI: define widget, layouts and wiring."""
		
		#---------------------------------------------------------------
		
		self.action_openDir = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Open directory..."),self)
		self.action_apply = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Apply changes..."),self)
		action_quit = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Quit"),self)
		self.action_rotateLeft = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Rotate left"),self)
		self.action_rotateRight = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Rotate right"),self)
		self.action_locationLookUp = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Look up coordinates..."),self)
		self.action_openGimp = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Open with the GIMP..."),self)
		self.action_resetOrientation = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset orientation"),self)
		self.action_resetLocation = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset coordinates"),self)
		self.action_resetKeywords = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset keywords"),self)
		self.action_resetTimezones = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset timezones"),self)
		self.action_resetCopyright = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset copyright notice"),self)
		self.action_resetAll = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Reset everything"),self)
		
		action_config = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Configure FPP..."),self)
		
		self.action_sortByName = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Sort by filename"),self)
		self.action_sortByTime = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Sort by timestamp"),self)
		self.action_sortByCamera = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"Sort by camera"),self)
		self.action_sortByName.setCheckable(True)
		self.action_sortByTime.setCheckable(True)
		self.action_sortByCamera.setCheckable(True)
		self.action_sortByName.setChecked(True)
		
		action_about = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"About FotoPreProcessor..."),self)
		action_aboutQt = QtGui.QAction(QtCore.QCoreApplication.translate(u"Menu",u"About Qt..."),self)
		
		self.action_rotateLeft.setShortcut(QtGui.QKeySequence(u"l"))
		self.action_rotateRight.setShortcut(QtGui.QKeySequence(u"r"))
		self.action_locationLookUp.setShortcut(QtGui.QKeySequence(u"g"))
		self.action_openGimp.setShortcut(QtGui.QKeySequence(u"c"))
		self.action_resetOrientation.setShortcut(QtGui.QKeySequence(u"n"))
		action_quit.setShortcut(QtGui.QKeySequence(u"Ctrl+Q"))
		self.action_openDir.setShortcut(QtGui.QKeySequence(u"Ctrl+O"))
		self.action_apply.setShortcut(QtGui.QKeySequence(u"Ctrl+S"))
		
		self.action_openGimp.setEnabled(len(self.ustr_path_gimp) > 0)
		self.action_openDir.setEnabled(len(self.ustr_path_exiftool) > 0)
		
		#---------------------------------------------------------------
		
		self.list_images = QtGui.QListWidget(self)
		self.list_images.setItemDelegate(FotoPreProcessorItem.FPPGalleryItemDelegate(QtGui.QIcon(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"icons",u"changed.png"))))
		self.list_images.setIconSize(QtCore.QSize(128,128))
		self.list_images.setViewMode(QtGui.QListView.IconMode)
		self.list_images.setResizeMode(QtGui.QListView.Adjust)
		self.list_images.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.list_images.setDragEnabled(False)
		self.list_images.setUniformItemSizes(True)
		
		#---------------------------------------------------------------
		
		self.dock_geotagging = FotoPreProcessorWidgets.FPPGeoTaggingDock()
		self.dock_timezones  = FotoPreProcessorWidgets.FPPTimezonesDock()
		self.dock_keywords   = FotoPreProcessorWidgets.FPPKeywordsDock()
		self.dock_copyright  = FotoPreProcessorWidgets.FPPCopyrightDock()
		
		self.dock_geotagging.setEnabled(False)
		self.dock_timezones.setEnabled(False)
		self.dock_keywords.setEnabled(False)
		self.dock_copyright.setEnabled(False)
		
		#---------------------------------------------------------------
		# construct menubar
		#
		# &File  &Edit       &View    &Bookmarks   Sess&ions  &Tools  &Settings      &Help
		# &Datei &Bearbeiten &Ansicht &Lesezeichen &Sitzungen E&xtras &Einstellungen &Hilfe
		#---------------------------------------------------------------
		
		menu_file = self.menuBar().addMenu(QtCore.QCoreApplication.translate(u"Menu",u"&File"))
		menu_file.addAction(self.action_openDir)
		menu_file.addSeparator()
		menu_file.addAction(self.action_apply)
		menu_file.addSeparator()
		menu_file.addAction(action_quit)
		
		self.menu_edit = self.menuBar().addMenu(QtCore.QCoreApplication.translate(u"Menu",u"&Edit"))
		self.menu_edit.addAction(self.action_rotateLeft)
		self.menu_edit.addAction(self.action_rotateRight)
		self.menu_edit.addSeparator()
		self.menu_edit.addAction(self.action_locationLookUp)
		self.menu_edit.addSeparator()
		menu_reset = self.menu_edit.addMenu(QtCore.QCoreApplication.translate(u"Menu",u"Reset values"))
		menu_reset.addAction(self.action_resetOrientation)
		menu_reset.addAction(self.action_resetLocation)
		menu_reset.addAction(self.action_resetTimezones)
		menu_reset.addAction(self.action_resetKeywords)
		menu_reset.addAction(self.action_resetCopyright)
		menu_reset.addSeparator()
		menu_reset.addAction(self.action_resetAll)
		self.menu_edit.addSeparator()
		self.menu_edit.addAction(self.action_openGimp)
		
		#---------------------------------------------------------------
		
		menu_settings = self.menuBar().addMenu(QtCore.QCoreApplication.translate(u"Menu",u"&Settings"))
		menu_docks = menu_settings.addMenu(QtCore.QCoreApplication.translate(u"Menu",u"Dockable windows"))
		menu_iconSize = menu_settings.addMenu(QtCore.QCoreApplication.translate(u"Menu",u"Icon size"))
		menu_sorting = menu_settings.addMenu(QtCore.QCoreApplication.translate(u"Menu",u"Sort criterion"))
		menu_settings.addSeparator()
		menu_settings.addAction(action_config)
		
		menu_docks.addAction(self.dock_geotagging.toggleViewAction())
		menu_docks.addAction(self.dock_timezones.toggleViewAction())
		menu_docks.addAction(self.dock_keywords.toggleViewAction())
		menu_docks.addAction(self.dock_copyright.toggleViewAction())
		
		actiongroup_iconSize = QtGui.QActionGroup(self)
		sizes = self.dct_iconsize.keys()
		sizes.sort()
		for size in sizes:
			action_iconSize = QtGui.QAction(size,self)
			action_iconSize.setCheckable(True)
			action_iconSize.setChecked(size == u"128x128")
			actiongroup_iconSize.addAction(action_iconSize)
			menu_iconSize.addAction(action_iconSize)
		
		actiongroup_sorting = QtGui.QActionGroup(self)
		actiongroup_sorting.addAction(self.action_sortByName)
		actiongroup_sorting.addAction(self.action_sortByTime)
		actiongroup_sorting.addAction(self.action_sortByCamera)
		menu_sorting.addAction(self.action_sortByName)
		menu_sorting.addAction(self.action_sortByTime)
		menu_sorting.addAction(self.action_sortByCamera)
		
		menu_help = self.menuBar().addMenu(QtCore.QCoreApplication.translate(u"Menu",u"&Help"))
		menu_help.addAction(action_about)
		menu_help.addAction(action_aboutQt)
		
		#---------------------------------------------------------------
		# wiring: connect widgets to functions (signals to slots)
		#---------------------------------------------------------------
		
		self.connect(
			self.list_images,
			QtCore.SIGNAL('itemSelectionChanged()'),
			self.listImagesSelectionChanged
		)
		self.connect(
			self.list_images,
			QtCore.SIGNAL('itemChanged(QListWidgetItem*)'),
			self.listImagesItemChanged
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			action_quit,
			QtCore.SIGNAL('triggered()'),
			QtGui.QApplication.instance().quit
		)
		self.connect(
			self.action_apply,
			QtCore.SIGNAL('triggered()'),
			self.applyChanges
		)
		self.connect(
			self.action_openDir,
			QtCore.SIGNAL('triggered()'),
			self.selectDirectory
		)
		self.connect(
			menu_iconSize,
			QtCore.SIGNAL('triggered(QAction*)'),
			self.adjustIconSize
		)
		self.connect(
			menu_sorting,
			QtCore.SIGNAL('triggered(QAction*)'),
			self.setSortCriterion
		)
		
		self.connect(
			self.action_rotateLeft,
			QtCore.SIGNAL('triggered()'),
			self.rotateImageLeft
		)
		self.connect(
			self.action_rotateRight,
			QtCore.SIGNAL('triggered()'),
			self.rotateImageRight
		)
		
		self.connect(
			self.action_resetAll,
			QtCore.SIGNAL('triggered()'),
			self.resetAll
		)
		self.connect(
			self.action_resetOrientation,
			QtCore.SIGNAL('triggered()'),
			self.resetOrientation
		)
		self.connect(
			self.action_resetLocation,
			QtCore.SIGNAL('triggered()'),
			self.resetLocation
		)
		self.connect(
			self.action_resetTimezones,
			QtCore.SIGNAL('triggered()'),
			self.resetTimezones
		)
		self.connect(
			self.action_resetKeywords,
			QtCore.SIGNAL('triggered()'),
			self.resetKeywords
		)
		self.connect(
			self.action_resetCopyright,
			QtCore.SIGNAL('triggered()'),
			self.resetCopyright
		)
		
		self.connect(
			self.action_locationLookUp,
			QtCore.SIGNAL('triggered()'),
			self.dock_geotagging.lookUpCoordinates
		)
		self.connect(
			self.action_openGimp,
			QtCore.SIGNAL('triggered()'),
			self.openWithTheGimp
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			self.action_resetOrientation,
			QtCore.SIGNAL('changed()'),
			self.updateResetAllAction
		)
		self.connect(
			self.action_resetLocation,
			QtCore.SIGNAL('changed()'),
			self.updateResetAllAction
		)
		self.connect(
			self.action_resetTimezones,
			QtCore.SIGNAL('changed()'),
			self.updateResetAllAction
		)
		self.connect(
			self.action_resetKeywords,
			QtCore.SIGNAL('changed()'),
			self.updateResetAllAction
		)
		self.connect(
			self.action_resetCopyright,
			QtCore.SIGNAL('changed()'),
			self.updateResetAllAction
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			self.dock_geotagging,
			QtCore.SIGNAL('dockDataUpdated(PyQt_PyObject)'),
			self.updateLocation
		)
		self.connect(
			self.dock_geotagging,
			QtCore.SIGNAL('dockResetTriggered()'),
			self.resetLocation
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			self.dock_timezones,
			QtCore.SIGNAL('dockDataUpdated(PyQt_PyObject)'),
			self.updateTimezones
		)
		self.connect(
			self.dock_timezones,
			QtCore.SIGNAL('dockResetTriggered()'),
			self.resetTimezones
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			self.dock_keywords,
			QtCore.SIGNAL('dockKeywordAdded(PyQt_PyObject)'),
			self.addKeyword
		)
		self.connect(
			self.dock_keywords,
			QtCore.SIGNAL('dockKeywordRemoved(PyQt_PyObject)'),
			self.removeKeyword
		)
		self.connect(
			self.dock_keywords,
			QtCore.SIGNAL('dockResetTriggered()'),
			self.resetKeywords
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			self.dock_copyright,
			QtCore.SIGNAL('dockDataUpdated(PyQt_PyObject)'),
			self.updateCopyright
		)
		self.connect(
			self.dock_copyright,
			QtCore.SIGNAL('dockResetTriggered()'),
			self.resetCopyright
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			action_config,
			QtCore.SIGNAL('triggered()'),
			self.configureProgram
		)
		
		#---------------------------------------------------------------
		
		self.connect(
			action_about,
			QtCore.SIGNAL('triggered()'),
			self.aboutDialog
		)
		self.connect(
			action_aboutQt,
			QtCore.SIGNAL('triggered()'),
			self.aboutQtDialog
		)
		
		#---------------------------------------------------------------
		# construct main window
		#---------------------------------------------------------------
		self.setCentralWidget(self.list_images)
		#self.resize(640,400)
		
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_geotagging)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_timezones)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_keywords)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_copyright)
		
		self.setWindowTitle(QtCore.QCoreApplication.translate(u"MainWindow",u"FotoPreProcessor"))
		self.setWindowIcon(QtGui.QIcon(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"icons",u"FPP.png")))
		
		self.setStyleSheet(u":disabled { color: gray; }")
		self.show()
	
	
	def closeEvent(self,event):
		"""Window received close event: toggles visibility (ie close to tray)."""
		edited = False
		for i in xrange(0,self.list_images.count()):
			if self.list_images.item(i).edited():
				edited = True
				break
		if edited:
			answer = QtGui.QMessageBox.question(
				self,
				QtCore.QCoreApplication.translate(u"Dialog",u"Exit Application"),
				QtCore.QCoreApplication.translate(u"Dialog",u"Some changes were made.\nDo you want to apply them before exiting?"),
				QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
			)
			if answer == QtGui.QMessageBox.Yes:
				self.applyChanges()
		self.dock_copyright.close() # i.e.: save copyright DB
		self.dock_keywords.close()  # i.e.: save keywords DB
		event.accept()
	
	
	def selectDirectory(self):
		path = QtGui.QFileDialog.getExistingDirectory(self,
			QtCore.QCoreApplication.translate(u"Dialog",u"Select Directory"),
			self.ustr_path,
			QtGui.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.setDirectory(path)
	
	
	def setDirectory(self,path=unicode()):
		path = unicode(path)
		if os.path.isdir(path) and len(self.ustr_path_exiftool) > 0:
			self.ustr_path = path
			self.setWindowTitle(
				QtCore.QCoreApplication.translate(
					u"MainWindow",
					u"FotoPreProcessor"
				) + u": " + path
			)
		else:
			# either path does not exist or Exiftool is not defined
			# delete list, reset path and title...
			self.ustr_path = unicode()
			self.setWindowTitle(
				QtCore.QCoreApplication.translate(
					u"MainWindow",
					u"FotoPreProcessor"
				)
			)
		self.updateImageList()
	
	
	def adjustIconSize(self,action):
		self.list_images.setIconSize(self.dct_iconsize[unicode(action.text())])
		for i in xrange(0,self.list_images.count()):
			self.list_images.item(i).updateIcon()
	
	
	def setSortCriterion(self,action):
		if action == self.action_sortByTime:
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByTime
		elif action == self.action_sortByCamera:
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByCamera
		else:
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByName
		
		for i in xrange(0,self.list_images.count()):
			self.list_images.item(i).setSortCriterion(sortCriterion)
		self.list_images.sortItems()
	
	
	def getFirstTextChild(self,node=None):
		value = unicode()
		for child in node.childNodes:
			if child.nodeType == node.TEXT_NODE and len(child.nodeValue.strip()) > 0:
				value = unicode(node.childNodes[0].nodeValue.strip())
				break
		return value
	
	
	def updateImageList(self):
		self.list_images.clear()
		
		progress = QtGui.QProgressDialog(self)
		progress.setWindowModality(QtCore.Qt.WindowModal)
		progress.setRange(0,100)
		progress.setValue(0)
		
		if self.action_sortByName.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByName
		elif self.action_sortByTime.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByTime
		elif self.action_sortByCamera.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByCamera
		
		try:    filelist = [os.path.join(self.ustr_path,i.decode(sys.getfilesystemencoding())) for i in os.listdir(self.ustr_path)]
		except: filelist = list()
		
		l_filelist = len(filelist)
		progress.setRange(0,l_filelist)
		
		if l_filelist > 0 and len(self.ustr_path_exiftool) > 0:
			proc_exiftool = subprocess.Popen([
				self.ustr_path_exiftool,
				u"-stay_open",u"True",
				u"-@",u"-",
				u"-common_args",
				u"-X",
				u"-b",
				u"-m",
				u"-if",
				u"$MIMEType =~ /^image/",
				u"-d",
				u"%Y %m %d %H %M %S",
				u"-Orientation",
				u"-DateTimeOriginal",
				u"-Keywords",
				u"-FocalLength#",
				u"-ScaleFactor35efl",
				u"-Aperture",
				u"-ShutterSpeed",
				u"-ISO",
				u"-Model",
				u"-LensType",
				u"-ThumbnailImageValidArea",
				u"-Copyright",
				u"-GPS:GPSLatitude#",
				u"-GPS:GPSLatitudeRef#",
				u"-GPS:GPSLongitude#",
				u"-GPS:GPSLongitudeRef#",
				u"-GPS:GPSAltitude#",
				u"-GPS:GPSAltitudeRef#",
				u"-ThumbnailImage"
			],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			
			for i in xrange(0,l_filelist,self.int_stepsize):
				#
				# read self.int_stepsize images at once and process output
				#
				command = u"\n".join(filelist[i:i+self.int_stepsize]) + u"\n-execute\n"
				proc_exiftool.stdin.write(command.encode("UTF-8"))
				proc_exiftool.stdin.flush()
				
				# os.read is needed for stdout/stderr "file" objects...
				# in addition, exiftool output ends with {ready}, so we have to catch it
				f_stdout = proc_exiftool.stdout.fileno()
				str_output = str()
				while not str_output[-64:].strip().endswith('{ready}'):
					# read until {ready} occurs
					str_output += os.read(f_stdout,self.int_readsize).decode(sys.stdout.encoding)
				QtCore.QCoreApplication.processEvents()
				str_output = str_output.strip()[:-7]
				
				try:    descriptionElements = xml.dom.minidom.parseString(str_output.encode("utf-8")).getElementsByTagName("rdf:Description")
				except: descriptionElements = tuple()
				
				k_max = len(descriptionElements)
				for k,description in enumerate(descriptionElements):
					#
					# process every identified image
					#
					filepath = unicode(description.getAttribute("rdf:about"))
					
					if len(filepath) == 0: continue
					if progress.wasCanceled(): break
					
					filename = os.path.basename(filepath)
					
					progress.setValue(progress.value()+1)
					progress.setLabelText(u"{0} {1}...".format(
						QtCore.QCoreApplication.translate(u"Dialog",u"Processing Image"),
						filename
					))
					
					timestamp    = unicode()
					focalLength  = unicode()
					cropFactor   = unicode()
					aperture     = unicode()
					shutterSpeed = unicode()
					isoValue     = unicode()
					cameraModel  = unicode()
					lensType     = unicode()
					thumbArea    = unicode()
					latitude     = unicode()
					latitudeRef  = unicode()
					longitude    = unicode()
					longitudeRef = unicode()
					elevation    = unicode()
					elevationRef = unicode()
					thumbData    = unicode()
					
					item = FotoPreProcessorItem.FPPGalleryItem(self.list_images)
					item.setFilename(filename)
					
					for node in description.childNodes:
						#
						# process nodes of the XML structure
						#
						if node.nodeType != node.ELEMENT_NODE: continue
						if node.localName == "Orientation":
							item.setOrientation(self.getFirstTextChild(node))
						elif node.localName == "DateTimeOriginal":
							timestamp = self.getFirstTextChild(node)
						elif node.localName == "Keywords":
							keywords = list()
							rdfBag = node.getElementsByTagName("rdf:Bag")
							if len(rdfBag) > 0:
								# more than one keyword: stored as RDF bag,
								# i.e. there is at least one rdf:Bag tag...
								for bagItem in rdfBag[0].getElementsByTagName("rdf:li"):
									keywords.append(self.getFirstTextChild(bagItem))
							else:
								# single keyword is stored as simple cdata
								keywords.append(self.getFirstTextChild(node))
							item.setKeywords(keywords)
						elif node.localName == "FocalLength":
							focalLength = self.getFirstTextChild(node)
						elif node.localName == "ScaleFactor35efl":
							cropFactor = self.getFirstTextChild(node)
						elif node.localName == "Aperture":
							aperture = self.getFirstTextChild(node)
						elif node.localName == "ShutterSpeed":
							shutterSpeed = self.getFirstTextChild(node)
						elif node.localName == "ISO":
							isoValue = self.getFirstTextChild(node)
						elif node.localName == "Model":
							cameraModel = self.getFirstTextChild(node)
						elif node.localName == "LensType":
							lensType = self.getFirstTextChild(node)
						elif node.localName == "ThumbnailImageValidArea":
							thumbArea = self.getFirstTextChild(node)
						elif node.localName == "Copyright":
							cr = self.getFirstTextChild(node)
							try:    cr = re.match(r'^(©|\(C\)|\(c\)|Copyright \(C\)|Copyright \(c\)|Copyright ©) [0-9-]* (.*)',cr).groups()[1]
							except: pass
							item.setCopyright(cr)
						elif node.localName == "GPSLatitude":
							latitude = self.getFirstTextChild(node)
						elif node.localName == "GPSLatitudeRef":
							latitudeRef = self.getFirstTextChild(node)
						elif node.localName == "GPSLongitude":
							longitude = self.getFirstTextChild(node)
						elif node.localName == "GPSLongitudeRef":
							longitudeRef = self.getFirstTextChild(node)
						elif node.localName == "GPSAltitude":
							elevation = self.getFirstTextChild(node)
						elif node.localName == "GPSAltitudeRef":
							elevationRef = self.getFirstTextChild(node)
						elif node.localName == "ThumbnailImage":
							thumbData = base64.b64decode(self.getFirstTextChild(node))
					
					thumbImage = QtGui.QPixmap()
					if not thumbImage.loadFromData(thumbData):
						try:
							thumbImage = QtGui.QPixmap(filepath)
							thumbImage.scaled(QtCore.QSize(160,160),QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)
						except:
							thumbImage = QtGui.QPixmap(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"icons",u"unknownPicture2.png"))
					else:
						try:
							(x1,x2,y1,y2) = tuple(thumbArea.split(u" "))
							thumbRect = QtCore.QRect()
							thumbRect.setTop(int(y1))
							thumbRect.setBottom(int(y2))
							thumbRect.setLeft(int(x1))
							thumbRect.setRight(int(x2))
							thumbImage = thumbImage.copy(thumbRect)
						except:
							pass
					item.setThumbnail(thumbImage)
					
					if len(timestamp) == 0:
						# no EXIF timestamp , so obtain timestamp from filesystem
						timestamp = time.strftime(
							u"%Y %m %d %H %M %S",
							time.localtime(os.path.getctime(filepath))
						)
					try:    item.setTimestamp(timestamp.split(u" "))
					except: pass
				
					settings = []
					if len(focalLength) != 0:
						try:
							settings.append(u"{0} mm ({1})".format(
								int(float(focalLength) * float(cropFactor)),
								QtCore.QCoreApplication.translate(u"ItemToolTip",u"on full-frame")
							))
						except:
							settings.append(u"{0} ({1})".format(
								focalLength,
								QtCore.QCoreApplication.translate(u"ItemToolTip",u"physical")
							))
					if len(aperture) != 0:
						settings.append(u"f/" + aperture)
					if len(shutterSpeed) != 0:
						settings.append(shutterSpeed + u" s")
					if len(isoValue) != 0:
						settings.append(u"ISO " + isoValue)
					if len(settings) != 0:
						item.setCameraSettings(u", ".join(settings))
					
					settings = []
					if len(cameraModel) > 0 and not cameraModel.startswith(u"Unknown"):
						settings.append(cameraModel)
					if len(lensType) > 0 and not lensType.startswith(u"Unknown"):
						settings.append(lensType)
					if len(settings) != 0:
						item.setCameraHardware(u", ".join(settings))
					
					try:
						latitude = float(latitude)
						longitude = float(longitude)
						if latitudeRef == u"S": latitude = -latitude
						if longitudeRef == u"W": longitude = -longitude
						try:    elevation = float(elevation)
						except: elevation = 0.0
						if elevationRef == u"1": elevation = -elevation
						item.setLocation(latitude,longitude,elevation)
					except:
						pass
					
					item.setSortCriterion(sortCriterion)
					item.saveState()
					#
					# end of image package processing
					#
				if progress.wasCanceled(): break
				#
				# end of file processing
				#
			
			# terminate exiftool
			proc_exiftool.communicate("-stay_open\nFalse\n")
			
		if progress.wasCanceled():
			self.list_images.clear()
		else:
			self.list_images.sortItems()
		
		progress.close()
		
		self.action_apply.setEnabled(False)
		
		self.action_locationLookUp.setEnabled(False)
		self.action_openGimp.setEnabled(False)
		
		self.action_resetAll.setEnabled(False)
		self.action_resetOrientation.setEnabled(False)
		self.action_resetLocation.setEnabled(False)
		self.action_resetTimezones.setEnabled(False)
		self.action_resetKeywords.setEnabled(False)
		self.action_resetCopyright.setEnabled(False)
		
		self.action_rotateLeft.setEnabled(False)
		self.action_rotateRight.setEnabled(False)
	
	
	def listImagesItemChanged(self,item):
		edited = False
		for i in xrange(0,self.list_images.count()):
			if self.list_images.item(i).edited():
				edited = True
				break
		self.action_apply.setEnabled(edited and len(self.ustr_path_exiftool) > 0)
	
	
	def listImagesSelectionChanged(self):
		items = self.list_images.selectedItems()
		if len(items) > 0:
			# collect data of selected items
			location  = set()
			timezones = set()
			keywords  = set()
			copyright = set()
			orientationEdited = False
			locationEdited = False
			timezonesEdited = False
			keywordsEdited = False
			copyrightEdited = False
			for item in items:
				location.add(item.location())
				timezones.add(item.timezones())
				keywords.add(item.keywords())
				copyright.add(item.copyright())
				orientationEdited = orientationEdited or item.orientationEdited()
				locationEdited = locationEdited or item.locationEdited()
				timezonesEdited = timezonesEdited or item.timezonesEdited()
				keywordsEdited = keywordsEdited or item.keywordsEdited()
				copyrightEdited = copyrightEdited or item.copyrightEdited()
			l_timezones = len(timezones)
			l_location  = len(location)
			l_keywords  = len(keywords)
			l_copyright = len(copyright)
			
			# import location data or resolve location conflicts
			self.dock_geotagging.setEnabled(True)
			self.action_locationLookUp.setEnabled(True)
			latitude,longitude,elevation = None,None,None
			if l_location == 1:
				try:    (latitude,longitude,elevation) = location.pop()
				except: pass
			elif l_location > 1:
				answer = QtGui.QMessageBox.question(
					self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Location Collision"),
					QtCore.QCoreApplication.translate(u"Dialog",u"The selected images are tagged with different locations.\nDo you want to reset them?\nIf you answer \"No\", GeoTagging will be disabled."),
					QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
				)
				if answer == QtGui.QMessageBox.Yes:
					locationEdited = False
					for item in items:
						item.setLocation(None,None,None)
						locationEdited = locationEdited or item.locationEdited()
				else:
					self.dock_geotagging.setEnabled(False)
					self.action_locationLookUp.setEnabled(False)
			
			self.dock_geotagging.setLocation(latitude,longitude,elevation)
			self.dock_timezones.setLocation(latitude,longitude)
			self.dock_geotagging.setResetEnabled(locationEdited)
			
			# import timezone corrections or resolve conflicts
			self.dock_timezones.setEnabled(True)
			fromTz,toTz = u"UTC",u"UTC"
			if l_timezones == 1:
				try:    (fromTz,toTz) = timezones.pop()
				except: pass
			elif l_timezones > 1:
				lst_timezones = list()
				timezones.add((u"UTC",u"UTC"))
				for tz in timezones:
					lst_timezones.append(u"{0} → {1}".format(*tz))
				lst_timezones.sort()
				lst_timezones.insert(0,u"Disable timezone settings.")
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Timezones Collision"),
					QtCore.QCoreApplication.translate(u"Dialog",u"The selected images feature different timezone correction information.\nWhich one should be used?\nIf you cancel this dialog, timezone settings will be disabled."),
					lst_timezones,0,False
				)
				if ok and answer != lst_timezones[0]:
					(fromTz,toTz) = tuple(unicode(answer).split(u" → ",1))
					timezonesEdited = False
					for item in items:
						item.setTimezones(fromTz,toTz)
						timezonesEdited = timezonesEdited or item.timezonesEdited()
				else:
					self.dock_timezones.setEnabled(False)
			self.dock_timezones.setTimezones(fromTz,toTz)
			self.dock_timezones.setResetEnabled(timezonesEdited)
			
			# import keywords or resolve conflicts
			self.dock_keywords.setEnabled(True)
			self.dock_keywords.setKeywords()
			tpl_kws = tuple()
			if l_keywords ==  1:
				try:    tpl_kws = tuple(keywords.pop())
				except: pass
			elif l_keywords > 1:
				str_disable = QtCore.QCoreApplication.translate(u"Dialog",u"Disable keyword settings.")
				str_empty = QtCore.QCoreApplication.translate(u"Dialog",u"Remove all keywords from all images.")
				str_union = QtCore.QCoreApplication.translate(u"Dialog",u"Apply union of all keywords to all images.")
				str_inter = QtCore.QCoreApplication.translate(u"Dialog",u"Only edit keywords common to all images.")
				str_diff  = QtCore.QCoreApplication.translate(u"Dialog",u"Remove common keywords and merge the remaining.")
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Keyword Collision"),
					QtCore.QCoreApplication.translate(u"Dialog",u"The selected images feature different sets of keywords.\nWhat do you want to do?\nIf you cancel this dialog, keyword settings will be disabled."),
					(str_disable,str_empty,str_union,str_inter,str_diff),0,False
				)
				if ok and answer != str_disable:
					set_kws = set(keywords.pop())
					keywordsEdited = False
					if answer == str_empty:
						# clear keywords of all selected items
						tpl_kws = tuple()
						for item in items:
							item.setKeywords(tpl_kws)
							keywordsEdited = keywordsEdited or item.keywordsEdited()
					elif answer == str_union:
						# create union of all keywords and apply it to all selected items
						for kws in keywords:
							set_kws = set_kws.union(set(kws))
						tpl_kws = tuple(set_kws)
						for item in items:
							item.setKeywords(tpl_kws)
							keywordsEdited = keywordsEdited or item.keywordsEdited()
					elif answer == str_inter:
						# create intersection, but don't apply it to the selected items;
						# editing will be done on this set; addKeyword and
						# removeKeyword will apply the settings to the items
						for kws in keywords:
							set_kws = set_kws.intersection(set(kws))
						tpl_kws = tuple(set_kws)
						for item in items:
							keywordsEdited = keywordsEdited or item.keywordsEdited()
					elif answer == str_diff:
						# create symmetric difference and apply it to all selected items
						for kws in keywords:
							set_kws = set_kws.symmetric_difference(set(kws))
						tpl_kws = tuple(set_kws)
						for item in items:
							item.setKeywords(tpl_kws)
							keywordsEdited = keywordsEdited or item.keywordsEdited()
				else:
					self.dock_keywords.setEnabled(False)
			self.dock_keywords.setKeywords(tpl_kws)
			self.dock_keywords.setResetEnabled(keywordsEdited)
			
			# import copyright data or resolve conflicts
			self.dock_copyright.setEnabled(True)
			copyrightNotice = unicode()
			if l_copyright == 1:
				try:    copyrightNotice = copyright.pop()
				except: pass
			elif l_copyright > 1:
				lst_copyright = [u"None (clear copyright notice)"]
				lst_copyright.extend(list(copyright))
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate(u"Dialog",u"Copyright Collision"),
					QtCore.QCoreApplication.translate(u"Dialog",u"The selected images feature different copyright notices.\nWhich one should be used?\nIf you cancel this dialog, copyright settings will be disabled."),
					lst_copyright,0,False
				)
				if ok:
					if answer != lst_copyright[0]:
						copyrightNotice = unicode(answer)
					copyrightEdited = False
					for item in items:
						item.setCopyright(copyrightNotice)
						copyrightEdited = copyrightEdited or item.copyrightEdited()
				else:
					self.dock_copyright.setEnabled(False)
			self.dock_copyright.setCopyright(copyrightNotice)
			self.dock_copyright.setResetEnabled(copyrightEdited)
			
			self.action_openGimp.setEnabled(len(self.ustr_path_gimp) > 0)
			
			self.action_resetAll.setEnabled(orientationEdited or locationEdited or timezonesEdited or keywordsEdited)
			self.action_resetOrientation.setEnabled(orientationEdited)
			self.action_resetLocation.setEnabled(locationEdited)
			self.action_resetTimezones.setEnabled(timezonesEdited)
			self.action_resetKeywords.setEnabled(keywordsEdited)
			self.action_resetCopyright.setEnabled(copyrightEdited)
			
			self.action_rotateLeft.setEnabled(True)
			self.action_rotateRight.setEnabled(True)
		else:
			self.dock_geotagging.setEnabled(False)
			self.dock_timezones.setEnabled(False)
			self.dock_keywords.setEnabled(False)
			self.dock_copyright.setEnabled(False)
			
			self.action_locationLookUp.setEnabled(False)
			self.action_openGimp.setEnabled(False)
			
			self.action_resetAll.setEnabled(False)
			self.action_resetOrientation.setEnabled(False)
			self.action_resetLocation.setEnabled(False)
			self.action_resetTimezones.setEnabled(False)
			self.action_resetKeywords.setEnabled(False)
			self.action_resetCopyright.setEnabled(False)
			
			self.action_rotateLeft.setEnabled(False)
			self.action_rotateRight.setEnabled(False)
	
	#-----------------------------------------------------------------------
	# orientation: methods
	#-----------------------------------------------------------------------
	
	def rotateImageLeft(self):
		for item in self.list_images.selectedItems(): item.rotateLeft()
		self.action_resetOrientation.setEnabled(True)
	
	
	def rotateImageRight(self):
		for item in self.list_images.selectedItems(): item.rotateRight()
		self.action_resetOrientation.setEnabled(True)
	
	
	def resetOrientation(self):
		for item in self.list_images.selectedItems(): item.resetOrientation()
	
	#-----------------------------------------------------------------------
	# geotagging: methods
	#-----------------------------------------------------------------------
	
	def updateLocation(self,location=tuple()):
		try:
			latitude  = float(location[0])
			longitude = float(location[1])
			elevation = float(location[2])
		except:
			latitude  = None
			longitude = None
			elevation = 0.0
		edited = False
		for item in self.list_images.selectedItems():
			item.setLocation(latitude,longitude,elevation)
			edited = edited or item.edited()
		self.dock_timezones.setLocation(latitude,longitude)
		self.dock_geotagging.setResetEnabled(edited)
		self.action_resetLocation.setEnabled(edited)
	
	
	def resetLocation(self):
		for item in self.list_images.selectedItems(): item.resetLocation()
		self.listImagesSelectionChanged()
	
	#-----------------------------------------------------------------------
	# timezones: methods
	#-----------------------------------------------------------------------
	
	def updateTimezones(self,timezones=tuple()):
		try:
			fromTz = unicode(timezones[0])
			toTz   = unicode(timezones[1])
			edited = False
			for item in self.list_images.selectedItems():
				item.setTimezones(fromTz,toTz)
				edited = edited or item.edited()
			self.dock_timezones.setResetEnabled(edited)
			self.action_resetTimezones.setEnabled(edited)
		except:
			pass
	
	
	def resetTimezones(self):
		for item in self.list_images.selectedItems(): item.resetTimezones()
		self.listImagesSelectionChanged()
	
	#-----------------------------------------------------------------------
	# keywords: methods
	#-----------------------------------------------------------------------
	
	def addKeyword(self,keyword=unicode()):
		try:
			keyword = unicode(keyword)
			edited = False
			for item in self.list_images.selectedItems():
				item.addKeyword(keyword)
				edited = edited or item.edited()
			self.dock_keywords.setResetEnabled(edited)
			self.action_resetKeywords.setEnabled(edited)
		except:
			pass
	
	
	def removeKeyword(self,keyword=unicode()):
		try:
			keyword = unicode(keyword)
			edited = False
			for item in self.list_images.selectedItems():
				item.removeKeyword(keyword)
				edited = edited or item.edited()
			self.dock_keywords.setResetEnabled(edited)
			self.action_resetKeywords.setEnabled(edited)
		except:
			pass
	
	
	def resetKeywords(self):
		for item in self.list_images.selectedItems(): item.resetKeywords()
		self.listImagesSelectionChanged()
	
	#-----------------------------------------------------------------------
	# copyright: methods
	#-----------------------------------------------------------------------
	
	def updateCopyright(self,notice=unicode()):
		try:
			notice = unicode(notice)
			edited = False
			for item in self.list_images.selectedItems():
				item.setCopyright(notice)
				edited = edited or item.edited()
			self.dock_copyright.setResetEnabled(edited)
			self.action_resetCopyright.setEnabled(edited)
		except:
			pass
	
	
	def resetCopyright(self):
		for item in self.list_images.selectedItems(): item.resetCopyright()
		self.listImagesSelectionChanged()
	
	#-----------------------------------------------------------------------
	
	def applyChanges(self):
		dct_parameters = dict()
		lst_all_files = list()
		for i in xrange(0,self.list_images.count()):
			item = self.list_images.item(i)
			name = unicode(os.path.join(self.ustr_path,item.filename()))
			lst_all_files.append(name)
			
			if item.edited():
				parameters = list()
				
				if item.orientationEdited():
					parameters.append(u"-Orientation={0}".format(item.orientation()))
				
				if item.locationEdited():
					try:
						(lat,lon,ele) = item.location()
						latitude  = unicode(abs(lat))
						longitude = unicode(abs(lon))
						elevation = unicode(abs(ele))
						if lat < 0:
							latitudeRef = u"S"
						else:
							latitudeRef = u"N"
						if lon < 0:
							longitudeRef = u"W"
						else:
							longitudeRef = u"E"
						if ele < 0:
							elevationRef = u"1"
						else:
							elevationRef = u"0"
					except:
						latitude     = unicode()
						latitudeRef  = unicode()
						longitude    = unicode()
						longitudeRef = unicode()
						elevation    = unicode()
						elevationRef = unicode()
					parameters.append(u"-GPSLatitude={0}".format(latitude))
					parameters.append(u"-GPSLatitudeRef={0}".format(latitudeRef))
					parameters.append(u"-GPSLongitude={0}".format(longitude))
					parameters.append(u"-GPSLongitudeRef={0}".format(longitudeRef))
					parameters.append(u"-GPSAltitude={0}".format(elevation))
					parameters.append(u"-GPSAltitudeRef={0}".format(elevationRef))
				
				if item.timezonesEdited():
					try:
						t     = item.shiftedTimestamp().strftime("%Y:%m:%d %H:%M:%S")
						t_utc = item.utcTimestamp().strftime("%Y:%m:%d %H:%M:%S")
					except:
						t     = unicode()
						t_utc = unicode()
					parameters.append(u"-AllDates={0}".format(t))
					parameters.append(u"-GPSDateStamp={0}".format(t_utc))
					parameters.append(u"-GPSTimeStamp={0}".format(t_utc))
				
				if item.keywordsEdited():
					keywords = item.keywords()
					if len(keywords) == 0: keywords = (u"",)
					for keyword in keywords:
						parameters.append(u"-Keywords={0}".format(keyword))
				
				if item.copyrightEdited():
					parameters.append(u"-Copyright=(C) {0} {1}".format(
						item.shiftedTimestamp().strftime("%Y"),
						item.copyright()
					))
				
				dct_parameters[name] = parameters
		
		# result: dictionary mapping files to sets of parameters
		# todo: calculate intersections between these sets to reduce exiftool calls
		
		dlg = FotoPreProcessorWidgets.FPPApplyChangesDialog()
		for name,parameters in dct_parameters.iteritems():
			command = [self.ustr_path_exiftool,u"-P",u"-overwrite_original"]
			command.extend(parameters)
			command.append(name)
			dlg.addCommand(command)
		
		command = [ self.ustr_path_exiftool,
			u"-config",unicode(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"FotoPreProcessor.exiftool")),
			u"-P",
			u"-overwrite_original",
			u"-d",u"%Y%m%d-%H%M%S",
			u"-FileName<${DateTimeOriginal}%-2nc-${FPPModel}.%le"
		]
		command.extend(lst_all_files)
		dlg.addCommand(command)
		
		if dlg.exec_() == QtGui.QDialog.Accepted:
			# everything worked as expected
			# clear image list
			self.setDirectory()
	
	
	def resetAll(self):
		for item in self.list_images.selectedItems():
			item.resetAll()
		self.dock_geotagging.resetData()
		self.dock_timezones.resetData()
		self.dock_keywords.resetData()
		self.listImagesSelectionChanged()
	
	
	def updateResetAllAction(self):
		self.action_resetAll.setEnabled(
			self.action_resetOrientation.isEnabled() or \
			self.action_resetLocation.isEnabled() or \
			self.action_resetTimezones.isEnabled() or \
			self.action_resetKeywords.isEnabled()
		)
	
	#-----------------------------------------------------------------------
	
	def openWithTheGimp(self):
		try:
			command = [self.ustr_path_gimp]
			for item in self.list_images.selectedItems():
				command.append(unicode(os.path.join(self.ustr_path,item.filename())))
			subprocess.Popen(command)
		except:
			pass
	
	#-----------------------------------------------------------------------
	
	def configureProgram(self):
		dlg = FotoPreProcessorWidgets.FPPSettingsDialog()
		if dlg.exec_() == QtGui.QDialog.Accepted:
			# Settings dialog modified QSettings -> load new parameters
			# no checking is needed because the user confirmed the changes
			settings = QtCore.QSettings()
			settings.setIniCodec(QtCore.QTextCodec.codecForName(u"UTF-8"))
			
			self.ustr_path_exiftool = self.sanitiseExecutable(
				unicode(settings.value(u"ExiftoolPath",u"/usr/bin/exiftool").toString())
			)
			self.ustr_path_gimp = self.sanitiseExecutable(
				unicode(settings.value(u"TheGimpPath",u"/usr/bin/gimp").toString())
			)
			self.action_openGimp.setEnabled(len(self.ustr_path_gimp) > 0)
			self.action_openDir.setEnabled(len(self.ustr_path_exiftool) > 0)
			self.action_apply.setEnabled(self.action_apply.isEnabled() and len(self.ustr_path_exiftool) > 0)
			
			(self.int_stepsize,ok) = settings.value(u"StepSize",4).toInt()
			if not ok: self.int_stepsize = 4
			
			(self.int_readsize,ok) = settings.value(u"ReadSize",1024).toInt()
			if not ok: self.int_readsize = 1024
	
			(self.float_readdelay,ok) = settings.value(u"ReadDelay",0.0001).toFloat()
			if not ok: self.float_readdelay = 0.0001
	
	#-----------------------------------------------------------------------
	
	def aboutDialog(self):
		dlg = FotoPreProcessorWidgets.FPPAboutDialog()
		dlg.exec_()

	
	def aboutQtDialog(self):
		QtGui.QMessageBox.aboutQt(self)



def parseArguments(set_args=set()):
	bool_help = True
	bool_license = True
	bool_version = True
	
	# check if help was requested; if yes, display help and exit without error
	try:
		set_args.remove(u"-h")
	except:
			try:
				set_args.remove(u"--help")
			except:
				bool_help = False
	if bool_help:
		print app.translate(u"CLI",u"""Usage: %1 [-h][-l][-v][DIR]

PyQt4-based (EXIF) metadata management of images in a directory.

Optional arguments:
   DIR             directory that should be opened at start
   -h, --help      show this help message and exit
   -l, --license   show full license notice and exit
   -v, --version   show version information and exit

Copyright (C) 2012 Frank Abelbeck <frank.abelbeck@googlemail.com>

This program comes with ABSOLUTELY NO WARRANTY. It is free software,
and you are welcome to redistribute it under certain conditions
(see argument --license for details).
""").arg(os.path.basename(path_self))

	# check if license was requested; if yes, display license and exit without error
	try:
		set_args.remove(u"-l")
	except:
			try:
				set_args.remove(u"--license")
			except:
				bool_license = False
	if bool_license:
		print app.translate(u"CLI",u"License information:")
		with codecs.open(qargs[0],"r") as f:
			for i in xrange(0,4): f.readline() # skip first four lines
			for line in f:
				if not line.startswith(u"$Id"): # read until version id encountered
					print line.strip()
				else:
					break
	
	# check if version was requested; if yes, display version and exit without error
	try:
		set_args.remove(u"-v")
	except:
			try:
				set_args.remove(u"--version")
			except:
				bool_version = False
	if bool_version:
		int_revision = 0
		for filename in (u"FotoPreProcessor.py",u"FotoPreProcessorItem.py",u"FotoPreProcessorTools.py",u"FotoPreProcessorWidgets.py"):
			with codecs.open(os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),filename),u"r") as f:
				for line in f:
					if line.startswith("$Id"):
						rev = int(re.match(r'^\$Id:\ .*\ (\d+)\ .*',line).groups()[0])
						if rev > int_revision: int_revision = rev
		print app.translate(u"CLI",u"SVN revision: %1").arg(unicode(int_revision))
	
	return bool_help or bool_license or bool_version,set_args



if __name__ == '__main__':
	# setup Qt application and pass commandline arguments
	app = QtGui.QApplication(sys.argv)
	
	# obtain command line arguments, filtered by QApplication
	qargs = [unicode(i) for i in app.arguments()]
	path_self = qargs[0]
	
	bool_stop,set_args = parseArguments(set(qargs[1:]))
	if not bool_stop:
		# argument parsing returned False, i.e.no information was requested
		# via CLI, and therefore GUI is allowed to start:
		
		# initialise application information used by settings
		app.setApplicationName(u"FotoPreProcessor")
		app.setOrganizationName("Abelbeck");
		app.setOrganizationDomain("abelbeck.wordpress.com");
		
		# initialise translation service
		system_locale = unicode(QtCore.QLocale.system().name()[0:2])
		qtTranslator = QtCore.QTranslator()
		qtTranslator.load(
			u"qt_"+system_locale,
			unicode(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
		)
		
		fppTranslator = QtCore.QTranslator()
		fppTranslator.load(
			u"FotoPreProcessor."+system_locale,
			os.path.join(sys.path[0].decode(sys.getfilesystemencoding()),u"i18n")
		)
		app.installTranslator(qtTranslator)
		app.installTranslator(fppTranslator)
		
		# create main window and set directory from remaining arguments
		mainwindow = FPPMainWindow()
		if mainwindow.isReady():
			for argpath in set_args:
				try:
					os.path.expanduser(argpath)
					if not os.path.isabs(argpath):
						argpath = unicode(os.path.join(os.getcwd().decode(sys.getfilesystemencoding()),argpath))
					argpath = unicode(os.path.normpath(argpath))
					if os.path.isdir(argpath):
						mainwindow.setDirectory(argpath)
						break
				except:
					pass
			
			# start event loop, i.e. start application
			app.exec_()

