#!/usr/bin/env python3
# -*- coding: utf-8 -*-
LICENSE="""
FotoPreProcessor: manage (EXIF) metadata of images in a directory
Copyright (C) 2012-2015 Frank Abelbeck <frank.abelbeck@googlemail.com>

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
"""
VERSION="2015-10-25"

# FPP displays image files in a given directory and allows extended selection;
# meant for batch manipulation of orientation, location, timestamp, keywords,
# copyright notice and filename.
#
# 2012-08-10: initial release as "works for me" version
# ...
# 2012-09-03: last fixes for enhanced version
# 2015-06-29: update to Python3, location search (geolocator), transition to GitHub
# 2015-10-25: minor fixes, new feature: change management (changes -> save/load file),
#             upgrade to new signal/slot mechanism, file naming now configurable

import sys,os,subprocess,time,pytz,datetime,codecs,xml.dom.minidom,base64,re,yaml

from PyQt4 import QtGui, QtCore

import FotoPreProcessorWidgets,FotoPreProcessorItem

class FPPClickableLabel(QtGui.QLabel):
	# new signal/slot mechanism: define emitted signals instead of using SLOT macro
	# these must be defined as class vars!
	leftClicked = QtCore.pyqtSignal()
	rightClicked = QtCore.pyqtSignal()
	leftDoubleClicked = QtCore.pyqtSignal()
	rightDoubleClicked = QtCore.pyqtSignal()
	loadPrev = QtCore.pyqtSignal()
	loadNext = QtCore.pyqtSignal()
	goBack = QtCore.pyqtSignal()
	
	def __init__(self):
		super().__init__()
		self.image = None
		self.setSizePolicy(QtGui.QSizePolicy.Ignored,QtGui.QSizePolicy.Ignored)
		self.setScaledContents(False)
		self.setAlignment(QtCore.Qt.AlignCenter)
		self.setBackgroundRole(QtGui.QPalette.Dark)
		
		self.button_prev = QtGui.QPushButton(QtGui.QIcon.fromTheme("go-previous"),QtCore.QCoreApplication.translate("Preview","Previous"))
		self.button_next = QtGui.QPushButton(QtGui.QIcon.fromTheme("go-next"),QtCore.QCoreApplication.translate("Preview","Next"))
		self.button_exit = QtGui.QPushButton(QtGui.QIcon.fromTheme("window-close"),QtCore.QCoreApplication.translate("Preview","Back"))
		
		self.button_prev.clicked.connect(self.floadPrev)
		self.button_next.clicked.connect(self.floadNext)
		self.button_exit.clicked.connect(self.fgoBack)
		
		self.button_prev.setFlat(True)
		self.button_next.setFlat(True)
		self.button_exit.setFlat(True)
		
		self.button_prev.setGraphicsEffect(QtGui.QGraphicsOpacityEffect())
		self.button_prev.graphicsEffect().setOpacity(0.66)
		self.button_next.setGraphicsEffect(QtGui.QGraphicsOpacityEffect())
		self.button_next.graphicsEffect().setOpacity(0.66)
		self.button_exit.setGraphicsEffect(QtGui.QGraphicsOpacityEffect())
		self.button_exit.graphicsEffect().setOpacity(0.66)
		
		self.button_prev.setShortcut(QtGui.QKeySequence("Left"))
		self.button_next.setShortcut(QtGui.QKeySequence("Right"))
		self.button_exit.setShortcut(QtGui.QKeySequence("Escape"))
		
		layout = QtGui.QGridLayout()
		layout.addWidget(self.button_prev,2,0)
		layout.addWidget(self.button_next,2,2)
		layout.addWidget(self.button_exit,0,2)
		layout.setRowStretch(1,1)
		layout.setColumnStretch(1,1)
		self.setLayout(layout)
		
	def mousePressEvent(self,event):
		if event.button() == QtCore.Qt.LeftButton:
			self.leftClicked.emit()
		elif event.button() == QtCore.Qt.RightButton:
			self.rightClicked.emit()
	def mouseDoubleClickEvent(self,event):
		if event.button() == QtCore.Qt.LeftButton:
			self.leftDoubleClicked.emit()
		elif event.button() == QtCore.Qt.RightButton:
			self.rightDoubleClicked.emit()
	def floadPrev(self):
		self.loadPrev.emit()
	def floadNext(self):
		self.loadNext.emit()
	def fgoBack(self):
		self.goBack.emit()
	def updateItem(self,filepath,orientation,imgsize,tooltip):
		QtGui.QApplication.setOverrideCursor(QtCore.Qt.WaitCursor)
		matrix = QtGui.QTransform()
		if orientation == 2:
			matrix.scale(-1,1)
		elif orientation == 3:
			matrix.rotate(180)
		elif orientation == 4:
			matrix.scale(1,-1)
		elif orientation == 5:
			matrix.scale(-1,1)
			matrix.rotate(270)
		elif orientation == 6:
			matrix.rotate(90)
		elif orientation == 7:
			matrix.scale(1,-1)
			matrix.rotate(90)
		elif orientation == 8:
			matrix.rotate(270)
		self.image = QtGui.QImage(filepath)
		
		self.setPixmap(QtGui.QPixmap().fromImage(self.image))
		QtGui.QApplication.restoreOverrideCursor()
		self.setToolTip(tooltip)
		
	def resizeEvent(self,event):
		if self.image:
			scaledSize = self.image.size()
			scaledSize.scale(self.size(),QtCore.Qt.KeepAspectRatio);
			self.setPixmap(QtGui.QPixmap().fromImage(self.image.scaled(self.size(),QtCore.Qt.KeepAspectRatio,QtCore.Qt.SmoothTransformation)))


class FPPMainWindow(QtGui.QMainWindow):	
	"""Main window class. Core element of the HQ."""
	
	def __init__(self):
		"""Constructor: initialise fields, load timezone DB and construct GUI ."""
		super().__init__()
		self.dct_iconsize = {
			" 32x32":   QtCore.QSize( 32, 32),
			" 64x64":   QtCore.QSize( 64, 64),
			"128x128": QtCore.QSize(128,128),
			"160x160": QtCore.QSize(160,160),
			"256x256": QtCore.QSize(256,256),
			"512x512": QtCore.QSize(512,512)
		}
		self.iconsize_max = "512x512"
		
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
		#
		# read settings
		#
		configatstart = settings.value("ConfigureAtStartup",True)
		if configatstart in ("true",True):
			# this seems to be the first time FPP is run: configure...
			dlg = FotoPreProcessorWidgets.FPPSettingsDialog()
			if dlg.exec_() == QtGui.QDialog.Accepted:
				settings.setValue("ConfigureAtStartup",False)
				self.bool_ready = True
			else:
				# not properly configured -> display warning message
				answer = QtGui.QMessageBox.critical(
					self,
					QtCore.QCoreApplication.translate("Dialog","Initial Configuration Cancelled"),
					QtCore.QCoreApplication.translate("Dialog","The program was not properly configured and thus is terminated."),
					QtGui.QMessageBox.Ok
				)
				self.bool_ready = False
		else:
			self.bool_ready = True
		
		# 2015-10-25: introduced naming scheme config option;
		#             older versions don't know this, so make sure it is set
		if settings.value("NamingScheme",None) == None:
			print("Updating config from older FPP version (+NamingScheme).")
			settings.setValue("NamingScheme",FotoPreProcessorWidgets.FPPSettingsDialog.DEFAULT_NAMING_SCHEME)
			settings.setValue("NamingEnabled",True)
		
		if self.bool_ready:
			# executing third-party programs is always a security nightmare...
			# but in a multi-platform application it is not feasible to check
			# all possible versions of The Gimp and Exiftool...
			#
			# therefore it is just checked that the executables are regular
			# files; let's hope the user knows what he does...
			self.ustr_path_exiftool = self.sanitiseExecutable(
				str(settings.value("ExiftoolPath","/usr/bin/exiftool"))
			)
			self.ustr_path_gimp = self.sanitiseExecutable(
				str(settings.value("TheGimpPath","/usr/bin/gimp"))
			)
			
			try:    self.int_stepsize = int(settings.value("StepSize",4))
			except: self.int_stepsize = 4
			
			try:    self.int_readsize = int(settings.value("ReadSize",1024))
			except: self.int_readsize = 1024
			
			try:    self.float_readdelay = float(settings.value("ReadDelay",0.0001))
			except: self.float_readdelay = 0.0001
			
			# load miscellaneous settings
			self.ustr_iconsize = str(settings.value("IconSize","128x128"))
			
			try:    self.int_sorting = int(settings.value("SortCriterion",FotoPreProcessorItem.FPPGalleryItem.SortByName))
			except: self.int_sorting = FotoPreProcessorItem.FPPGalleryItem.SortByName
			
			try:
				self.size_window = settings.value("WindowSize",QtCore.QSize(640,480)).toSize()
				if not self.size_window.isValid(): raise
			except:
				self.size_window = QtCore.QSize(640,480)
			
			#
			# write settings back; this way we get a basic config file at first start
			#
			settings.setValue("ExiftoolPath",self.ustr_path_exiftool)
			settings.setValue("TheGimpPath",self.ustr_path_gimp)
			settings.setValue("StepSize",self.int_stepsize)
			settings.setValue("ReadSize",self.int_readsize)
			settings.setValue("IconSize",self.ustr_iconsize)
			settings.setValue("SortCriterion",self.int_sorting)
			settings.setValue("WindowSize",self.size_window)
			
			self.ustr_path = ""
			
			self.setupGUI()
			self.wasSaved = False
			self.updateImageList()
	
	
	def sanitiseExecutable(self,path=""):
		returnPath = ""
		path = str(path)
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
		
		self.action_openDir = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Open directory..."),self)
		self.action_apply = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Apply changes..."),self)
		self.action_save = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Save changes..."),self)
		action_quit = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Quit"),self)
		self.action_rotateLeft = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Rotate left"),self)
		self.action_rotateRight = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Rotate right"),self)
		self.action_locationLookUp = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Look up coordinates..."),self)
		self.action_openGimp = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Open with the GIMP..."),self)
		self.action_resetOrientation = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset orientation"),self)
		self.action_resetLocation = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset coordinates"),self)
		self.action_resetKeywords = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset keywords"),self)
		self.action_resetTimezones = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset timezones"),self)
		self.action_resetCopyright = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset copyright notice"),self)
		self.action_resetAll = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Reset everything"),self)
		
		action_config = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Configure FPP..."),self)
		
		self.action_sortByName = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Sort by filename"),self)
		self.action_sortByTime = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Sort by timestamp"),self)
		self.action_sortByCamera = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","Sort by camera"),self)
		self.action_sortByName.setCheckable(True)
		self.action_sortByTime.setCheckable(True)
		self.action_sortByCamera.setCheckable(True)
		self.action_sortByName.setChecked(self.int_sorting == FotoPreProcessorItem.FPPGalleryItem.SortByName)
		self.action_sortByTime.setChecked(self.int_sorting == FotoPreProcessorItem.FPPGalleryItem.SortByTime)
		self.action_sortByCamera.setChecked(self.int_sorting == FotoPreProcessorItem.FPPGalleryItem.SortByCamera)
		
		action_about = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","About FotoPreProcessor..."),self)
		action_aboutQt = QtGui.QAction(QtCore.QCoreApplication.translate("Menu","About Qt..."),self)
		
		self.action_rotateLeft.setShortcut(QtGui.QKeySequence("l"))
		self.action_rotateRight.setShortcut(QtGui.QKeySequence("r"))
		self.action_locationLookUp.setShortcut(QtGui.QKeySequence("g"))
		self.action_openGimp.setShortcut(QtGui.QKeySequence("c"))
		self.action_resetOrientation.setShortcut(QtGui.QKeySequence("n"))
		action_quit.setShortcut(QtGui.QKeySequence("Ctrl+Q"))
		self.action_openDir.setShortcut(QtGui.QKeySequence("Ctrl+O"))
		self.action_apply.setShortcut(QtGui.QKeySequence("Ctrl+S"))
		self.action_save.setShortcut(QtGui.QKeySequence("Ctrl+Shift+S"))
		
		self.action_openGimp.setEnabled(len(self.ustr_path_gimp) > 0)
		self.action_openDir.setEnabled(len(self.ustr_path_exiftool) > 0)
		
		#---------------------------------------------------------------
		
		self.list_images = QtGui.QListWidget(self)
		self.list_images.setItemDelegate(FotoPreProcessorItem.FPPGalleryItemDelegate(QtGui.QIcon(os.path.join(sys.path[0],"icons","changed.png"))))
		self.list_images.setIconSize(QtCore.QSize(128,128))
		self.list_images.setViewMode(QtGui.QListView.IconMode)
		self.list_images.setResizeMode(QtGui.QListView.Adjust)
		self.list_images.setSelectionMode(QtGui.QAbstractItemView.ExtendedSelection)
		self.list_images.setDragEnabled(False)
		self.list_images.setUniformItemSizes(True)
		
		#---------------------------------------------------------------
		
		self.scroll_image_label = FPPClickableLabel()
		
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
		
		menu_file = self.menuBar().addMenu(QtCore.QCoreApplication.translate("Menu","&File"))
		menu_file.addAction(self.action_openDir)
		menu_file.addSeparator()
		menu_file.addAction(self.action_apply)
		menu_file.addAction(self.action_save)
		menu_file.addSeparator()
		menu_file.addAction(action_quit)
		
		self.menu_edit = self.menuBar().addMenu(QtCore.QCoreApplication.translate("Menu","&Edit"))
		self.menu_edit.addAction(self.action_rotateLeft)
		self.menu_edit.addAction(self.action_rotateRight)
		self.menu_edit.addSeparator()
		self.menu_edit.addAction(self.action_locationLookUp)
		self.menu_edit.addSeparator()
		menu_reset = self.menu_edit.addMenu(QtCore.QCoreApplication.translate("Menu","Reset values"))
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
		
		menu_settings = self.menuBar().addMenu(QtCore.QCoreApplication.translate("Menu","&Settings"))
		menu_docks = menu_settings.addMenu(QtCore.QCoreApplication.translate("Menu","Dockable windows"))
		self.menu_iconSize = menu_settings.addMenu(QtCore.QCoreApplication.translate("Menu","Icon size"))
		menu_sorting = menu_settings.addMenu(QtCore.QCoreApplication.translate("Menu","Sort criterion"))
		menu_settings.addSeparator()
		menu_settings.addAction(action_config)
		
		menu_docks.addAction(self.dock_geotagging.toggleViewAction())
		menu_docks.addAction(self.dock_timezones.toggleViewAction())
		menu_docks.addAction(self.dock_keywords.toggleViewAction())
		menu_docks.addAction(self.dock_copyright.toggleViewAction())
		
		actiongroup_iconSize = QtGui.QActionGroup(self)
		sizes = list(self.dct_iconsize.keys())
		sizes.sort()
		for size in sizes:
			action_iconSize = QtGui.QAction(size,self)
			action_iconSize.setCheckable(True)
			action_iconSize.setChecked(size == self.ustr_iconsize)
			actiongroup_iconSize.addAction(action_iconSize)
			self.menu_iconSize.addAction(action_iconSize)
		
		actiongroup_sorting = QtGui.QActionGroup(self)
		actiongroup_sorting.addAction(self.action_sortByName)
		actiongroup_sorting.addAction(self.action_sortByTime)
		actiongroup_sorting.addAction(self.action_sortByCamera)
		menu_sorting.addAction(self.action_sortByName)
		menu_sorting.addAction(self.action_sortByTime)
		menu_sorting.addAction(self.action_sortByCamera)
		
		menu_help = self.menuBar().addMenu(QtCore.QCoreApplication.translate("Menu","&Help"))
		menu_help.addAction(action_about)
		menu_help.addAction(action_aboutQt)
		
		#---------------------------------------------------------------
		# wiring: connect widgets to functions (signals to slots)
		#---------------------------------------------------------------
		
		self.list_images.itemSelectionChanged.connect(self.listImagesSelectionChanged)
		self.list_images.itemChanged.connect(self.listImagesItemChanged)
		self.list_images.itemDoubleClicked.connect(self.openPreviewImage)
		
		#---------------------------------------------------------------
		
		self.scroll_image_label.leftClicked.connect(self.closePreviewImage)
		self.scroll_image_label.goBack.connect(self.closePreviewImage)
		self.scroll_image_label.loadNext.connect(self.loadNextPreviewImage)
		self.scroll_image_label.loadPrev.connect(self.loadPrevPreviewImage)
		
		#---------------------------------------------------------------
		
		action_quit.triggered.connect(self.quitEvent)
		self.action_apply.triggered.connect(self.applyChanges)
		self.action_save.triggered.connect(self.saveChanges)
		self.action_openDir.triggered.connect(self.selectDirectory)
		self.menu_iconSize.triggered.connect(self.adjustIconSize)
		menu_sorting.triggered.connect(self.setSortCriterion)
		self.action_rotateLeft.triggered.connect(self.rotateImageLeft)
		self.action_rotateRight.triggered.connect(self.rotateImageRight)
		self.action_resetAll.triggered.connect(self.resetAll)
		self.action_resetOrientation.triggered.connect(self.resetOrientation)
		self.action_resetLocation.triggered.connect(self.resetLocation)
		self.action_resetTimezones.triggered.connect(self.resetTimezones)
		self.action_resetKeywords.triggered.connect(self.resetKeywords)
		self.action_resetCopyright.triggered.connect(self.resetCopyright)
		self.action_locationLookUp.triggered.connect(self.dock_geotagging.lookUpCoordinates)
		self.action_openGimp.triggered.connect(self.openWithTheGimp)
		
		#---------------------------------------------------------------
		
		self.action_resetOrientation.changed.connect(self.updateResetAllAction)
		self.action_resetLocation.changed.connect(self.updateResetAllAction)
		self.action_resetTimezones.changed.connect(self.updateResetAllAction)
		self.action_resetKeywords.changed.connect(self.updateResetAllAction)
		self.action_resetCopyright.changed.connect(self.updateResetAllAction)
		
		#---------------------------------------------------------------
		
		self.dock_geotagging.dockDataUpdated.connect(self.updateLocation)
		self.dock_geotagging.dockResetTriggered.connect(self.resetLocation)
		
		#---------------------------------------------------------------
		
		self.dock_timezones.dockDataUpdated.connect(self.updateTimezones)
		self.dock_timezones.dockResetTriggered.connect(self.resetTimezones)
		
		#---------------------------------------------------------------
		
		self.dock_keywords.dockKeywordAdded.connect(self.addKeyword)
		self.dock_keywords.dockKeywordRemoved.connect(self.removeKeyword)
		self.dock_keywords.dockResetTriggered.connect(self.resetKeywords)
		
		#---------------------------------------------------------------
		
		self.dock_copyright.dockDataUpdated.connect(self.updateCopyright)
		self.dock_copyright.dockResetTriggered.connect(self.resetCopyright)
		
		#---------------------------------------------------------------
		
		action_config.triggered.connect(self.configureProgram)
		
		#---------------------------------------------------------------
		
		action_about.triggered.connect(self.aboutDialog)
		action_aboutQt.triggered.connect(self.aboutQtDialog)
		
		#---------------------------------------------------------------
		# construct main window
		#---------------------------------------------------------------
		self.main_widget = QtGui.QStackedWidget()
		self.main_widget.addWidget(self.list_images)
		self.main_widget.addWidget(self.scroll_image_label)
		self.setCentralWidget(self.main_widget)
		
		self.resize(self.size_window)
		
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_geotagging)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_timezones)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_keywords)
		self.addDockWidget(QtCore.Qt.RightDockWidgetArea,self.dock_copyright)
		
		self.setWindowTitle(QtCore.QCoreApplication.translate("MainWindow","FotoPreProcessor"))
		self.setWindowIcon(QtGui.QIcon(os.path.join(sys.path[0],"icons","FPP.png")))
		
		self.setStyleSheet(":disabled { color: gray; }")
		self.show()
	
	
	def checkOnExit(self):
		edited = False
		for i in range(0,self.list_images.count()):
			if self.list_images.item(i).edited():
				edited = True
				break
		if edited:
			if self.wasSaved:
				# was already saved, so only ask if changes should be applied
				answer = QtGui.QMessageBox.question(
					self,
					QtCore.QCoreApplication.translate("Dialog","Exit Application"),
					QtCore.QCoreApplication.translate("Dialog","Some changes were made.\nDo you want to apply them before exiting?"),
					QtGui.QMessageBox.Apply | QtGui.QMessageBox.Discard 
				)
			else:
				answer = QtGui.QMessageBox.question(
					self,
					QtCore.QCoreApplication.translate("Dialog","Exit Application"),
					QtCore.QCoreApplication.translate("Dialog","Some changes were made.\nDo you want to apply or save them before exiting?"),
					QtGui.QMessageBox.Apply | QtGui.QMessageBox.Save | QtGui.QMessageBox.Discard 
				)
			if answer == QtGui.QMessageBox.Apply:
				self.applyChanges()
			elif answer == QtGui.QMessageBox.Save:
				self.saveChanges()
		self.dock_copyright.close() # i.e.: save copyright DB
		self.dock_keywords.close()  # i.e.: save keywords DB
		# save miscellaneous settings
		settings = QtCore.QSettings()
		settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
		settings.setValue("IconSize",self.ustr_iconsize)
		settings.setValue("SortCriterion",self.int_sorting)
		settings.setValue("WindowSize",self.size())
	
	
	def quitEvent(self):
		"""Program shall quit: check for changes and quit."""
		self.checkOnExit()
		QtGui.QApplication.instance().quit()
	
	
	def closeEvent(self,event):
		"""Window received close event: check for changes and accept event."""
		self.checkOnExit()
		event.accept()
	
	
	def selectDirectory(self):
		path = QtGui.QFileDialog.getExistingDirectory(self,
			QtCore.QCoreApplication.translate("Dialog","Select Directory"),
			self.ustr_path,
			QtGui.QFileDialog.DontUseNativeDialog
		)
		if len(path) > 0:
			self.setDirectory(path)
	
	
	def setDirectory(self,path=""):
		path = str(path)
		if os.path.isdir(path) and len(self.ustr_path_exiftool) > 0:
			self.ustr_path = path
			self.setWindowTitle(
				QtCore.QCoreApplication.translate(
					"MainWindow",
					"FotoPreProcessor"
				) + ": " + path
			)
		else:
			# either path does not exist or Exiftool is not defined
			# delete list, reset path and title...
			self.ustr_path = str()
			self.setWindowTitle(
				QtCore.QCoreApplication.translate(
					"MainWindow",
					"FotoPreProcessor"
				)
			)
		self.updateImageList()
	
	
	def adjustIconSize(self,action=None):
		if action == None:
			actions = self.menu_iconSize.actions()
			for action in actions:
				self.ustr_iconsize = str(action.text())
				if action.isChecked(): break
		else:
			self.ustr_iconsize = str(action.text())
		self.list_images.setIconSize(self.dct_iconsize[self.ustr_iconsize])
		for i in range(0,self.list_images.count()):
			self.list_images.item(i).updateIcon()
	
	
	def setSortCriterion(self,action):
		if action == self.action_sortByTime:
			self.int_sorting = FotoPreProcessorItem.FPPGalleryItem.SortByTime
		elif action == self.action_sortByCamera:
			self.int_sorting = FotoPreProcessorItem.FPPGalleryItem.SortByCamera
		else:
			self.int_sorting = FotoPreProcessorItem.FPPGalleryItem.SortByName
		
		for i in range(0,self.list_images.count()):
			self.list_images.item(i).setSortCriterion(self.int_sorting)
		self.list_images.sortItems()
	
	
	def getFirstTextChild(self,node=None):
		value = str()
		for child in node.childNodes:
			if child.nodeType == node.TEXT_NODE and len(child.nodeValue.strip()) > 0:
				value = str(node.childNodes[0].nodeValue.strip())
				break
		return value
	
	
	def updateImageList(self):
		self.list_images.clear()
		
		progress = QtGui.QProgressDialog(self)
		progress.setWindowModality(QtCore.Qt.WindowModal)
		progress.setMinimumDuration(0)
		progress.setAutoClose(False)
		progress.setAutoReset(False)
		
		if self.action_sortByName.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByName
		elif self.action_sortByTime.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByTime
		elif self.action_sortByCamera.isChecked():
			sortCriterion = FotoPreProcessorItem.FPPGalleryItem.SortByCamera
		
		# 2012-10-17, bug: program is stalled when a directory is part of the filelist
		# solution: scan filelist and remove all non-regular files
		# 2014-01-17: removed .decode() as it ran into errors with UTF-8 filenames
		try:
			filelist = [os.path.join(self.ustr_path,i) for i in os.listdir(self.ustr_path) if os.path.isfile(os.path.join(self.ustr_path,i))]
		except:
			filelist = list()
		
		l_filelist = len(filelist)
		progress.setRange(0,l_filelist)
		progress.setValue(0)
		
		if l_filelist > 0 and len(self.ustr_path_exiftool) > 0:
			proc_exiftool = subprocess.Popen([
				self.ustr_path_exiftool,
				"-stay_open","True",
				"-@","-",
				"-common_args",
				"-X",
				"-b",
				"-m",
				"-if",
				"$MIMEType =~ /^image/",
				"-d",
				"%Y %m %d %H %M %S",
				"-Orientation",
				"-DateTimeOriginal",
				"-Keywords",
				"-FocalLength#",
				"-ScaleFactor35efl",
				"-Aperture",
				"-ShutterSpeed",
				"-ISO",
				"-Model",
				"-LensType",
				"-ThumbnailImageValidArea",
				"-Copyright",
				"-Author",
				"-GPS:GPSLatitude#",
				"-GPS:GPSLatitudeRef#",
				"-GPS:GPSLongitude#",
				"-GPS:GPSLongitudeRef#",
				"-GPS:GPSAltitude#",
				"-GPS:GPSAltitudeRef#",
				"-ThumbnailImage",
				"-PreviewImage",
				"-ImageSize"
			],stdout=subprocess.PIPE,stdin=subprocess.PIPE,stderr=subprocess.PIPE)
			
			for i in range(0,l_filelist,self.int_stepsize):
				#
				# read self.int_stepsize images at once and process output
				#
				command = "\n".join(filelist[i:i+self.int_stepsize]) + "\n-execute\n"
				proc_exiftool.stdin.write(command.encode("UTF-8"))
				proc_exiftool.stdin.flush()
				
				# os.read is needed for stdout/stderr "file" objects...
				# in addition, exiftool output ends with {ready}, so we have to catch it
				f_stdout = proc_exiftool.stdout.fileno()
				str_output = str()
				QtCore.QCoreApplication.processEvents()
				while not str_output[-64:].strip().endswith('{ready}'):
					# read until {ready} occurs
					str_output += os.read(f_stdout,self.int_readsize).decode()
				QtCore.QCoreApplication.processEvents()
				str_output = str_output.strip()[:-7]
				
				try:
					descriptionElements = xml.dom.minidom.parseString(str_output).getElementsByTagName("rdf:Description")
				except:
					descriptionElements = tuple()
				
				self.list_images.setUpdatesEnabled(False)
				
				for k,description in enumerate(descriptionElements):
					#
					# process every identified image
					#
					filepath = str(description.getAttribute("rdf:about"))
					
					if len(filepath) == 0: continue
					if progress.wasCanceled(): break
					
					filename = os.path.basename(filepath)
					progress.setValue(progress.value()+1)
					progress.setLabelText("{0} {1}...".format(
						QtCore.QCoreApplication.translate("Dialog","Processing Image"),
						filename
					))
					
					timestamp    = str()
					focalLength  = str()
					cropFactor   = str()
					aperture     = str()
					shutterSpeed = str()
					isoValue     = str()
					cameraModel  = str()
					lensType     = str()
					thumbArea    = str()
					latitude     = str()
					latitudeRef  = str()
					longitude    = str()
					longitudeRef = str()
					elevation    = str()
					elevationRef = str()
					thumbData    = str()
					previewData  = str()
					author       = str()
					copyright    = str()
					imgwidth     = -1
					imgheight    = -1
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
							copyright = self.getFirstTextChild(node)
							try:    copyright = re.match(r'^(©|\(C\)|\(c\)|Copyright \(C\)|Copyright \(c\)|Copyright ©) [0-9-]* (.*)',copyright).groups()[1]
							except: pass
						elif node.localName == "Author":
							author = self.getFirstTextChild(node)
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
						elif node.localName == "PreviewImage":
							previewData = base64.b64decode(self.getFirstTextChild(node))
						elif node.localName == "ImageSize":
							try:
								imgwidth,imgheight = [int(i) for i in self.getFirstTextChild(node).split("x")]
							except:
								pass
					
					# 2013-01-08: +support for preview images >160px
					# 2013-05-02: -support for preview images >160px (reduce memory footprint, instead do preview on-demand)
					# resources: thumbnail image
					# maximum: self.iconsize_max
					# 1. try thumb
					# 2. use unknownPicture2
					# sidenote: optimised QPixmap usage; by avoiding stupid
					# re-assignment (thumbImage = QPixmap()) memory usage is kept low
					thumbImage = QtGui.QPixmap()
					if not thumbImage.loadFromData(previewData):
						# no preview image available, try thumb
						if thumbImage.loadFromData(thumbData):
							try:
								# try to fit thumbnail into its area
								(x1,x2,y1,y2) = tuple(thumbArea.split(" "))
								thumbRect = QtCore.QRect()
								thumbRect.setTop(int(y1))
								thumbRect.setBottom(int(y2))
								thumbRect.setLeft(int(x1))
								thumbRect.setRight(int(x2))
								thumbImage = thumbImage.copy(thumbRect)
							except:
								pass
						else:
							# no thumb: load image directly
							if not thumbImage.load(filepath):
								# direct image loading failed: load unknownPicture2
								if not thumbImage.load(os.path.join(sys.path[0],"icons","unknownPicture2.png")):
									# well, at this point we have a non-valid
									# image and an erroneous installation...
									continue
					
					# scale thumb image and store it in the item
					thumbImage = thumbImage.scaled(
						self.dct_iconsize[self.iconsize_max],
						QtCore.Qt.KeepAspectRatio,
						QtCore.Qt.SmoothTransformation
					)
					item.setThumbnail(thumbImage)
					item.setSize(imgwidth,imgheight);
					
					if len(timestamp) == 0:
						# no EXIF timestamp , so obtain timestamp from filesystem
						timestamp = time.strftime(
							"%Y %m %d %H %M %S",
							time.localtime(os.path.getctime(filepath))
						)
					try:    item.setTimestamp(timestamp.split(" "))
					except: pass
				
					settings = []
					if len(focalLength) != 0:
						try:
							settings.append("{0} mm ({1})".format(
								int(float(focalLength) * float(cropFactor)),
								QtCore.QCoreApplication.translate("ItemToolTip","on full-frame")
							))
						except:
							settings.append("{0} ({1})".format(
								focalLength,
								QtCore.QCoreApplication.translate("ItemToolTip","physical")
							))
					if len(aperture) != 0:
						settings.append("f/" + aperture)
					if len(shutterSpeed) != 0:
						settings.append(shutterSpeed + " s")
					if len(isoValue) != 0:
						settings.append("ISO " + isoValue)
					if len(settings) != 0:
						item.setCameraSettings(", ".join(settings))
					
					settings = []
					if len(cameraModel) > 0 and not cameraModel.startswith("Unknown"):
						settings.append(cameraModel)
					if len(lensType) > 0 and not lensType.startswith("Unknown"):
						settings.append(lensType)
					if len(settings) != 0:
						item.setCameraHardware(", ".join(settings))
					
					try:
						latitude = float(latitude)
						longitude = float(longitude)
						if latitudeRef == "S": latitude = -latitude
						if longitudeRef == "W": longitude = -longitude
						try:    elevation = float(elevation)
						except: elevation = 0.0
						if elevationRef == "1": elevation = -elevation
						item.setLocation(latitude,longitude,elevation)
					except:
						pass
					
					# copyright string = author name
					#
					# additional symbols and strings (i.e. "Copyright" and
					# (c) or © resp.) are added later by the exec routine
					#
					# Thus this snippet first tries to use author information
					# to set the copyright notice of the item. If no author
					# information is given, the copyright tag is evaluated.
					# If everything fails, no copyright is set (remains "").
					if len(author) > 0:
						item.setCopyright(author)
					else:
						if len(copyright) > 0:
							item.setCopyright(copyright)

					item.setSortCriterion(sortCriterion)
					item.saveState()
					#
					# end of node processing
					#
					
				if progress.wasCanceled(): break
				#
				# end of file processing
				#
			
			# terminate exiftool
			proc_exiftool.communicate("-stay_open\nFalse\n".encode("utf-8"))
			
		#
		# end of image package processing
		#
		self.list_images.setUpdatesEnabled(True)
			
		if progress.wasCanceled():
			self.list_images.clear()
		else:
			self.list_images.sortItems()
			self.adjustIconSize()
		
		progress.close()
		
		#self.action_apply.setEnabled(False)
		self.action_save.setEnabled(False)
		self.wasSaved = False
		
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
		for i in range(0,self.list_images.count()):
			if self.list_images.item(i).edited():
				edited = True
				break
		if edited: self.wasSaved = False
		#self.action_apply.setEnabled(edited and len(self.ustr_path_exiftool) > 0)
		self.action_save.setEnabled(edited and len(self.ustr_path_exiftool) > 0)
	
	
	def openPreviewImage(self,item):
		# present preview of the image list item currently double-clicked
		self.list_images.setCurrentRow(self.list_images.currentRow(),QtGui.QItemSelectionModel.ClearAndSelect)
		self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
		self.scroll_image_label.adjustSize()
		self.main_widget.setCurrentIndex(1)
	
	
	def closePreviewImage(self):
		# restore image list
		self.main_widget.setCurrentIndex(0)
	
	
	def loadPrevPreviewImage(self):
		# load the previous image in the list
		count = self.list_images.count()
		index = self.list_images.currentRow()
		if index == 0:
			index = count - 1
		else:
			index = index - 1
		self.list_images.setCurrentRow(index,QtGui.QItemSelectionModel.ClearAndSelect)
		item = self.list_images.currentItem()
		self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
		self.scroll_image_label.adjustSize()
	
	
	def loadNextPreviewImage(self):
		# load the previous image in the list
		count = self.list_images.count()
		index = self.list_images.currentRow()
		if index == count - 1:
			index = 0
		else:
			index = index + 1
		self.list_images.setCurrentRow(index,QtGui.QItemSelectionModel.ClearAndSelect)
		item = self.list_images.currentItem()
		self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
		self.scroll_image_label.adjustSize()
	
	
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
			latitude,longitude,elevation = None,None,None
			enabled_geo = self.dock_geotagging.isEnabled()
			if l_location <= 1:
				try:
					(latitude,longitude,elevation) = location.pop()
				except:
					pass
				enabled_geo = True
			elif l_location > 1 and enabled_geo:
				answer = QtGui.QMessageBox.question(
					self,
					QtCore.QCoreApplication.translate("Dialog","Location Collision"),
					QtCore.QCoreApplication.translate("Dialog","The selected images are tagged with different locations.\nDo you want to reset them?\nIf you answer \"No\", GeoTagging will be disabled."),
					QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
				)
				if answer == QtGui.QMessageBox.Yes:
					locationEdited = False
					for item in items:
						item.setLocation(None,None,None)
						locationEdited = locationEdited or item.locationEdited()
					enabled_geo = True
				else:
					enabled_geo = False
			
			self.dock_geotagging.setEnabled(enabled_geo)
			self.action_locationLookUp.setEnabled(enabled_geo)
			self.dock_geotagging.setLocation(latitude,longitude,elevation)
			self.dock_timezones.setLocation(latitude,longitude)
			self.dock_geotagging.setResetEnabled(locationEdited)
			
			# import timezone corrections or resolve conflicts
			enabled_tz = self.dock_timezones.isEnabled()
			fromTz,toTz = "UTC","UTC"
			if l_timezones <= 1:
				try:
					(fromTz,toTz) = timezones.pop()
				except:
					pass
				enabled_tz = True
			elif l_timezones > 1 and enabled_tz:
				lst_timezones = list()
				timezones.add(("UTC","UTC"))
				for tz in timezones:
					lst_timezones.append("{0} → {1}".format(*tz))
				lst_timezones.sort()
				lst_timezones.insert(0,"Disable timezone settings.")
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate("Dialog","Timezones Collision"),
					QtCore.QCoreApplication.translate("Dialog","The selected images feature different timezone correction information.\nWhich one should be used?\nIf you cancel this dialog, timezone settings will be disabled."),
					lst_timezones,0,False
				)
				if ok and answer != lst_timezones[0]:
					(fromTz,toTz) = tuple(str(answer).split(" → ",1))
					timezonesEdited = False
					for item in items:
						item.setTimezones(fromTz,toTz)
						timezonesEdited = timezonesEdited or item.timezonesEdited()
					enabled_tz = True
				else:
					enabled_tz = False
			
			self.dock_timezones.setEnabled(enabled_tz)
			self.dock_timezones.setTimezones(fromTz,toTz)
			self.dock_timezones.setResetEnabled(timezonesEdited)
			
			# import keywords or resolve conflicts
			enabled_keywords = self.dock_keywords.isEnabled()
			self.dock_keywords.setKeywords()
			tpl_kws = tuple()
			if l_keywords <=  1:
				try:
					tpl_kws = tuple(keywords.pop())
				except:
					pass
				enabled_keywords = True
			elif l_keywords > 1 and enabled_keywords:
				str_disable = QtCore.QCoreApplication.translate("Dialog","Disable keyword settings.")
				str_empty = QtCore.QCoreApplication.translate("Dialog","Remove all keywords from all images.")
				str_union = QtCore.QCoreApplication.translate("Dialog","Apply union of all keywords to all images.")
				str_inter = QtCore.QCoreApplication.translate("Dialog","Only edit keywords common to all images.")
				str_diff  = QtCore.QCoreApplication.translate("Dialog","Remove common keywords and merge the remaining.")
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate("Dialog","Keyword Collision"),
					QtCore.QCoreApplication.translate("Dialog","The selected images feature different sets of keywords.\nWhat do you want to do?\nIf you cancel this dialog, keyword settings will be disabled."),
					(str_inter,str_empty,str_union,str_diff),0,False
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
					enabled_keywords = True
				else:
					enabled_keywords = False
			
			self.dock_keywords.setEnabled(enabled_keywords)
			self.dock_keywords.setKeywords(tpl_kws)
			self.dock_keywords.setResetEnabled(keywordsEdited)
			
			# import copyright data or resolve conflicts
			enabled_copyright = self.dock_copyright.isEnabled()
			copyrightNotice = str()
			if l_copyright <= 1:
				try:
					copyrightNotice = copyright.pop()
				except:
					pass
				enabled_copyright = True
			elif l_copyright > 1 and enabled_copyright:
				lst_copyright = ["None (clear copyright notice)"]
				lst_copyright.extend(list(copyright))
				(answer,ok) = QtGui.QInputDialog.getItem(self,
					QtCore.QCoreApplication.translate("Dialog","Copyright Collision"),
					QtCore.QCoreApplication.translate("Dialog","The selected images feature different copyright notices.\nWhich one should be used?\nIf you cancel this dialog, copyright settings will be disabled."),
					lst_copyright,0,False
				)
				if ok:
					if answer != lst_copyright[0]:
						copyrightNotice = str(answer)
					copyrightEdited = False
					for item in items:
						item.setCopyright(copyrightNotice)
						copyrightEdited = copyrightEdited or item.copyrightEdited()
					enabled_copyright = True
				else:
					enabled_copyright = False
			
			self.dock_copyright.setEnabled(enabled_copyright)
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
			#
			# 2012-11-27: no item selected: reset docks
			#
			self.dock_geotagging.setLocation()
			self.dock_timezones.setTimezones()
			self.dock_keywords.setKeywords()
			self.dock_copyright.setCopyright()
			
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
		if self.main_widget.currentIndex() == 1:
			self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
			self.scroll_image_label.adjustSize()
	
	def rotateImageRight(self):
		for item in self.list_images.selectedItems(): item.rotateRight()
		self.action_resetOrientation.setEnabled(True)
		if self.main_widget.currentIndex() == 1:
			self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
			self.scroll_image_label.adjustSize()
	
	def resetOrientation(self):
		for item in self.list_images.selectedItems(): item.resetOrientation()
		if self.main_widget.currentIndex() == 1:
			self.scroll_image_label.updateItem(str(os.path.join(self.ustr_path,item.filename())),item.orientation(),item.size(),item.toolTip())
			self.scroll_image_label.adjustSize()
	
	#-----------------------------------------------------------------------
	# geotagging: methods
	#-----------------------------------------------------------------------
	
	def updateLocation(self,lat=None,lon=None,ele=0.0):
		try:
			latitude  = float(lat)
			longitude = float(lon)
			elevation = float(ele)
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
	
	def updateTimezones(self,ftz=str(),ttz=str()):
		try:
			fromTz = str(ftz)
			toTz   = str(ttz)
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
	
	def addKeyword(self,keyword=str()):
		try:
			keyword = str(keyword)
			edited = False
			for item in self.list_images.selectedItems():
				item.addKeyword(keyword)
				edited = edited or item.edited()
			self.dock_keywords.setResetEnabled(edited)
			self.action_resetKeywords.setEnabled(edited)
		except:
			pass
	
	
	def removeKeyword(self,keyword=str()):
		try:
			keyword = str(keyword)
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
	
	def updateCopyright(self,notice=str()):
		try:
			notice = str(notice)
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
	
	def processChanges(self):
		"""Inspect image list, collect all changes and generate a command list.

Returns:
   A list of lists: [[cmd,arg1,...argn],...]"""
		commands = list()
		dct_parameters = dict()
		lst_all_files = list()
		for i in range(0,self.list_images.count()):
			item = self.list_images.item(i)
			name = str(os.path.join(self.ustr_path,item.filename()))
			lst_all_files.append(name)
			
			if item.edited():
				parameters = list()
				
				if item.orientationEdited():
					# need to set --printConv for Orientation by adding "#"
					parameters.append("-Orientation#={0}".format(item.orientation()))
				
				if item.locationEdited():
					try:
						(lat,lon,ele) = item.location()
						latitude  = str(abs(lat))
						longitude = str(abs(lon))
						elevation = str(abs(ele))
						if lat < 0:
							latitudeRef = "S"
						else:
							latitudeRef = "N"
						if lon < 0:
							longitudeRef = "W"
						else:
							longitudeRef = "E"
						if ele < 0:
							elevationRef = "1"
						else:
							elevationRef = "0"
					except:
						latitude     = str()
						latitudeRef  = str()
						longitude    = str()
						longitudeRef = str()
						elevation    = str()
						elevationRef = str()
					parameters.append("-GPSLatitude={0}".format(latitude))
					parameters.append("-GPSLatitudeRef={0}".format(latitudeRef))
					parameters.append("-GPSLongitude={0}".format(longitude))
					parameters.append("-GPSLongitudeRef={0}".format(longitudeRef))
					parameters.append("-GPSAltitude={0}".format(elevation))
					parameters.append("-GPSAltitudeRef={0}".format(elevationRef))
				
				if item.timezonesEdited():
					try:
						t     = item.shiftedTimestamp().strftime("%Y:%m:%d %H:%M:%S")
						t_utc = item.utcTimestamp().strftime("%Y:%m:%d %H:%M:%S")
					except:
						t     = str()
						t_utc = str()
					parameters.append("-AllDates={0}".format(t))
					parameters.append("-GPSDateStamp={0}".format(t_utc))
					parameters.append("-GPSTimeStamp={0}".format(t_utc))
				
				if item.keywordsEdited():
					keywords = item.keywords()
					if len(keywords) == 0: keywords = ("",)
					for keyword in keywords:
						parameters.append("-Keywords={0}".format(keyword))
				
				if item.copyrightEdited():
					parameters.append("-Copyright=Copyright (C) {0} {1}".format(
						item.shiftedTimestamp().strftime("%Y"),
						item.copyright()
					))
					parameters.append("-Author={0}".format(
						item.copyright()
					))
				
				dct_parameters[name] = parameters
		
		return dct_parameters
		
	
	def saveChanges(self):
		"""Process image list (cf. processChanges()) and store YAMLed command list.
This method creates a "save file" dialog."""

		filename = QtGui.QFileDialog.getSaveFileName(self,QtCore.QCoreApplication.translate("Dialog","Save File"))
		if len(filename) > 0:
			with open(filename,"w") as f:
				yaml.dump(self.processChanges(),f)
			self.wasSaved = True
	
	
	def applyChanges(self):
		dlg = FotoPreProcessorWidgets.FPPApplyChangesDialog(self.ustr_path_exiftool)
		dlg.addParameters(self.processChanges())
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
				command.append(str(os.path.join(self.ustr_path,item.filename())))
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
			settings.setIniCodec(QtCore.QTextCodec.codecForName("UTF-8"))
			
			self.ustr_path_exiftool = self.sanitiseExecutable(
				str(settings.value("ExiftoolPath","/usr/bin/exiftool").toString())
			)
			self.ustr_path_gimp = self.sanitiseExecutable(
				str(settings.value("TheGimpPath","/usr/bin/gimp").toString())
			)
			self.action_openGimp.setEnabled(len(self.ustr_path_gimp) > 0)
			self.action_openDir.setEnabled(len(self.ustr_path_exiftool) > 0)
			#self.action_apply.setEnabled(self.action_apply.isEnabled() and len(self.ustr_path_exiftool) > 0)
			self.action_save.setEnabled(self.action_save.isEnabled() and len(self.ustr_path_exiftool) > 0)
			
			try:    self.int_stepsize = int(settings.value("StepSize",4))
			except: self.int_stepsize = 4
			
			try:    self.int_readsize = int(settings.value("ReadSize",1024))
			except: self.int_readsize = 1024
	
			try:    self.float_readdelay = float(settings.value("ReadDelay",0.0001))
			except: self.float_readdelay = 0.0001
			
			try:    self.lst_naming_cmd = settings.value("NamingScheme",dlg.DEFAULT_NAMING_SCHEME).split(" ")
			except: self.lst_naming_cmd = dlg.DEFAULT_NAMING_SCHEME.split(" ")
	
	#-----------------------------------------------------------------------
	
	def aboutDialog(self):
		dlg = FotoPreProcessorWidgets.FPPAboutDialog(VERSION)
		dlg.exec_()

	
	def aboutQtDialog(self):
		QtGui.QMessageBox.aboutQt(self)



def parseArguments(progpath,set_args):
	bool_help = True
	bool_license = True
	bool_version = True
	
	# check if help was requested; if yes, display help and exit without error
	try:
		set_args.remove("-h")
	except:
			try:
				set_args.remove("--help")
			except:
				bool_help = False
	if bool_help:
		print(app.translate("CLI","""Usage: {progname} [-h][-l][-v][DIR]

PyQt4-based (EXIF) metadata management of images in a directory.

Optional arguments:
   DIR             directory that should be opened at start
   -h, --help      show this help message and exit
   -l, --license   show full license notice and exit
   -v, --version   show version information and exit

Copyright (C) 2012-2015 Frank Abelbeck <frank.abelbeck@googlemail.com>

This program comes with ABSOLUTELY NO WARRANTY. It is free software,
and you are welcome to redistribute it under certain conditions
(see argument --license for details).
""").format(progname=os.path.basename(progpath)))
	
	# check if license was requested; if yes, display license and exit without error
	try:
		set_args.remove("-l")
	except:
			try:
				set_args.remove("--license")
			except:
				bool_license = False
	if bool_license:
		print(app.translate("CLI","License information:"))
		print(LICENSE)
	
	# check if version was requested; if yes, display version and exit without error
	try:
		set_args.remove("-v")
	except:
			try:
				set_args.remove("--version")
			except:
				bool_version = False
	if bool_version:
		print(app.translate("CLI","Version:"),VERSION)
	
	return not(bool_help or bool_license or bool_version)


if __name__ == '__main__':
	# setup Qt application and pass commandline arguments
	app = QtGui.QApplication(sys.argv)
	
	# initialise application information used by settings
	app.setApplicationName("FotoPreProcessor")
	app.setOrganizationName("Abelbeck");
	app.setOrganizationDomain("abelbeck.wordpress.com");
	
	# initialise translation service
	system_locale = str(QtCore.QLocale.system().name()[0:2])
	qtTranslator = QtCore.QTranslator()
	qtTranslator.load(
		"qt_"+system_locale,
		str(QtCore.QLibraryInfo.location(QtCore.QLibraryInfo.TranslationsPath))
	)
	fppTranslator = QtCore.QTranslator()
	fppTranslator.load(
		"FotoPreProcessor."+system_locale,
		os.path.join(sys.path[0],"i18n")
	)
	app.installTranslator(qtTranslator)
	app.installTranslator(fppTranslator)
	
	# obtain command line arguments, filtered by QApplication
	qargs = [str(i) for i in app.arguments()]
	progpath = qargs[0]
	set_args = set(qargs[1:])
	if parseArguments(progpath,set_args):
		# argument parsing returned True, i.e.no information was requested
		# via CLI, and therefore GUI is allowed to start:
		# create main window and set directory from remaining arguments
		mainwindow = FPPMainWindow()
		if mainwindow.isReady():
			for argpath in set_args:
				try:
					os.path.expanduser(argpath)
					if not os.path.isabs(argpath):
						argpath = str(os.path.join(os.getcwd(),argpath))
					argpath = str(os.path.normpath(argpath))
					if os.path.isdir(argpath):
						mainwindow.setDirectory(argpath)
						break
				except:
					pass
			# start event loop, i.e. start application
			app.exec_()

