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
import sys, os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.Qsci import *

import core.management

class TestCases(QWidget):
	def __init__(self, netmanager, parent=None):
		QWidget.__init__(self, parent)

		self.netmanager = netmanager
		self.appinfo = self.netmanager.appinfo

		self.folder_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/world.png')
		self.url_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/tag.png')
		self.mouse_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/mouse.png')
		self.keyboard_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/keyboard.png')
		self.wand_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/wand.png')

		self.proper_testcase_icon = {
			'mouse' : self.mouse_icon,
			'keyboard' : self.keyboard_icon,
			'domain' : self.folder_icon,
			'magic' : self.wand_icon
		}

		self.tree = QTreeWidget()
		self.tree.setColumnCount(6)
		self.tree.setWordWrap(True)
		self.tree.resizeColumnToContents(0)
		self.tree.setAlternatingRowColors(True)
		self.tree.setHeaderLabels(['Location', 'Event Type', 'User Content', 'Link Followed', 'Web Element', 'Internal Request ID'])
		self.tree.setUniformRowHeights(True)

		layout = QVBoxLayout()
		layout.addWidget(self.tree)
		self.setLayout(layout)

	def selectedItem_Slot(self, item, int):
		return

	def addFromRequestID_Slot(self, request_id):
		pass

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	@staticmethod
	def __qstringify(value):
		if None == value:
			value = ""
		if isinstance(value, int):
			value = str(value)
		elif isinstance(value, QUrl):
			value = TestCases.__url_str(value)
		return QString(value)

	def createInteractionItem(self, event_type, user_content, link_followed, element, request_id):
		item = QTreeWidgetItem()
		item.setText(1, TestCases.__qstringify(event_type))
		if event_type in self.proper_testcase_icon:
			item.setIcon(1, self.proper_testcase_icon[event_type])
		item.setText(2, TestCases.__qstringify(user_content))
		item.setText(3, TestCases.__qstringify(link_followed))
		item.setText(4, TestCases.__qstringify(element))
		item.setText(5, TestCases.__qstringify(request_id))
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		return item

	def createInteractionDomain(self, domain):
		item = QTreeWidgetItem()
		item.setText(0, TestCases.__qstringify(domain))
		item.setIcon(0, self.folder_icon)
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		return item

	def createInteractionURL(self, qurlstr):
		item = QTreeWidgetItem()
		item.setText(0, TestCases.__qstringify(qurlstr))
		item.setIcon(0, self.url_icon)
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		return item

	def userInteractionInfoAvailable_Slot(self, domain, qurlstr, request_id, eventOrigin, user_content, link_followed, element):
		self.tree.setUpdatesEnabled(False)
		# search for the QTreeWidgetItem for domain, if doesn't exist, create it
		parentDomain = None
		treeitems = self.tree.findItems(TestCases.__qstringify(domain), Qt.MatchExactly, 0)
		if treeitems and 0 < len(treeitems):
			parentDomain = treeitems[0]
		else:
			parentDomain = self.createInteractionDomain(domain)
			self.tree.invisibleRootItem().addChild(parentDomain)

		parentQurlStr = None
		treeitems = self.tree.findItems(TestCases.__qstringify(qurlstr), Qt.MatchRecursive, 0)
		if treeitems and 0 < len(treeitems):
			parentQurlStr = treeitems[0]
		else:
			parentQurlStr = self.createInteractionURL(qurlstr)
			parentDomain.addChild(parentQurlStr)

		item = self.createInteractionItem(eventOrigin, user_content, link_followed, element, request_id)
		parentQurlStr.addChild(item)
		self.tree.expandAll()
		for i in range(7):
			self.tree.resizeColumnToContents(i)
		self.tree.setUpdatesEnabled(True)
