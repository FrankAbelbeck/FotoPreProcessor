#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
FotoPreProcessorTools: GeoTagging GUI, timezone management, strings DB
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

import datetime,pytz,os.path,sys,codecs

from PyQt4 import QtGui, QtCore, QtWebKit


class FPPTimezone:
	"""Class for the management of timezone information.

Relies on a properly setup timezone database (sys-libs/timezone-data) and
provides the ability to reverse look-up a timezone name by position."""
	
	def __init__(self):
		"""Constructor; initialise fields"""
		self.dct_timezones = dict()
		self.dct_timezone_offsets = dict()
		self.tpl_timezone_names = tuple()
	
	
	def loadTimezoneDB(self,filename=u"/usr/share/zoneinfo/zone.tab"):
		"""Load timezone information from a certain file.

The files has to contain tab-delimited information on timezones:
two-letter country-code, coordinates, timezone name

Coordinates are expected as latitude longitude pairs of sign-degrees-minutes
(+DDMM+DDDMM) or sign-degrees-minutes-seconds (+DDMMSS+DDDMMSS)."""
		t_normal = datetime.datetime(2012,1,1,12,0,0)
		t_summer = datetime.datetime(2012,6,1,12,0,0)
		self.dct_timezones.clear()
		self.dct_timezone_offsets.clear()
		lst_tzname = list()
		with open(u"/usr/share/zoneinfo/zone.tab",u"r") as f:
			for line in f:
				if not line.startswith(u"#"):
					data = line.strip().split(u"\t")
					coords = unicode(data[1])
					tzname = unicode(data[2])
					if coords[5] in ("+","-"):
						# format: +DDMM+DDDMM
						lat_deg = int(coords[0:3])
						lat_min = int(coords[3:5])
						lat_sec = 0
						lon_deg = int(coords[5:9])
						lon_min = int(coords[9:11])
						lon_sec = 0
						# convert from dms to decimal degrees
						lat = float(coords[0:3]) + float(coords[3:5])/60.0
						lon = float(coords[5:9]) + float(coords[9:11])/60.0
					else:
						# format: +DDMMSS+DDDMMSS
						lat_deg = int(coords[0:3])
						lat_min = int(coords[3:5])
						lat_sec = int(coords[5:7])
						lon_deg = int(coords[7:11])
						lon_min = int(coords[11:13])
						lon_sec = int(coords[13:15])
						# convert from dms to decimal degrees
						lat = float(coords[0:3]) + (float(coords[3:5]) + float(coords[5:7])/60.0)/60.0
						lon = float(coords[7:11]) + (float(coords[11:13]) + float(coords[13:15])/60.0)/60.0
					tz = pytz.timezone(tzname)
					t_n = tz.localize(t_normal).strftime(u"%z")
					t_s = tz.localize(t_summer).strftime(u"%z")
					self.dct_timezones[tzname] = (
						lat,
						lon
					)
					self.dct_timezone_offsets[tzname] = (
						(int(t_n[0:3])*60+int(t_n[3:5])),
						(int(t_s[0:3])*60+int(t_s[3:5]))
					)
					lst_tzname.append(tzname)
		lst_tzname.sort()
		lst_tzname.insert(0,u"UTC")
		self.dct_timezones[u"UTC"] = (51.477678,0.0) # http://en.wikipedia.org/wiki/World_Geodetic_System
		self.dct_timezone_offsets[u"UTC"] = (0,0)
		self.tpl_timezone_names = tuple(lst_tzname)
	
	
	def timezoneNames(self):
		"""Return a tuple with all recognized timezone names."""
		return self.tpl_timezone_names
	
	
	def timezoneIndex(self,tzName=unicode()):
		"""Return the index of given tzName in the timezone list.

Returns -1 if tzName was not found."""
		try:    retval = self.tpl_timezone_names.index(unicode(tzName))
		except: retval = -1
		return retval
	
	
	def timezoneOffset(self,name=None):
		"""Return UTC offsets in minutes of timezone with given name.

A tuple (normal,dst) with offsets for both normal and daylight saving time."""
		try:    offset = self.dct_timezone_offsets[unicode(name)]
		except: offset = (0,0)
		return offset
	
	def timezoneName(self,latitude=None,longitude=None):
		"""Look-up and return timezone name for given position.

Returns None if no timezone name is found."""
		try:
			latitude = float(latitude)
			longitude = float(longitude)
		except:
			pass
		distance = 360**2 + 180**2
		result = None
		for tzname,coord in self.dct_timezones.iteritems():
			dist = (coord[0]-latitude)**2 + (coord[1]-longitude)**2
			if dist < distance:
				result = tzname
				distance = dist
		return result



class FPPGeoBookmarks:
	"""Class for the management of simple location bookmarks.

Bookmarks are stored in plain-text UTF-8 encoded files.

Each line of such a file contains latitude, longitude and bookmark name,
delimited by simple spaces. Example line:

52.7 9.3001 Test Location

Lines starting with a # as well as ill-formed coordinates are ignored."""
	
	def __init__(self):
		"""Constructor; initialise fields."""
		self.dct_locations = dict()
		self.str_filename = unicode()
		self.bool_changed = False
	
	def loadFile(self,filename=None):
		"""Load and process given file and populate the internal bookmark database."""
		self.dct_locations.clear()
		try:
			with codecs.open(filename,u"r",u"utf-8") as f:
				for line in f:
					if not line.startswith("#"):
						try:
							(lat,lon,name) = line.strip().split(u" ",2)
							self.dct_locations[unicode(name)] = (float(lat),float(lon))
						except:
							pass
			self.str_filename = unicode(filename)
			self.bool_changed = False
		except:
			pass
	
	
	def names(self):
		"""Return all names currently stored in the bookmark database."""
		return self.dct_locations.keys()
	
	
	def listLocations(self):
		"""Return all name-location tuples currently stored in the bookmark database.

Returns a sorted tuple of name-location tuples (name,(latitude,longitude))"""
		lst_locations = []
		for name,location in self.dct_locations.iteritems():
			lst_locations.append((name,location))
		lst_locations.sort()
		return tuple(lst_locations)
	
	
	def readLocation(self,name=None):
		"""Return location tuple (latitude,longitude) of bookmark with given name."""
		try:    location = self.dct_locations[unicode(name)]
		except: location = None
		return location
	
	
	def writeLocation(self,name=None,latitude=None,longitude=None):
		"""Create a bookmark with given name and given location.

Existing bookmarks will be overwritten."""
		try:
			lat = float(latitude)
			lon = float(longitude)
			nam = unicode(name)
		except:
			pass
		else:
			if nam in self.dct_locations.keys():
				# bookmark exists; check if it is changed
				(lat_old,lon_old) = self.dct_locations[unicode(name)]
				if lat_old != lat or lon_old != lon:
					self.bool_changed = True
			else:
				# new bookmark: database is changed
				self.bool_changed = True
			self.dct_locations[unicode(name)] = (float(latitude),float(longitude))
	
	
	def saveFile(self,filename=None,force=False):
		"""Save current bookmark database in a file with given name.

If no filename is given, fall back to name of last file loaded.

File will only be altered if database was changed since last file loading.
This behaviour can be overridden by setting force=True."""
		if filename == None and len(self.str_filename) != 0:
			filename = self.str_filename
		try:
			if self.bool_changed or bool(force):
				with codecs.open(filename,u"w",u"utf-8") as f:
					for name,location in self.dct_locations.iteritems():
						f.write(u"{0} {1} {2}\n".format(float(location[0]),float(location[1]),unicode(name)))
		except:
			pass



class FPPGeoTaggingDialog(QtGui.QDialog):
	"""Class for an OpenStreetMap-based geotagging dialog based on QtGui.QDialog.

Relies on a custom "FotoPreProcessorOSM.html" file for OpenStreetMap interaction
and allows to load and store location bookmarks in "FotoPreProcessor.locations"."""
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields, load bookmarks and construct GUI."""
		QtGui.QDialog.__init__(self,parent)
		
		# load timezone info and bookmarks
		self.tz = FPPTimezone()
		self.tz.loadTimezoneDB()
		self.bookmarks = FPPGeoBookmarks()
		self.bookmarks.loadFile(os.path.join(sys.path[0],u"FotoPreProcessor.locations"))
		
		# prepare progressbar (webpage loading progress) and webview
		self.progressbar = QtGui.QProgressBar()
		self.webview = QtWebKit.QWebView()
		
		# construct bookmark sidebar (bookmark list, add and delete button)
		self.list_locations = QtGui.QListWidget()
		for name,location in self.bookmarks.listLocations():
			item = QtGui.QListWidgetItem()
			item.setText(name)
			item.setToolTip(u"{0:9.4f}, {1:9.4f}".format(*location))
			self.list_locations.addItem(item)
		
		self.button_add = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Add..."))
		self.button_add.setEnabled(False)
		self.button_add.setDisabled(True)
		
		self.button_del = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Delete"))
		self.button_del.setEnabled(False)
		self.button_del.setDisabled(True)
		
		layout_locbut = QtGui.QHBoxLayout()
		layout_locbut.addWidget(self.button_add)
		layout_locbut.addWidget(self.button_del)
		
		# construct controls for coordinates: lat/lon spinboxes, goto button
		button_goto = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Go to"))
		button_goto.setSizePolicy(QtGui.QSizePolicy.Preferred,QtGui.QSizePolicy.Preferred)
		self.spin_latitude = QtGui.QDoubleSpinBox()
		self.spin_latitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spin_latitude.setRange(-84.99999999,85)
		self.spin_latitude.setDecimals(8)
		self.spin_latitude.setSuffix(u" °")
		self.spin_latitude.setSingleStep(1)
		self.spin_latitude.setWrapping(True)
		
		self.spin_longitude = QtGui.QDoubleSpinBox()
		self.spin_longitude.setSizePolicy(QtGui.QSizePolicy.MinimumExpanding,QtGui.QSizePolicy.Fixed)
		self.spin_longitude.setRange(-179.99999999,180)
		self.spin_longitude.setDecimals(8)
		self.spin_longitude.setSuffix(u" °")
		self.spin_longitude.setSingleStep(1)
		self.spin_longitude.setWrapping(True)
		
		layout_latlon = QtGui.QFormLayout()
		layout_latlon.addRow(
			QtGui.QLabel(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Latitude:")),
			self.spin_latitude
		)
		layout_latlon.addRow(
			QtGui.QLabel(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Longitude:")),
			self.spin_longitude
		)
		
		# arrange widgets for sidebar and coordinates control
		layout_coord = QtGui.QHBoxLayout()
		layout_coord.addLayout(layout_latlon)
		layout_coord.addWidget(button_goto)
		layout_coord.setAlignment(QtCore.Qt.AlignTop)
		
		layout_locations = QtGui.QVBoxLayout()
		layout_locations.addWidget(self.list_locations)
		layout_locations.addLayout(layout_locbut)
		layout_locations.addLayout(layout_coord)
		
		locations = QtGui.QWidget()
		locations.setLayout(layout_locations)
		
		# create standard dialog buttons (ok/cancel)
		button_ok = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"OK"))
		button_cancel = QtGui.QPushButton(QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Cancel"))
		
		layout_buttons = QtGui.QHBoxLayout()
		layout_buttons.addStretch(1)
		layout_buttons.addWidget(button_ok)
		layout_buttons.addWidget(button_cancel)
		
		# integrate sidebar, controls, webpage and buttons into a central splitter
		layout_webview = QtGui.QVBoxLayout()
		layout_webview.addWidget(self.webview)
		layout_webview.addLayout(layout_buttons)
		
		webview = QtGui.QWidget()
		webview.setLayout(layout_webview)
		
		splitter = QtGui.QSplitter()
		splitter.setOrientation(QtCore.Qt.Horizontal)
		splitter.addWidget(locations)
		splitter.addWidget(webview)
		
		layout_central = QtGui.QVBoxLayout()
		layout_central.addWidget(self.progressbar)
		layout_central.addWidget(splitter)
		
		# wiring: connect widgets to methods
		self.connect(
			self.webview.page().mainFrame(),
			QtCore.SIGNAL('javaScriptWindowObjectCleared()'),
             		self.populateJavaScriptWindowObject
             	)
		self.connect(
			self.webview,
			QtCore.SIGNAL('loadStarted()'),
			self.webViewLoadStarted
		)
		self.connect(
			self.webview,
			QtCore.SIGNAL('loadProgress(int)'),
			self.webViewLoadProgress
		)
		self.connect(
			self.webview,
			QtCore.SIGNAL('loadFinished(bool)'),
			self.webViewLoadFinished
		)
		self.connect(
			button_ok,
			QtCore.SIGNAL('clicked()'),
			self.accept
		)
		self.connect(
			button_cancel,
			QtCore.SIGNAL('clicked()'),
			self.reject
		)
		self.connect(
			self,
			QtCore.SIGNAL('finished(int)'),
			self.writeLocationsToFile
		)
		self.connect(
			self.button_add,
			QtCore.SIGNAL('clicked()'),
			self.addLocation
		)
		self.connect(
			self.button_del,
			QtCore.SIGNAL('clicked()'),
			self.deleteLocation
		)
		self.connect(
			self.list_locations,
			QtCore.SIGNAL('itemSelectionChanged()'),
			self.selectionChanged
		)
		self.connect(
			self.list_locations,
			QtCore.SIGNAL('itemDoubleClicked(QListWidgetItem*)'),
			self.loadLocation
		)
		self.connect(
			self.spin_latitude,
			QtCore.SIGNAL('valueChanged(double)'),
			self.setMarkerAndGoTo
		)
		self.connect(
			self.spin_longitude,
			QtCore.SIGNAL('valueChanged(double)'),
			self.setMarkerAndGoTo
		)
		self.connect(
			button_goto,
			QtCore.SIGNAL('clicked()'),
			self.setMarkerAndGoTo
		)
		
		# start dialog by setting central layout and loading custom OSM page
		self.setLayout(layout_central)
		self.webview.load(QtCore.QUrl(os.path.join(sys.path[0],u"FotoPreProcessorOSM.html")))
		self.webview.show()
	
	
	def webViewLoadStarted(self):
		"""Reset and show progressbar. Called by webview's "loadStarted()" signal."""
		self.progressbar.reset()
		self.progressbar.show()
	
	
	def webViewLoadProgress(self,progress):
		"""Update progressbar value. Called by webview's "loadProgress(int)" signal."""
		self.progressbar.setValue(progress)
	
	
	def webViewLoadFinished(self,ok):
		"""Reset and hide progressbar. Called by webview's "loadFinished(bool)" signal."""
		self.progressbar.reset()
		self.progressbar.hide()
		self.setMarkerAndGoTo()	# after creating dialog and setting location,
					# page might still be loading and thus not
					# receiving the setMarker command; therefore
					# it is repeated after loading has finished;
					# thanks to try-except this does no harm
		# catch ok=False? (i.e. page not properly loaded)
	
	
	def setLocation(self,latitude=None,longitude=None,elevation=None):
		"""Set location to given coordinates.
		
Expects decimal degrees as integers or floats.

If any of the coordinates equals None, location information will be erased.
Elevation is currently not supported by OpenStreetMap, therefore it is ignored."""
		try:
			lat = float(latitude)
			lon = float(longitude)
			self.spin_latitude.setValue(lat)
			self.spin_longitude.setValue(lon)
			self.setMarkerAndGoTo()
		except:
			pass
	
	
	def location(self):
		"""Return currently set location tuple (latitude,longitude,elevation).
Might be empty."""
		try:    location = (self.spin_latitude.value(),self.spin_longitude.value(),0.0)
		except: location = tuple(None,None,None)
		return location
	
	
	def addLocation(self):
		"""Add a location bookmark for currently set location.

This opens a dialog to let the user either choose or type in a new name."""
		latitude  = self.spin_latitude.value()
		longitude = self.spin_longitude.value()
		lst_names = []
		for i in xrange(0,self.list_locations.count()):
			lst_names.append(self.list_locations.item(i).text())
		
		(name,ok) = QtGui.QInputDialog.getItem(self,
			QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Add new Named Location"),
			QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Please provide a name for currently set location:"),
			lst_names,0,True
		)
		if ok:
			if name in lst_names:
				answer = QtGui.QMessageBox.question(
					self,
					QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"Overwriting Existing Name"),
					QtCore.QCoreApplication.translate(u"GeoLookUpDialog",u"A location with that name exists. Shall it be overwritten?"),
					QtGui.QMessageBox.Yes | QtGui.QMessageBox.No
				)
				if answer == QtGui.QMessageBox.Yes:
					items = self.list_locations.findItems(name,QtCore.Qt.MatchExactly)
					items[0].setText(name)
					items[0].setToolTip(u"{0}, {1}".format(latitude,longitude))
					self.bookmarks.writeLocation(name,latitude,longitude)
			else:
				item = QtGui.QListWidgetItem()
				item.setText(name)
				item.setToolTip(u"{0}, {1}".format(latitude,longitude))
				self.list_locations.addItem(item)
				self.bookmarks.writeLocation(name,latitude,longitude)
	
	
	def deleteLocation(self):
		"""Delete all currently selected location bookmarks."""
		for item in self.list_locations.selectedItems():
			self.list_locations.takeItem(self.list_locations.row(item))
	
	
	def selectionChanged(self):
		"""Handle delete button state depending on number of selected items.

Called by itemSelectionChanged() of the bookmark list widget.

If the number of selected items equals zero, nothing can be deleted and thus the
delete button is disabled. Otherwise it is enabled."""
		self.button_del.setEnabled(len(self.list_locations.selectedItems()) != 0)
	
	
	def populateJavaScriptWindowObject(self):
		"""Establish connection between Javascript of FotoPreProcessorOSM.html and lat/lon spinboxes."""
		self.webview.page().mainFrame().addToJavaScriptWindowObject(
			u"spin_latitude",
			self.spin_latitude
		)
		self.webview.page().mainFrame().addToJavaScriptWindowObject(
			u"spin_longitude",
			self.spin_longitude
		)
	
	
	def goToCoordinates(self,latitude,longitude):
		"""Call FotoPreProcessorOSM.html Javascript to center map on given coordinates."""
		try:
			self.webview.page().mainFrame().evaluateJavaScript(
				u"centerOnLatLon({0},{1},null);".format(
					float(latitude),
					float(longitude)
				)
			)
		except:
			pass
	
	
	def setMarkerAndGoTo(self):
		"""Call FotoPreProcessorOSM.html Javascript to center map on given coordinates and set a marker."""
		try:    latitude  = float(self.spin_latitude.value())
		except: latitude  = None
		try:    longitude = float(self.spin_longitude.value())
		except: longitude = None
		if latitude != None and longitude != None:
			self.button_add.setEnabled(True)
			self.button_add.setDisabled(False)
			self.webview.page().mainFrame().evaluateJavaScript(
				u"setMarker({0},{1});".format(
					latitude,
					longitude
				)
			)
			for i in xrange(0,self.list_locations.count()):
				tooltip = self.list_locations.item(i).toolTip().split(u", ")
				if latitude == float(tooltip[0]) and longitude == float(tooltip[1]):
					self.list_locations.setCurrentRow(i)
					break
	
	
	def loadLocation(self,item):
		"""Load location specified by given QListWidgetItem.

Called by the bookmark list's signal itemDoubleClicked(QListWidgetItem*).

Expects the item's tooltip to contain coordinates seperated by ", ".

Sets latitude and longitude and places a marker."""
		str_tooltip = item.toolTip().split(u", ")
		try:
			self.spin_latitude.setValue(float(str_tooltip[0]))
			self.spin_longitude.setValue(float(str_tooltip[1]))
			self.setMarkerAndGoTo()
		except:
			pass
	
	
	def writeLocationsToFile(self,result):
		"""Save locations to the file "FotoPreProcessor.locations"."""
		self.bookmarks.saveFile()



class FPPStringDB:
	"""Class for the management of simple text database files.

Strings are stored in plain-text UTF-8 encoded files,
with each string on a separate line."""
	
	def __init__(self):
		"""Constructor; initialise fields."""
		self.set_database = set()
		self.str_filename = unicode()
		self.bool_changed = False
	
	
	def loadFile(self,filename=None):
		"""Load and process given file and populate the internal string database."""
		if filename != None:
			self.set_database.clear()
			filename = unicode(filename)
			try:
				with codecs.open(filename,u"r",u"utf-8") as f:
					for line in f:
						self.set_database.add(unicode(line.strip()))
			except:
				pass
			self.str_filename = filename
			self.bool_changed = False
	
	
	def strings(self):
		"""Return all strings currently stored, as a tuple."""
		return tuple(self.set_database)
	
	
	def add(self,string=unicode()):
		"""Add a string to the database. If the string already exists, nothing is changed."""
		try:
			l_old = len(self.set_database)
			self.set_database.add(unicode(string))
			if l_old != len(self.set_database):
				self.bool_changed = True
		except:
			pass
	
	
	def delete(self,string=unicode()):
		"""Delete a string from the database. Does nothing if the string doesn't exist."""
		try:
			self.set_database.remove(unicode(string))
		except:
			pass
	
	
	def saveFile(self,filename=None,force=False):
		"""Save current bookmark database in a file with given name.

If no filename is given, fall back to name of last file loaded.

File will only be altered if database was changed since last file loading.
This behaviour can be overridden by setting force=True."""
		if filename == None and len(self.str_filename) > 0:
			filename = self.str_filename
		try:
			if self.bool_changed or bool(force):
				lst_database = list(self.set_database)
				lst_database.sort()
				with codecs.open(filename,u"w",u"utf-8") as f:
					for string in lst_database:
						f.write(u"{0}\n".format(string))
		except:
			pass


