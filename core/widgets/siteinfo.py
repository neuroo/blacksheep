#!/usr/bin/env python
"""
	BlackSheep -- Penetration testing framework
	by Romain Gaucher <r@rgaucher.info> - http://rgaucher.info

	Copyright (c) 2008-2012 Romain Gaucher <r@rgaucher.info>

	Licensed under the Apache License, Version 2.0 (the "License");
	you may not use this file except in compliance with the License.
	You may obtain a copy of the License at

		http://www.apache.org/licenses/LICENSE-2.0

	Unless required by applicable law or agreed to in writing, software
	distributed under the License is distributed on an "AS IS" BASIS,
	WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
	See the License for the specific language governing permissions and
	limitations under the License.
"""
import sys, os, string, re

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

from core.widgets.component.graphicview import GraphView
from core.widgets.sitemap import probe_icon

from core.utils.fileutils import correctFileName

import core.management

COLUMN_KEYWORDS = [
	'filetype',
	'url'
]

FILTER_TOKENIZER = re.compile("(" + '|'.join(COLUMN_KEYWORDS) + "):([^\\s]+)", re.I)

FILTER_TOOLTIP = """Filter commands:
%s are the different directives used
to create a particular selection for the
types of nodes to display. The search works
as an exact match (case insensitive).

ex: filetype:html filetype:swf""" % ', '.join(COLUMN_KEYWORDS)


# Splitted the display to introduce a QSplitter
class InfoDisplay(QWidget):
	def __init__(self, appinfo, parent = None):
		QWidget.__init__(self, parent)
		self.appinfo = appinfo
		self.current_selection = None
		self.activedomain = None

		self.redraw_screen = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/map.png"), "Redraw AFG view", self)
		self.clear_screen = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/page_white.png"), "Clear AFG view", self)
		self.save_screen = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/image.png"), "Export AFG as an image", self)

		#self.apply_heuristic = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/wand.png"), "Apply selected heuristic", self)
		#self.apply_heuristic.setCheckable(True)
		#self.apply_heuristic.setChecked(False)

		self.toolBar = QToolBar()
		self.toolBar.setStyleSheet("QToolBar {margin:0;border:0;padding:0}")
		self.toolBar.addAction(self.redraw_screen)
		self.toolBar.addAction(self.clear_screen)
		self.toolBar.addAction(self.save_screen)
		#self.toolBar.addSeparator()
		#self.toolBar.addAction(self.apply_heuristic)

		self.filter = QLineEdit()
		self.filter.setToolTip(FILTER_TOOLTIP)

		self.dropDownDomain = QComboBox()
		self.dropDownDomain.addItem(QString("List of domains:"))

		self.tree = QTreeWidget()
		self.tree.setColumnCount(2)
		self.tree.setRootIsDecorated(False)
		self.tree.setAlternatingRowColors(True)
		self.tree.setSortingEnabled(False)
		self.tree.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.tree.setWordWrap(True)
		self.tree.setHeaderLabels(["Selected Node Information", "Value"])
		self.tree.setUniformRowHeights(True)
		self.tree.resizeColumnToContents(0)
		self.loadLabel = QLabel("Load Request:")
		self.availableRequestDropDown = QComboBox()
		self.availableRequestDropDown.addItem(QString("List of existing requests:"))

		bottomLayout = QHBoxLayout()
		bottomLayout.addWidget(self.loadLabel)
		bottomLayout.addWidget(self.availableRequestDropDown)

		rightLayout = QVBoxLayout()
		rightLayout.addWidget(self.toolBar)
		# rightLayout.addWidget(self.filter)
		rightLayout.addWidget(self.dropDownDomain)
		rightLayout.addWidget(self.tree)
		rightLayout.addLayout(bottomLayout)
		self.setLayout(rightLayout)


class SiteInfo(QWidget):
	def __init__(self, appinfo, parent = None):
		QWidget.__init__(self, parent)

		self.appinfo = appinfo
		self.current_selection = None
		width = self.width()
		self.domainIcon = QIcon(probe_icon(None, None, 'domain'))

		self.graphview = GraphView(self.appinfo)
		QObject.connect(self.graphview, SIGNAL('updateDetailsNodePan'), self.fillInformationPan_Slot)

		self.infodisplay = InfoDisplay(self.appinfo)
		QObject.connect(self.infodisplay.dropDownDomain, SIGNAL('currentIndexChanged(const QString&)'), self.selectedDomain_Slot)
		QObject.connect(self.infodisplay.availableRequestDropDown, SIGNAL('currentIndexChanged(const QString&)'), self.selectedRequestID_Slot)
		QObject.connect(self.infodisplay.save_screen, SIGNAL('triggered()'), self.saveGraphView_Slot)
		QObject.connect(self.infodisplay.clear_screen, SIGNAL('triggered()'), self.clearGraphView_Slot)
		QObject.connect(self.infodisplay.redraw_screen, SIGNAL('triggered()'), self.redrawGraphView_Slot)
		#QObject.connect(self.infodisplay.apply_heuristic, SIGNAL('toggled()'), self.graphview.executeHeuristic)
		QObject.connect(self.infodisplay.filter, SIGNAL('returnPressed()'), self.processFilter_Slot)

		self.splitter = QSplitter(parent)
		self.splitter.addWidget(self.graphview)
		self.splitter.addWidget(self.infodisplay)

		layout = QHBoxLayout()
		layout.addWidget(self.splitter)
		self.setLayout(layout)

	def newFindingForURL_Slot(self, qurlstr):
		self.appinfo.newFindingForURL(qurlstr)

	def processFilter_Slot(self):
		filter_value = unicode(self.infodisplay.filter.text())
		if 4 < len(filter_value):
			list_filters = FILTER_TOKENIZER.findall(filter_value)
			compiled_filter = {}
			for filter in list_filters:
				if filter[0] not in compiled_filter:
					compiled_filter[filter[0]] = [filter[1]]
				elif filter[1] not in compiled_filter[filter[0]]:
					compiled_filter[filter[0]].append(filter[1])
			self.graphview.setFilterTypes(compiled_filter)
		else:
			self.graphview.setFilterTypes(None)

	def renew(self):
		self.tree.clear()
		self.graphview.renew()

	#def resizeEvent(self, event):
	#	self.infodisplay.tree.setMaximumWidth(self.width() // 5)

	def appInfoAvailable_Slot(self, domain, qurlstr, request_id):
		node_info = None
		if request_id:
			node_info = self.appinfo.getInfoByRequestID(domain, request_id)[0]
		else:
			node_info = self.appinfo.getInfo(domain, qurlstr)

		self.graphview.process(domain, qurlstr, request_id, node_info)
		# add domain in QComboBox if doens't exist in there
		if 0 > self.infodisplay.dropDownDomain.findText(domain):
			self.infodisplay.dropDownDomain.addItem(self.domainIcon, domain)
			if not self.infodisplay.activedomain:
				self.infodisplay.activedomain = domain
				self.infodisplay.dropDownDomain.setCurrentIndex(self.infodisplay.dropDownDomain.findText(domain))

	# TODO: add support for multiple domains (or automatically merge the ones that have redirections)
	def selectedDomain_Slot(self, rts):
		if not rts.contains("List of domains:"):
			prev_domain = self.infodisplay.activedomain
			self.infodisplay.activedomain = rts
			self.graphview.setActiveDomain(self.infodisplay.activedomain)
			if prev_domain:
				self.graphview.changeDomain()

	def selectedRequestID_Slot(self, rts):
		if not rts.contains("List of existing requests:") and 0 < len(rts):
			rts = str(rts).replace("request - ", "").replace(" ", "")
			request_id = int(rts)
			if 0 < request_id:
				self.emit(SIGNAL("siteInfoLoadRequestIDInTamperData"), request_id)

	@staticmethod
	def __create_treeitem(name, value, icon=None):
		if not isinstance(name, QString):
			name = QString(name)
		if not isinstance(value, QString):
			value = QString(value)
		item = QTreeWidgetItem()
		item.setText(0, name)
		if icon:
			item.setIcon(0, icon)
		item.setText(1, value)
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		return item

	@staticmethod
	def __create_treeseparator(name):
		bgColor = QColor(0, 0, 255, 25)
		if not isinstance(name, QString):
			name = QString(name)
		item = QTreeWidgetItem()
		item.setText(0, name)
		item.setBackgroundColor(0, bgColor)
		item.setBackgroundColor(1, bgColor)
		return item

	def fillInformationPan_Slot(self, tpl):
		self.current_selection = tpl
		domain = tpl[0]
		qurlstr = tpl[1]
		info = self.appinfo.getInfo(domain, qurlstr)
		if not info:
			return
		# domain {
		#  url-string {
		#  'method' : []
		#  'request_id' : []
		#  'original' : True if user clicked on link or if link was directly requested
		#               False if it's a subsequent request
		#  'tampered' : True if user tampered this request once... will help to extract
		#               the coverage of pen-test
		#  'spidered' : True if spider discovered the link
		#  'content-type' : [image, xml, html, js, css, flash, binary, etc.]
		#  'get' : { '$PARAMETER_NAME$' :  []}
		#  'post' : { '$PARAMETER_NAME$' :  []}
		#  'headers' : { '$PARAMETER_NAME$' :  []}
		#  'cookies' : { '$PARAMETER_NAME$' :  [('value', 'raw')]}
		#  'fragment' : []
		# } }
		# load request ID to the drop down
		self.infodisplay.availableRequestDropDown.clear()
		self.infodisplay.availableRequestDropDown.addItem(QString("List of existing requests:"))
		for request_id in info['request_id']:
			self.infodisplay.availableRequestDropDown.addItem(QString("request - %d" % request_id))

		self.infodisplay.tree.setUpdatesEnabled(False)
		self.infodisplay.tree.clear()

		root = self.infodisplay.tree.invisibleRootItem()
		item = QTreeWidgetItem()
		item.setText(0, domain)
		item.setIcon(0, self.domainIcon)
		item.setIcon(0, QIcon(probe_icon(None, None, 'domain')))
		item.setText(1, QUrl(qurlstr).path())
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		root.addChild(item)
		root.addChild(SiteInfo.__create_treeitem("Nb Requests", str(len(info['request_id']))))
		root.addChild(SiteInfo.__create_treeitem("Clicked by user", "true" if info['original'] else "false"))
		root.addChild(SiteInfo.__create_treeitem("Tampered by user", "true" if info['tampered'] else "false"))
		root.addChild(SiteInfo.__create_treeitem("Spidered", "true" if info['spidered'] else "false"))
		root.addChild(SiteInfo.__create_treeitem("Content types", ", ".join(info['content-type'])))

		for item in ('headers', 'get', 'post', 'cookies'):
			category = SiteInfo.__create_treeseparator(string.capitalize(item))
			root.addChild(category)
			for variable in info[item]:
				values = [unicode(v) for v in info[item][variable]]
				category.addChild(SiteInfo.__create_treeitem(variable, ", ".join(values)))
		if 0 < len(info['fragment']):
			category = SiteInfo.__create_treeseparator("Fragments")
			root.addChild(category)
			values = [unicode(v) for v in info['fragment']]
			category.addChild(SiteInfo.__create_treeitem(", ".join(values), ""))

		self.infodisplay.tree.expandAll()
		self.infodisplay.tree.resizeColumnToContents(0)
		self.infodisplay.tree.setUpdatesEnabled(True)

	def redrawGraphView_Slot(self):
		self.graphview.changeDomain()

	def clearGraphView_Slot(self):
		self.graphview.scene.newScene()

	def saveGraphView_Slot(self):
		properFileName = correctFileName(unicode(self.infodisplay.activedomain))
		orgFileName = core.management.configuration['path']['user'] + 'bsheep_%s_AFG.png' % properFileName
		filename = QFileDialog.getSaveFileName(self, "Save file as...", orgFileName, "Image Format (*.png)")
		if not filename.isEmpty():
			painter = QPainter()
			img = QImage(self.graphview.size(), QImage.Format_ARGB32_Premultiplied)
			painter.begin(img)
			self.graphview.render(painter)
			painter.end()
			img.save(filename, "PNG")
