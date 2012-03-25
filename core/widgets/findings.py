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
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from core.utils.findingsdb import FindingsDatabase
from core.dialog.findingcategory import NewFindingCategoryDialog
from core.widgets.component.findingdisplay import FindingDisplay

import core.management

class FindingTreeWidget(QTreeWidget):
	def __init__(self, parent=None):
		QTreeWidgetItem.__init__(self, parent)
		self.contextmenu = QMenu(self)
		# item might be a finding or a category (depends on the action triggered)
		self.current_item = None
		self.duplicate_finding = QAction("Duplicate Finding", self)
		self.duplicate_finding.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/split.png'))
		self.delete_finding = QAction("Delete Finding", self)
		self.delete_finding.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/delete.png'))
		self.add_category = QAction("Add Finding Category", self)
		self.add_category.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/add.png'))

		# self.delete_category = QAction("Delete Finding Category", self)

		QObject.connect(self.duplicate_finding, SIGNAL("triggered()"), self.duplicateFinding_Slot)
		QObject.connect(self.delete_finding, SIGNAL("triggered()"), self.deleteFinding_Slot)
		QObject.connect(self.add_category, SIGNAL("triggered()"), self.addCategory_Slot)


	def contextMenuEvent(self, event):
		self.current_item = self.currentItem()
		item = self.current_item
		# if the item has a finding ID -> Show delete and duplicate
		# else.. show "add category"
		self.contextmenu.clear()
		if item and 0 < len(item.text(7)):
			self.contextmenu.addAction(self.duplicate_finding)
			self.contextmenu.addAction(self.delete_finding)
		else:
			self.contextmenu.addAction(self.add_category)
		self.contextmenu.exec_(event.globalPos())
		QTreeWidget.contextMenuEvent(self, event)

	def duplicateFinding_Slot(self):
		self.emit(SIGNAL('duplicateFinding'), self.current_item)

	def deleteFinding_Slot(self):
		self.emit(SIGNAL('deleteFinding'), self.current_item)

	def addCategory_Slot(self):
		self.emit(SIGNAL('addCategory'))


class Findings(QWidget):
	def __init__(self, netmanager, parent=None):
		QWidget.__init__(self, parent)

		self.sshort_id = 0
		self.findingsdb = FindingsDatabase(netmanager)
		QObject.connect(self.findingsdb, SIGNAL('refreshFindingsView'), self.updateTree)
		QObject.connect(self.findingsdb, SIGNAL('newFindingForURL'), self.newFindingForURL_Slot)
		self.folder_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/folder.png')

		self.tree = FindingTreeWidget()
		self.tree.setColumnCount(7)
		self.tree.setWordWrap(True)
		self.tree.resizeColumnToContents(0)
		self.tree.setAlternatingRowColors(True)
		self.tree.setHeaderLabels(['Vulnerability', 'Domain', 'Location', 'Method', 'Parameter', 'Payload', 'Information', 'FindingID'])
		self.tree.setUniformRowHeights(True)
		QObject.connect(self.tree, SIGNAL('itemClicked(QTreeWidgetItem *, int)'), self.selectedFinding_Slot)
		QObject.connect(self.tree, SIGNAL('duplicateFinding'), self.duplicateFinding_Slot)
		QObject.connect(self.tree, SIGNAL('deleteFinding'), self.deleteFinding_Slot)
		QObject.connect(self.tree, SIGNAL('addCategory'), self.addCategory_Slot)

		self.findingdisplay = FindingDisplay(self.findingsdb, netmanager)
		QObject.connect(self.findingdisplay, SIGNAL('updateFindingTree'), self.updateTree)

		self.toplevelItems = {}
		self.updateTree()

		self.splitter = QSplitter()
		self.splitter.addWidget(self.tree)
		self.splitter.addWidget(self.findingdisplay)

		layout = QHBoxLayout()
		layout.addWidget(self.splitter)
		self.setLayout(layout)


	def newFindingForURL_Slot(self, qurlstr):
		self.emit(SIGNAL('newFindingForURL'), qurlstr)

	def updateVulneratiblityType(self):
		self.toplevelItems = {}
		vuln_cat = self.findingsdb.getCategories()
		for uid in vuln_cat:
			name = vuln_cat[uid]['name']
			self.toplevelItems[name] = QTreeWidgetItem()
			self.toplevelItems[name].setIcon(0, self.folder_icon)
			self.toplevelItems[name].setText(0, name)

	def insertFinding(self, name, qurlstr, data):
		uid = self.findingsdb.getCategoryUID(name)
		if uid:
			self.findingsdb.insert(uid, qurlstr, data)
			self.updateTree()

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	@staticmethod
	def __createitem(findingid, info, representatives):
		item = QTreeWidgetItem()
		item.setText(1, info['domain'])
		item.setText(2, Findings.__url_str(representatives[1]))
		item.setText(3, representatives[0])
		item.setText(4, representatives[2])
		item.setText(5, representatives[3])
		item.setText(6, info['type'])
		item.setText(7, findingid)
		return item

	def updateTree(self):
		self.updateVulneratiblityType()
		category_names = self.toplevelItems.keys()
		category_names.sort()
		self.tree.setUpdatesEnabled(False)
		self.tree.clear()
		for name in category_names:
			uid = self.findingsdb.getCategoryUID(name)
			if uid and self.findingsdb.hasFinding(uid):
				self.tree.invisibleRootItem().addChild(self.toplevelItems[name])
				for findingid in self.findingsdb.getFindingsPerUID(uid):
					representatives = self.findingsdb.getFindingRepresentative(findingid)
					self.toplevelItems[name].addChild(Findings.__createitem(findingid, self.findingsdb.getFindingInfo(findingid), representatives))
		self.tree.expandAll()
		for i in range(8):
			self.tree.resizeColumnToContents(i)
		self.tree.setUpdatesEnabled(True)

	def selectedFinding_Slot(self, item, col):
		findingid = item.text(7)
		if findingid and 0 < len(findingid):
			self.showFindingInformation(str(findingid))

	def duplicateFinding_Slot(self, item):
		findingid = item.text(7)
		if findingid and 0 < len(findingid):
			# copy the content and change the findingid
			self.findingsdb.duplicateFinding(str(findingid))
			self.findingdisplay.rebuildClassificationDropDown()
			self.updateTree()

	def deleteFinding_Slot(self, item):
		findingid = item.text(7)
		if findingid and 0 < len(findingid):
			self.findingsdb.delete(str(findingid))
			self.findingdisplay.rebuildClassificationDropDown()
			self.updateTree()
			self.findingdisplay.current_findingid = None

	def addCategory_Slot(self):
		addfinding_dialog = NewFindingCategoryDialog(self)
		if addfinding_dialog.exec_() == QDialog.Accepted and 0 < len(addfinding_dialog.category_name.text()):
			category_name = unicode(addfinding_dialog.category_name.text())
			cwe_list = (' '.join(str(addfinding_dialog.cwe_list.text()).split())).split(',')
			capec_list = (' '.join(str(addfinding_dialog.capec_list.text()).split())).split(',')
			description = unicode(addfinding_dialog.description.toPlainText())
			reference = unicode(addfinding_dialog.reference.toPlainText())
			self.findingsdb.addCategory(category_name, cwe_list, capec_list, description, reference)
			self.findingdisplay.rebuildClassificationDropDown()
			self.updateTree()

	def populateFinding_Slot(self, name, attackdata):
		# TODO: populate the findings
		self.findingsdb.insertFindingHelper_CategoryAttackIDs(name, attackdata)

	def showFindingInformation(self, findingid):
		self.findingdisplay.loadFromFindingID(findingid)

	def addFromRequestID_Slot(self, request_id):
		# ask for which type the finding should be associated to
		# then, add it to the findings
		findingid = self.findingsdb.insertFinding_RequestID(request_id)
		self.showFindingInformation(findingid)
		self.updateTree()
		# force the view to be on that finding
		self.emit(SIGNAL('forceTabSwitchedTo'), 'findings')

	def renew(self):
		self.findingsdb.renew()

	def save(self):
		self.findingsdb.save()

	def exportAs(self, filename):
		if not filename:
			self.sshort_id += 1
			today = str(QDateTime.currentDateTime().toString("yyyy-MM-d_hh-mm-ss"))
			filename = core.management.configuration['path']['user'] + 'bsheep_findings_%s_%d.xml' % (today, self.sshort_id)
		self.findingsdb.exportAs(filename)
