#!/usr/bin/env python
"""
	BlackSheep -- Penetration testing framework
	by Romain Gaucher <r@rgaucher.info> - http://rgaucher.info

	Copyright (c) 2008-2010 Romain Gaucher <r@rgaucher.info>

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
from PyQt4.QtCore import *
from PyQt4.QtGui import *

from core.utils.http_request import HTTPRequest
from core.widgets.component.widgetiterator import QTreeWidgetIterPy
from core.widgets.component.tampertreewidget import TamperTreeWidget

import core.network
import core.management


# Interception and tampering dialog
#
# TODOs:
#  - possibility to add any fields
#  - improve interface
#  - implement the transformations system (apply same transfo to subsequent requests)
#    a simple diff per element name should work for that... with few basic operations
#    such as string replace, string append, string remove
class HTTPTamperDialog(QDialog):
	def __init__(self, netmanager, op, qrequest, outgoingDataList = None, parent = None):
		QDialog.__init__(self, parent)

		# passed args saved for further update, etc.
		self.netmanager = netmanager
		self.op = op
		self.qrequest = qrequest
		self.outgoingDataList = outgoingDataList

		# storage of the HTTPRequest
		self.nrequest = None

		# QTree widget to represent the different editable information
		self.request = TamperTreeWidget()
		self.request.setRootIsDecorated(False)
		self.request.setAlternatingRowColors(True)
		self.request.setSortingEnabled(False)
		self.request.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.request.setHeaderLabels(['HTTP Header', 'value'])
		self.request.resizeColumnToContents(0)
		self.request.setWordWrap(True)
		QObject.connect(self.request, SIGNAL("itemChanged(QTreeWidgetItem *, int)"), self.requestChangedItemHeaders_Slot)
		QObject.connect(self.request, SIGNAL("addRowTreeWidget"), self.addRowTreeWidget_Slot)
		QObject.connect(self.request, SIGNAL("duplicateRowTreeWidget"), self.duplicateRowTreeWidget_Slot)
		QObject.connect(self.request, SIGNAL("deleteRowTreeWidget"), self.deleteRowTreeWidget_Slot)

		self.gbox = QGroupBox("&Header Tampering")
		self.continue_tampering = QCheckBox("&Continue Tampering")
		self.continue_tampering.setCheckState(Qt.Checked)
		self.apply_transformation = QCheckBox("&Apply These Transformations on Subsequent Requests")

		QObject.connect(self.continue_tampering, SIGNAL('stateChanged(int)'), self.stateChanged_ContinueTampering_Slot)
		QObject.connect(self.apply_transformation, SIGNAL('stateChanged(int)'), self.stateChanged_ApplyTransformation_Slot)

		self.refresh_values = QPushButton("&Reload Values")
		self.refresh_values.setEnabled(False)
		self.send_request = QPushButton("&Send Request")
		self.cancel_request = QPushButton("&Close")

		QObject.connect(self.refresh_values, SIGNAL('pressed()'), self.reloadRequest_Slot)
		QObject.connect(self.cancel_request, SIGNAL('pressed()'), self.cancel_Slot)
		QObject.connect(self.send_request, SIGNAL('pressed()'), self.accept_Slot)

		vlayout = QVBoxLayout()
		vlayout.addWidget(self.continue_tampering)
		vlayout.addWidget(self.apply_transformation)
		self.gbox.setLayout(vlayout)

		blayout = QHBoxLayout()
		blayout.addWidget(self.refresh_values)
		blayout.addWidget(self.cancel_request)
		blayout.addWidget(self.send_request)

		layout = QVBoxLayout()
		layout.addWidget(self.gbox)
		layout.addWidget(self.request)
		layout.addLayout(blayout)
		self.setModal(False)
		self.setLayout(layout)
		# fill the data
		self.updateRequest()

		self.setMinimumSize(520,300)
		self.resize(900,600)

	def updateRequest(self):
		self.request.setUpdatesEnabled(False)
		self.request.clear()
		url = self.qrequest.url()

		# process request
		root = QTreeWidgetItem()
		root.setText(0, core.network.getHTTPMethodString(self.op))
		root.setText(1, url.toString(QUrl.StripTrailingSlash))
		root.setFlags(root.flags() | Qt.ItemIsEditable)
		self.request.invisibleRootItem().addChild(root)
		for h in self.qrequest.rawHeaderList():
			item = QTreeWidgetItem()
			item.setText(0, QString(h))
			item.setText(1, QString(self.qrequest.rawHeader(h)))
			item.setFlags(item.flags() | Qt.ItemIsEditable)
			self.request.invisibleRootItem().addChild(item)

		cookies = self.netmanager.cookieJar().cookiesForUrl(url)
		if cookies and 0 < len(cookies):
			separator_0 = QTreeWidgetItem()
			separator_0.setText(0, '-')
			self.request.invisibleRootItem().addChild(separator_0)
			tree_cookies = QTreeWidgetItem()
			tree_cookies.setText(0, "Cookies")
			tree_cookies.setText(1, "")
			self.request.invisibleRootItem().addChild(tree_cookies)
			for elmt in cookies:
				item = QTreeWidgetItem()
				item.setText(0, QString(elmt.name()))
				item.setText(1, QString(elmt.toRawForm()).remove(QString(elmt.name()+' = ')))
				item.setFlags(item.flags() | Qt.ItemIsEditable)
				tree_cookies.addChild(item)
			self.request.expandAll()

		if self.outgoingDataList and 0 < len(self.outgoingDataList):
			separator_1 = QTreeWidgetItem()
			separator_1.setText(0, '-')
			self.request.invisibleRootItem().addChild(separator_1)
			tree_post = QTreeWidgetItem()
			tree_post.setText(0, "POST data")
			tree_post.setText(1, "")
			self.request.invisibleRootItem().addChild(tree_post)
			for elmts in self.outgoingDataList:
				item = QTreeWidgetItem()
				item.setText(0, elmts[0])
				if 2 == len(elmts):
					item.setText(1, elmts[1])
				item.setFlags(item.flags() | Qt.ItemIsEditable)
				tree_post.addChild(item)
			self.request.expandAll()
		self.request.setUpdatesEnabled(True)

	def getHTTPRequest(self):
		return self.nrequest

	def prepareRequest(self):
		# load all the components in an HTTPRequest structure
		if self.refresh_values.isEnabled():
			# retrieve data
			self.nrequest = HTTPRequest()
			nrequest = {'method' : None, 'url' : None, 'headers' : [], 'cookies' : [], 'post' : []}
			request_iter = QTreeWidgetIterPy(self.request)
			firstiter, state = True, "headers"
			for elmt in request_iter:
				if firstiter:
					nrequest['method'] = elmt.text(0)
					nrequest['url'] = elmt.text(1)
					firstiter = False
				else:
					# state: headers -> cookies -> post
					if "-" == elmt.text(0):
						continue
					if "headers" == state:
						if "Cookies" == elmt.text(0):
							state = "cookies"
							continue
						elif "POST data" == elmt.text(0):
							state = "post"
							continue
					elif "cookies" == state:
						if "POST data" == elmt.text(0):
							state = "post"
							continue
					nrequest[state].append((elmt.text(0), elmt.text(1)))
			self.nrequest.setMethod(nrequest['method'])
			self.nrequest.setUrl(nrequest['url'])
			self.nrequest.setHeaders(nrequest['headers'])
			# set tampered cookies in the current cookiejar
			if nrequest['cookies'] and 0 < len(nrequest['cookies']):
				self.nrequest.setCookies(nrequest['cookies'])
				self.netmanager.cookieJar().setCookiesFromUrl(self.nrequest.getQtCookies(), self.nrequest.url)
			# process and store the POST data using post_history structure
			if nrequest['post'] and 0 < len(nrequest['post']):
				self.nrequest.setData(nrequest['post'])

	def reloadRequest_Slot(self):
		self.updateRequest()
		self.nrequest = None
		self.refresh_values.setEnabled(False)

	def requestChangedItemHeaders_Slot(self, item, col):
		self.refresh_values.setEnabled(True)

	def stateChanged_ApplyTransformation_Slot(self, state):
		pass

	def stateChanged_ContinueTampering_Slot(self, state):
		if Qt.Unchecked == state:
			self.netmanager.setIntercept(False)
		else:
			self.netmanager.setIntercept(True)

	def addRowTreeWidget_Slot(self, item):
		p = item.parent()
		new_item = QTreeWidgetItem()
		new_item.setText(0, "")
		new_item.setText(1, "")
		new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
		if p:
			p.addChild(new_item)
		else:
			self.request.invisibleRootItem().addChild(new_item)

	def duplicateRowTreeWidget_Slot(self, item):
		p = item.parent()
		new_item = QTreeWidgetItem()
		new_item.setText(0, item.text(0))
		new_item.setText(1, item.text(1))
		new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
		if p:
			p.addChild(new_item)
		else:
			self.request.invisibleRootItem().addChild(new_item)

	def deleteRowTreeWidget_Slot(self, item):
		self.request.invisibleRootItem().removeChild(item)

	def accept_Slot(self):
		self.prepareRequest()
		self.accept()

	def cancel_Slot(self):
		self.reject()
