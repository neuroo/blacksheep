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
import re

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from core.widgets.sitemap import probe_icon

# URL rewriting storage
class URLRewritingDialog(QDialog):
	def __init__(self, netmanager, parent = None):
		QDialog.__init__(self, parent)

		self.netmanager = netmanager
		self.urlrewritestore = self.netmanager.urlrewriting
		self.domainIcon = QIcon(probe_icon(None, None, 'domain'))

		self.enable_urlrewriting = QCheckBox("Enable URL rewriting handling")
		self.enable_urlrewriting.setChecked(False)
		QObject.connect(self.enable_urlrewriting, SIGNAL('stateChanged(int)'), self.enableURLRewrite_Slot)

		# QTree widget to represent the different editable information
		self.tree = QTreeWidget()
		self.tree.setRootIsDecorated(False)
		self.tree.setAlternatingRowColors(True)
		self.tree.setSortingEnabled(False)
		self.tree.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.tree.setHeaderLabels(['URL match', 'URL replace', 'Active', 'Unique ID'])
		self.tree.setColumnHidden(3, True)
		self.tree.setColumnWidth (2, 40)
		self.tree.resizeColumnToContents(0)
		self.tree.resizeColumnToContents(1)
		self.tree.setWordWrap(True)
		QObject.connect(self.tree, SIGNAL("itemClicked(QTreeWidgetItem *, int)"), self.clickedIndex_Slot)

		self.gbox = QGroupBox("URL Rewrite Rule")
		self.urlr_id = -1
		self.domain_edit = QLineEdit()
		self.activated_rule = QCheckBox("Active")
		self.match_path = QLineEdit()
		self.replace = QLineEdit()

		self.close_dialog = QPushButton("&Close")
		QObject.connect(self.close_dialog, SIGNAL('pressed()'), self.cancel_Slot)

		self.add_button = QPushButton("Add rule")
		self.upd_button = QPushButton("Update rule")
		self.del_button = QPushButton("Delete rule")
		QObject.connect(self.add_button, SIGNAL('pressed()'), self.addRule_Slot)
		QObject.connect(self.upd_button, SIGNAL('pressed()'), self.updateRule_Slot)
		QObject.connect(self.del_button, SIGNAL('pressed()'), self.deleteRule_Slot)


		domain_active = QHBoxLayout()
		domain_active.addWidget(self.domain_edit)
		domain_active.addWidget(self.activated_rule)

		gridlayout = QGridLayout()
		gridlayout.addWidget(QLabel("Domain:"), 0, 0)
		gridlayout.addLayout(domain_active, 0, 1)
		gridlayout.addWidget(self.add_button, 0, 2)
		gridlayout.addWidget(QLabel("Match:"), 1, 0)
		gridlayout.addWidget(self.match_path, 1, 1)
		gridlayout.addWidget(self.upd_button, 1, 2)
		gridlayout.addWidget(QLabel("Replace:"), 2, 0)
		gridlayout.addWidget(self.replace, 2, 1)
		gridlayout.addWidget(self.del_button, 2, 2)
		self.gbox.setLayout(gridlayout)

		blayout = QGridLayout()
		blayout.addWidget(self.close_dialog, 0, 2)

		layout = QVBoxLayout()
		layout.addWidget(self.enable_urlrewriting)
		layout.addWidget(self.tree)
		layout.addWidget(self.gbox)
		layout.addLayout(blayout)
		self.setModal(False)
		self.setLayout(layout)
		# fill the data
		self.updateListRules()
		self.setMinimumSize(520,700)

	@staticmethod
	def __create_treeitem(match, replace, status, urlr_id, icon = None):
		if not isinstance(match, QString):
			match = QString(match)
		if not isinstance(replace, QString):
			replace = QString(replace)
		item = QTreeWidgetItem()
		item.setText(0, match)
		item.setText(1, replace)
		item.setText(2, "true" if status else "false")
		item.setText(3, QString(str(urlr_id)))
		return item

	@staticmethod
	def __create_treeseparator(name, icon = None):
		bgColor = QColor(0, 0, 255, 25)
		if not isinstance(name, QString):
			name = QString(name)
		item = QTreeWidgetItem()
		item.setText(0, name)
		if icon:
			item.setIcon(0, icon)
		item.setBackgroundColor(0, bgColor)
		item.setBackgroundColor(1, bgColor)
		item.setBackgroundColor(2, bgColor)
		item.setBackgroundColor(3, bgColor)
		return item

	def updateListRules(self):
		self.tree.setUpdatesEnabled(False)
		self.tree.clear()
		for domain in self.urlrewritestore.store:
			if len(self.urlrewritestore.store):
				ditem = URLRewritingDialog.__create_treeseparator(domain, self.domainIcon)
				self.tree.invisibleRootItem().addChild(ditem)
				for urlr_id in self.urlrewritestore.store[domain]:
					d = self.urlrewritestore.store[domain][urlr_id]
					ditem.addChild(URLRewritingDialog.__create_treeitem(d['match'], d['replace'], d['active'], urlr_id))
		self.tree.expandAll()
		self.tree.setColumnWidth (2, 40)
		self.tree.resizeColumnToContents(0)
		self.tree.resizeColumnToContents(1)

		self.tree.setUpdatesEnabled(True)

	def addRule_Slot(self):
		domain = self.domain_edit.text()
		match = self.match_path.text()
		replace = self.replace.text()
		status = self.activated_rule.isChecked()

		if match.isEmpty() or replace.isEmpty() or domain.isEmpty():
			return
		self.urlrewritestore.addRule(domain, match, replace, status)
		self.updateListRules()

	def updateRule_Slot(self):
		urlr_id = self.urlr_id
		domain = self.domain_edit.text()
		match = self.match_path.text()
		replace = self.replace.text()
		status = self.activated_rule.isChecked()
		if match.isEmpty() or replace.isEmpty() or domain.isEmpty():
			return
		self.urlrewritestore.updateValues(domain, urlr_id, match, replace, status)
		self.updateListRules()

	def deleteRule_Slot(self):
		urlr_id = self.urlr_id
		domain = self.domain_edit.text()
		self.urlrewritestore.removeRule(domain, urlr_id)
		self.updateListRules()

	def clickedIndex_Slot(self, item, column):
		urlr_id_str = item.text(3)
		domain = None
		if item.parent():
			domain = item.parent().text(0)
		else:
			domain = item.text(0)
		self.domain_edit.setText(domain)
		if not urlr_id_str.isEmpty():
			# get domain from parent, get urlr_id from item
			self.urlr_id = int(str(urlr_id_str))
			info = self.urlrewritestore.store[domain][self.urlr_id]
			self.match_path.setText(QString(info['match']))
			self.replace.setText(QString(info['replace']))
			self.activated_rule.setChecked(info['active'])

	def enableURLRewrite_Slot(self, state):
		if Qt.Unchecked == state:
			self.netmanager.setURLRewriting(False)
		else:
			if 0 < self.urlrewritestore.urlr_id:
				self.netmanager.setURLRewriting(True)

	def cancel_Slot(self):
		self.reject()
