#!/usr/bin/env python2
# -*- coding: utf-8 -*-
"""
FotoPreProcessorItem: a custom QListWidgetItem
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

import datetime,pytz

from PyQt4 import QtGui, QtCore

class FPPGalleryItemDelegate(QtGui.QItemDelegate):
	"""Class for a custom drawn list item.

Depending on the (boolean) UserRole a custom marker can be placed over an
icons pixmap. This is actually used in the GUI to mark an item as "edited"."""
	
	def __init__(self,icon=None):
		QtGui.QItemDelegate.__init__(self)
		try:    self.icon_changed = QtGui.QIcon(icon)
		except: self.icon_changed = QtGui.QIcon()
	
	
	def paint(self,painter,option,index):
#		QtGui.QItemDelegate.paint(self,painter,option,index)
		
		painter.save()
		
		if option.state & QtGui.QStyle.State_Selected:
			painter.fillRect(option.rect,option.palette.highlight())
		
		painter.setRenderHint(QtGui.QPainter.Antialiasing, True)
		painter.setBackgroundMode(QtCore.Qt.TransparentMode)
		
		x = option.rect.x()
		y = option.rect.y()
		w = option.rect.width()
		h = option.rect.height()
		
		w_icon = option.decorationSize.width()
		h_icon = option.decorationSize.height()
		icon = QtGui.QIcon(index.data(QtCore.Qt.DecorationRole)).pixmap(w_icon,h_icon)
		w_thumb = icon.width()
		h_thumb = icon.height()
		
		rect_thumb = QtCore.QRect(x, y, w_thumb, h_thumb)
		
		painter.drawPixmap(
			x + (w-w_thumb)/2,
			y + (h-h_thumb)/2,
			QtGui.QPixmap(icon)
		)
		
		if bool(index.data(QtCore.Qt.UserRole).toBool()):
			marker = self.icon_changed.pixmap(w_icon,h_icon)
			w_marker = marker.width()
			h_marker = marker.height()
			painter.drawPixmap(
				x + (w-w_marker)/2,
				y + (h-h_marker)/2,
				marker
			)
		
		painter.restore()


class FPPGalleryItem(QtGui.QListWidgetItem):
	"""Class for a custom QListWidgetItem.

The item is enhanced by properties for timestamp, GPS timestamp,
camera settings, camera hardware, orientation, timeshift based on from/to
timezones, location (latitude, longitude, elevation) and a set of keywords.

Appropriate methods for handling and showing these properties are defined, too."""
	
	MapStringToOrientation = {
		u"Standard (normal)": 1,
		u"Mirror horizontal": 2,
		u"Rotate 180": 3,
		u"Mirror vertical": 4,
		u"Mirror horizontal and rotate 270 CW": 5,
		u"Rotate 90 CW": 6,
		u"Mirro horizontal and rotate 90 CW": 7,
		u"Rotate 270 CW": 8,
	}
	
	SortByName   = 0
	SortByTime   = 1
	SortByCamera = 2
	
	def __init__(self,parent=None):
		"""Constructor; initialise fields."""
		QtGui.QListWidgetItem.__init__(self,parent,1001)
		self.pix_thumb = QtGui.QPixmap(1,1)
		
		self.str_filename = unicode()
		self.date_timestamp = None
		self.str_cameraSettings = unicode()
		self.str_cameraHardware = unicode()
		self.str_copyright = unicode()
		
		self.int_orientation = 1
		self.tpl_timezones = (u"UTC",u"UTC")
		self.tpl_location = tuple()
		self.tpl_keywords = tuple()
		
		self.int_saved_orientation = 1
		self.tpl_saved_timezones = (u"UTC",u"UTC")
		self.tpl_saved_location = tuple()
		self.tpl_saved_keywords = tuple()
		self.str_saved_copyright = unicode()
		
		self.int_timeshift = 0
		self.date_shiftedTimestamp = None
		self.date_utcTimestamp = None
		
		self.bool_edited = False
		self.bool_editedOrientation = False
		self.bool_editedLocation = False
		self.bool_editedTimezones = False
		self.bool_editedKeywords = False
		self.bool_editedCopyright = False
		
		self.int_width = -1
		self.int_height = -1
		
		self.int_sortCriterion = self.SortByName
	
	
	def __lt__(self,otherItem=None):
		try:
			resultName = self.str_filename < otherItem.str_filename
			resultTime = self.date_timestamp < otherItem.date_timestamp
			resultCam  = self.str_cameraHardware < otherItem.str_cameraHardware
			return self.comparisonHelper(otherItem,resultName,resultTime,resultCam)
		except:
			return False
	
	
	def __gt__(self,otherItem=None):
		try:
			resultName = self.str_filename > otherItem.str_filename
			resultTime = self.date_timestamp > otherItem.date_timestamp
			resultCam  = self.str_cameraHardware > otherItem.str_cameraHardware
			return self.comparisonHelper(otherItem,resultName,resultTime,resultCam)
		except:
			return False
	
	
	def __eq__(self,otherItem=None):
		result = False
		try:
			if self.int_sortCriterion == self.SortByName:
				result = self.str_filename == otherItem.str_filename
			elif self.int_sortCriterion == self.SortByTime:
				result = self.date_timestamp == otherItem.date_timestamp
			elif self.int_sortCriterion == self.SortByCamera:
				result = self.str_cameraHardware == otherItem.str_cameraHardware
		except:
			pass
		return result
	
	
	def __ne__(self,otherItem=None):
		result = False
		try:
			if self.int_sortCriterion == self.SortByName:
				result = self.str_filename != otherItem.str_filename
			elif self.int_sortCriterion == self.SortByTime:
				result = self.date_timestamp != otherItem.date_timestamp
			elif self.int_sortCriterion == self.SortByCamera:
				result = self.str_cameraHardware != otherItem.str_cameraHardware
		except:
			pass
		return result
	
	
	def comparisonHelper(self,otherItem=None,resultName=False,resultTime=False,resultCam=False):
		result = False
		try:
			if self.int_sortCriterion == self.SortByName:
				# --- sort by name ---
				result = resultName # name should be pretty unique...
			
			elif self.int_sortCriterion == self.SortByCamera:
				# --- sort by camera ---
				if self.str_cameraHardware == otherItem.str_cameraHardware:
					# items created with same camera: sort by timestamp
					if self.date_timestamp == otherItem.date_timestamp:
						# same timestamp: possible (image series), sort by name
						result = resultName
					else:
						result = resultTime
				else:
					result = resultCam
			
			elif self.int_sortCriterion == self.SortByTime:
				# --- sort by time ---
				if self.date_timestamp == otherItem.date_timestamp:
					# same timestamp: possible (image series), sort by name
					result = resultName
				else:
					result = resultTime
		except:
			pass
		return result
	
	
	def setSortCriterion(self,value=SortByName):
		if value == self.SortByCamera or value == self.SortByTime or value == self.SortByName:
			self.int_sortCriterion = value
	
	
	def setSize(self,width,height):
		try:
			self.int_width = int(width)
			self.int_height = int(height)
		except:
			self.int_width = -1
			self.int_height = -1
	
	
	def size(self):
		return (self.int_width,self.int_height)
	
	
	def updateEditState(self):
		"""Update "edited" state of the item (updates fields and UserRole).

Compare orientation, timeshift, location, keywords to previously saved values."""
		self.bool_editedOrientation = (self.int_orientation != self.int_saved_orientation)
		self.bool_editedTimezones = (self.tpl_timezones != self.tpl_saved_timezones)
		self.bool_editedLocation = (self.tpl_location != self.tpl_saved_location)
		self.bool_editedKeywords = (self.tpl_keywords != self.tpl_saved_keywords)
		self.bool_editedCopyright = (self.str_copyright != self.str_saved_copyright)
		self.bool_edited = (self.bool_editedOrientation or \
			self.bool_editedLocation or self.bool_editedTimezones or \
			self.bool_editedKeywords or self.bool_editedCopyright)
		self.setData(QtCore.Qt.UserRole,self.bool_edited)
	
	
	def edited(self):
		"""Return True if item was edited.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_edited
	
	
	def orientationEdited(self):
		"""Return True if the item's orientation was changed.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_editedOrientation
	
	
	def timezonesEdited(self):
		"""Return True if the item's timezone correction was changed.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_editedTimezones
	
	
	def locationEdited(self):
		"""Return True if the item's location was changed.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_editedLocation
	
	
	def keywordsEdited(self):
		"""Return True if the item's keyword set was changed.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_editedKeywords
	
	
	def copyrightEdited(self):
		"""Return True if the item's copyright string was changed.

Note: This is based on a variable which gets updated by updateEditState()."""
		return self.bool_editedCopyright
	
	
	def setFilename(self,filename=None):
		"""Set filename property."""
		if filename != None:
			try:
				self.str_filename = unicode(filename)
				self.setText(str_filename)
				self.updateToolTip()
			except:
				pass
		return self.str_filename
	
	
	def filename(self):
		"""Return the item's filename as a unicode string. Might be an empty string."""
		return self.str_filename
	
	
	def setThumbnail(self,pixmap=None):
		"""Set thumbnail image. Expects a QPixmap."""
		try:
			self.pix_thumb = QtGui.QPixmap(pixmap)
			self.updateIcon()
		except:
			pass
	
	
	def thumbnail(self):
		"""Return thumbnail image as a QPixmap."""
		return self.pix_thumb
	
	
	def setTimezones(self,fromTimezone=None,toTimezone=None):
		"""If called with values: set timezone correction.

Expects valid timezone names as strings, e.g. "Europe/Berlin" or "UTC".
If invalid timezone names are provided, nothing is changed."""
		if fromTimezone != None and toTimezone != None:
			try:
				fromTz = pytz.timezone(unicode(fromTimezone))
				toTz = pytz.timezone(unicode(toTimezone))
				t_from = fromTz.localize(self.date_timestamp).strftime(u"%z")
				t_to = toTz.localize(self.date_timestamp).strftime(u"%z")
				m_from = 60*int(t_from[0:3]) + int(t_from[3:5])
				m_to   = 60*int(t_to[0:3])   + int(t_to[3:5])
				self.tpl_timezones = (unicode(fromTimezone),unicode(toTimezone))
				self.int_timeshift = m_to - m_from
			except:
				pass
			self.updateShiftedTimestamps()
			self.updateEditState()
			self.updateToolTip()
	
	
	def timeshift(self):
		"""Return timezone correction as integer timeshift in minutes."""
		return self.int_timeshift
	
	
	def timezones(self):
		"""Return timezone correction as a tuple (fromTz,toTz) of unicode strings."""
		return self.tpl_timezones
	
	
	def updateShiftedTimestamps(self):
		"""Update shifted timestamp value.

Timezone correction as set by setTimezones(fromTz,toTz) is applied to the
original timestamp and the result is stored internally for display purposes."""
		try:
			fromTz = pytz.timezone(self.tpl_timezones[0])
			toTz = pytz.timezone(self.tpl_timezones[1])
			t_from = fromTz.localize(self.date_timestamp)
			self.date_shiftedTimestamp = toTz.normalize(t_from.astimezone(toTz))
			self.date_utcTimestamp = t_from.astimezone(pytz.utc)
		except:
			self.date_shiftedTimestamp = self.date_timestamp
		self.updateEditState
	
	
	def setTimestamp(self,tpl_timestamp=tuple()):
		"""Set the item's timestamp.

Expects a tuple (year,month,day,hour,minute,second) of integers."""
		try:
			self.date_timestamp = datetime.datetime(
				int(tpl_timestamp[0]),
				int(tpl_timestamp[1]),
				int(tpl_timestamp[2]),
				int(tpl_timestamp[3]),
				int(tpl_timestamp[4]),
				int(tpl_timestamp[5])
			)
			self.updateShiftedTimestamps()
			self.updateToolTip()
		except:
			pass
	
	
	def timestamp(self):
		"""Return the item's timestamp. Might be None."""
		return self.date_timestamp
	
	
	def shiftedTimestamp(self):
		return self.date_shiftedTimestamp
	
	
	def utcTimestamp(self):
		"""Return the item's GPS timestamp. Might be None."""
		return self.date_utcTimestamp
	
	
	def setOrientation(self,value=None):
		"""Set orientation of the item's thumbnail image.

An integer as well as a string is accepted:
   1 <---> "Horizontal (normal)"
   2 <---> "Mirror horizontal"
   3 <---> "Rotate 180"
   4 <---> "Mirror vertical"
   5 <---> "Mirror horizontal and rotate 270 CW"
   6 <---> "Rotate 90 CW"
   7 <---> "Mirror horizontal and rotate 90 CW"
   8 <---> "Rotate 270 CW"

Horizontal (normal) orientation (=1) is set a default."""
		try:
			self.int_orientation = self.MapStringToOrientation[unicode(value)]
			self.updateIcon()
			self.updateEditState()
			self.updateToolTip()
		except:
			try:
				self.int_orientation = max(min(int(value),8),1)
				self.updateIcon()
				self.updateEditState()
				self.updateToolTip()
			except:
				pass
		
	def orientation(self):
		"""Return the item's orientation value as an integer. Equals 1 by default."""
		return self.int_orientation
	
		
	def rotateLeft(self):
		"""Set orientation value to a new value, rotated counter-clockwise.

Rotation cylce: 1 -> 8 -> 3 -> 6 -> 1"""
		if self.int_orientation == 1:   # normal -> 270 CW
			self.int_orientation = 8
		elif self.int_orientation == 3: # 180 -> 90 CW
			self.int_orientation = 6
		elif self.int_orientation == 6: # 90 CW -> normal
			self.int_orientation = 1
		elif self.int_orientation == 8: # 270 CW -> 180
			self.int_orientation = 3
		self.updateIcon()
		self.updateEditState()
		self.updateToolTip()
	
	
	def rotateNormal(self):
		"""Set orientation value to normal orientation (=1)."""
		self.int_orientation = 1
		self.updateIcon()
		self.updateEditState()
		self.updateToolTip()
	
	
	def rotateRight(self):
		"""Set orientation value to a new value, rotated clockwise.

Rotation cylce: 1 -> 6 -> 3 -> 8 -> 1"""
		if self.int_orientation == 1:   # normal -> 90 CW
			self.int_orientation = 6
		elif self.int_orientation == 3: # 180 -> 270 CW
			self.int_orientation = 8
		elif self.int_orientation == 6: # 90 CW -> 180
			self.int_orientation = 3
		elif self.int_orientation == 8: # 270 CW -> normal
			self.int_orientation = 1
		self.updateIcon()
		self.updateEditState()
		self.updateToolTip()
	
	
	def addKeyword(self,keyword=unicode()):
		try:
			keywords = list(self.tpl_keywords)
			keywords.append(unicode(keyword))
			self.tpl_keywords = tuple(keywords)
			self.updateEditState()
			self.updateToolTip()
		except:
			pass
	
	
	def removeKeyword(self,keyword=unicode()):
		try:
			keywords = list(self.tpl_keywords)
			keywords.remove(unicode(keyword))
			self.tpl_keywords = tuple(keywords)
			self.updateEditState()
			self.updateToolTip()
		except:
			pass
	
	
	def setKeywords(self,keywords=tuple()):
		"""Define a new keyword tuple for this item.

The parameter keywords is expected to be a set, list or tuple of strings
whicht will be converted to a tuple of unicode strings."""
		try:
			self.tpl_keywords = tuple([unicode(i) for i in keywords])
			self.updateEditState()
			self.updateToolTip()
		except:
			pass
	
	
	def keywords(self):
		"""Return the item's keyword tuple (a tuple of unicode strings). Might be empty."""
		return self.tpl_keywords
	
	
	def setCameraSettings(self,settings=unicode()):
		"""Set camera settings string. Expects a unicode string.

Recommended settings: focal length, aperture, shutter speed and ISO level, e.g.:

    "35 mm, f/5.6, 1/250 s, ISO 100" """
		if settings != None:
			try:
				self.str_cameraSettings = unicode(settings)
				self.updateToolTip()
			except:
				pass
	
	def cameraSettings(self):
		"""Return the item's camera settings unicode string. Might be empty."""
		return self.str_cameraSettings
	
	
	def setCameraHardware(self,hardware=unicode()):
		"""Set camera hardware string. Expects a unicode string.

Hardware: Camera model and/or lens type, e.g.:

    "Canon EOS 450D, Canon EF-S 15-85mm f/3.5-5.6 IS USM" """
		if hardware != None:
			try:
				self.str_cameraHardware = unicode(hardware)
				self.updateToolTip()
			except:
				pass
	
	def cameraHardware(self):
		"""Return the item's camera hardware unicode string. Might be empty."""
		return self.str_cameraHardware
	
	
	def setCopyright(self,notice=unicode()):
		"""Set copyright string. Expects a unicode string."""
		if notice != None:
			try:
				self.str_copyright = unicode(notice)
				self.updateEditState()
				self.updateToolTip()
			except:
				pass
	
	def copyright(self):
		"""Return the item's copyright unicode string. Might be empty."""
		return self.str_copyright
	
	
	def setLocation(self,latitude=None,longitude=None,elevation=None):
		"""Set location of item to given coordinates.
		
Expects decimal degrees as integers or floats:

latitude >= 0:  northward           latitude < 0:   southward
longitude >= 0: eastward            longitude < 0:  westward
altitude >= 0:  above sea level     altitude < 0: below sea level

If any of the coordinates equals None, location information will be erased."""
		try:
			self.tpl_location = (float(latitude),float(longitude),float(elevation))
		except:
			self.tpl_location = tuple()
		self.updateEditState()
		self.updateToolTip()
	
	
	def location(self):
		"""Return location of item as a tuple of floats (latitude,longitude,elevation)."""
		return self.tpl_location
		
		#-----------------------------------------------------------------------
		# read or set location tuple("x.xxxx...","x.xxx...")
		# GPS tags:
		#   GPSLatitude     = x.xxxxxxx
		#   GPSLatitudeRef  = ("N","S")
		#   GPSLongitude    = x.xxxxxxx
		#   GPSLongitudeRef = ("E","W")
		#   GPSAltitude     = 0
		#   GPSAltitudeRef  = 0 # above sea level, 1 = below...
		#   GPSTimeStamp/GPSDateStamp = UTC time of image
		#
		# OpenStreetMap: lat  >= 0 -> latRef = N
		#                lat  < 0  -> latRef = S
		#                long >= 0 -> longRef = E
		#                long < 0  -> longRef = W
		#
		# loc = tuple("x.xxxx","y.yyyy")
		#
		#-----------------------------------------------------------------------
	
	
	def updateIcon(self):
		"""Apply currently set orientation to stored thumbnail image
in order to create a new item icon."""
		iconsize = self.listWidget().iconSize()
		matrix = QtGui.QTransform()
		if self.int_orientation == 2:
			matrix.scale(-1,1)
		elif self.int_orientation == 3:
			matrix.rotate(180)
		elif self.int_orientation == 4:
			matrix.scale(1,-1)
		elif self.int_orientation == 5:
			matrix.scale(-1,1)
			matrix.rotate(270)
		elif self.int_orientation == 6:
			matrix.rotate(90)
		elif self.int_orientation == 7:
			matrix.scale(1,-1)
			matrix.rotate(90)
		elif self.int_orientation == 8:
			matrix.rotate(270)
		thumb = self.pix_thumb.transformed(
				matrix,
				QtCore.Qt.SmoothTransformation
			).scaled(
				iconsize,
				QtCore.Qt.KeepAspectRatio,
				QtCore.Qt.SmoothTransformation
			)
		self.setIcon(QtGui.QIcon(thumb))
		self.setSizeHint(iconsize+QtCore.QSize(8,8))
	
	
	def updateToolTip(self):
		"""Update the item's tooltip."""
		str_tooltip = u"<h4>{0}</h4>".format(self.str_filename)
		
		if self.date_timestamp != None:
			if self.bool_editedTimezones:
				str_tooltip += u"<p><font color=\"blue\">{0}</font> ({1} UTC)</p>".format(
					self.date_shiftedTimestamp.strftime(u"%Y-%m-%d %H:%M:%S"),
					self.date_utcTimestamp.strftime(u"%Y-%m-%d %H:%M:%S"),
				)
			else:
				str_tooltip += u"<p>{0}</p>".format(self.date_timestamp.strftime(u"%Y-%m-%d %H:%M:%S"))
		
		if len(self.str_cameraSettings) != 0:
			str_tooltip += u"<p>{0}</p>".format(self.str_cameraSettings)
		if len(self.str_cameraHardware) != 0:
			str_tooltip += u"<p>{0}</p>".format(self.str_cameraHardware)
		
		if len(self.tpl_keywords) > 0:
			if self.bool_editedKeywords:
				str_tooltip += u"<p><font color=\"blue\">{0}</font></p>".format(u", ".join(self.tpl_keywords))
			else:
				str_tooltip += u"<p>{0}</p>".format(", ".join(self.tpl_keywords))
		
		if len(self.tpl_location) == 3:
			if self.bool_editedLocation:
				str_tooltip += u"<p><font color=\"blue\">"
			else:
				str_tooltip += u"<p>"
			str_tooltip += u"{0:+.3f}, {1:+.3f}, {2:+.0f} m {3}".format(
					self.tpl_location[0],
					self.tpl_location[1],
					self.tpl_location[2],
					QtCore.QCoreApplication.translate(u"ItemToolTip",u"Elevation")
			)
			if self.bool_editedLocation:
				if len(self.tpl_saved_location) == 3:
					str_tooltip += u"</font> ({0:+.3f}, {1:+.3f}, {2:+.0f} m {3})".format(
						self.tpl_saved_location[0],
						self.tpl_saved_location[1],
						self.tpl_saved_location[2],
						QtCore.QCoreApplication.translate(u"ItemToolTip",u"Elevation")
					)
			str_tooltip += u"</p>"
		
		if len(self.str_copyright) > 0:
			if self.bool_editedCopyright:
				str_tooltip += u"<p><font color=\"blue\">&#169; {0}</font></p>".format(self.str_copyright)
			else:
				str_tooltip += u"<p>&#169; {0}</p>".format(self.str_copyright)
		
		self.setToolTip(str_tooltip)
	
	
	def saveState(self):
		"""Back-up the item's state."""
		self.int_saved_orientation = self.int_orientation
		self.tpl_saved_keywords = self.tpl_keywords
		self.tpl_saved_location = self.tpl_location
		self.tpl_saved_timezones = self.tpl_timezones
		self.str_saved_copyright = self.str_copyright
		self.updateEditState()
		self.updateToolTip()
	
	
	def resetOrientation(self):
		"""Return to previously saved orientation."""
		self.setOrientation(self.int_saved_orientation)
	
	
	def resetTimezones(self):
		"""Return to previously saved timezone correction."""
		self.setTimezones(*self.tpl_saved_timezones)
	
	
	def resetKeywords(self):
		"""Return to previously saved keyword set."""
		self.setKeywords(self.tpl_saved_keywords)
	
	
	def resetLocation(self):
		"""Return to previously saved location."""
		self.setLocation(*self.tpl_saved_location)
	
	
	def resetCopyright(self):
		"""Return to previously saved location."""
		self.setCopyright(self.str_saved_copyright)
	
	
	def resetAll(self):
		"""Reset all properties to previously saved values.

Convenience method to call all other reset* methods at once."""
		self.resetOrientation()
		self.resetTimezones()
		self.resetKeywords()
		self.resetLocation()
		self.resetCopyright()



