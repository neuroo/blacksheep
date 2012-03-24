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


from core.widgets.sitemap import probe_icon
from core.widgets.component.widgetiterator import QTreeWidgetIterPy

class FindingDisplay(QWidget):
	def __init__(self, findingdb, netmanager, parent = None):
		QWidget.__init__(self, parent)
		self.findingdb = findingdb
		self.netmanager = netmanager
		self.current_findingid = None

		self.classification_name = QComboBox()
		self.rebuildClassificationDropDown()

		self.findingid = QLineEdit()
		self.findingid.setEnabled(False)
		self.domain_icon = QIcon(probe_icon(None, None, 'domain'))
		self.domain = QLineEdit()
		self.typefinding = QLineEdit()
		self.qurlstr = QLineEdit()
		self.severity = QLineEdit()
		self.impact = QLineEdit()

		self.trace = QTreeWidget()
		self.trace.setColumnCount(7)
		self.trace.setRootIsDecorated(False)
		self.trace.setAlternatingRowColors(True)
		self.trace.setSortingEnabled(False)
		self.trace.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.trace.setWordWrap(True)
		self.trace.setHeaderLabels(["Request ID", "HTTP Method", "URL", "Parameter", "Payload", "Description", "User Information"])
		self.trace.setUniformRowHeights(True)
		self.trace.resizeColumnToContents(0)

		self.description = QTextEdit()
		self.description.setAcceptRichText(False)
		self.description.setAutoFormatting(QTextEdit.AutoNone)

		self.reference = QTextEdit()
		self.reference.setAcceptRichText(False)
		self.reference.setAutoFormatting(QTextEdit.AutoNone)

		self.refresh_button = QPushButton("Refresh Finding Content")
		self.update_button = QPushButton("Persist Content")
		self.add_button = QPushButton("Add Finding")
		QObject.connect(self.add_button, SIGNAL("pressed()"), self.addFinding_Slot)
		QObject.connect(self.refresh_button, SIGNAL("pressed()"), self.refreshFinding_Slot)
		QObject.connect(self.update_button, SIGNAL("pressed()"), self.persistFinding_Slot)

		glayout = QGridLayout()
		glayout.addWidget(QLabel("Category name:"), 0, 0)
		glayout.addWidget(self.classification_name, 0, 1)
		glayout.addWidget(QLabel("Finding ID:"), 0, 2)
		glayout.addWidget(self.findingid, 0, 3)

		glayout.addWidget(QLabel("Domain:"), 1, 0)
		glayout.addWidget(self.domain, 1, 1)

		glayout.addWidget(QLabel("Type of finding:"), 2, 0)
		glayout.addWidget(self.typefinding, 2, 1)


		glayout.addWidget(QLabel("Severity:"), 3, 0)
		glayout.addWidget(self.severity, 3, 1)
		glayout.addWidget(QLabel("Impact:"), 3, 2)
		glayout.addWidget(self.impact, 3, 3)

		ilayout = QGridLayout()
		ilayout.addWidget(QLabel("URL:"), 0, 0)
		ilayout.addWidget(self.qurlstr, 0, 1)
		ilayout.addWidget(QLabel("Trace:"), 1, 0)
		ilayout.addWidget(self.trace, 1, 1)
		ilayout.addWidget(QLabel("Description:"), 2, 0)
		ilayout.addWidget(self.description, 2, 1)
		ilayout.addWidget(QLabel("Reference:"), 3, 0)
		ilayout.addWidget(self.reference, 3, 1)

		ilayout.setAlignment(Qt.AlignTop)


		button_layout = QHBoxLayout()
		#button_layout.addWidget(self.add_button)
		button_layout.addWidget(self.refresh_button)
		button_layout.addWidget(self.update_button)

		ilayout.addLayout(button_layout, 4, 1)

		layout = QVBoxLayout()
		layout.addLayout(glayout)
		layout.addSpacing(20)
		layout.addLayout(ilayout)
		self.setLayout(layout)


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
			value = FindingDisplay.__url_str(value)
		return QString(value)

	@staticmethod
	def __create_treeitem(req_id, method, qtraceurlstr, parameter, payload, description, user, uid=None):
		item = QTreeWidgetItem()
		item.setText(0, FindingDisplay.__qstringify(req_id))
		item.setText(1, FindingDisplay.__qstringify(method))
		item.setText(2, FindingDisplay.__qstringify(qtraceurlstr))
		item.setText(3, FindingDisplay.__qstringify(parameter))
		item.setText(4, FindingDisplay.__qstringify(payload))
		item.setText(5, FindingDisplay.__qstringify(description))
		item.setText(6, FindingDisplay.__qstringify(user))
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		return item

	#  finding id {
	#   'uid' : general type of vuln
	#   'trace' : [{
	#      req_id, uid, parameter, payload, description, user
	#   }]
	#   'severity' : 0-> 5
	#   'impact' :  Don't care, Low, Medium, High, Critical
	#   'description' : ""
	#   'reference' : ""
	#   'domain' : ""
	#   'type' : "Manual/Automated/Plugin/Other"
	def loadFromFindingID(self, findingid):
		if not self.findingdb.hasFinding(findingid):
			self.current_findingid = findingid
			# make sure we have all the classification (default + custom)
			self.rebuildClassificationDropDown()
			info = self.findingdb.getFindingInfo(findingid)
			self.findingid.setText(QString(findingid))
			classification_name = self.findingdb.getcategoryName(info['uid'])
			if classification_name:
				self.classification_name.setCurrentIndex(self.classification_name.findText(QString(classification_name)))

			self.qurlstr.setText(QString(info['qurlstr']))
			self.domain.setText(QString(info['domain']))
			self.severity.setText(QString(str(info['severity'])))
			self.impact.setText(QString(str(info['impact'])))
			self.description.setText(QString(info['description']))
			self.reference.setText(QString(info['reference']))
			self.typefinding.setText(QString(info['type']))

			# fill the trace
			# "Request ID", "Parameter", "Payload", "Description", "User Information"
			self.trace.setUpdatesEnabled(False)
			self.trace.clear()
			root = self.trace.invisibleRootItem()
			for elmt in info['trace']:
				method, qtraceurlstr = self.findingdb.getTraceRepresentative(elmt['req_id'])
				root.addChild(FindingDisplay.__create_treeitem(elmt['req_id'], method, qtraceurlstr, elmt['parameter'],
															   elmt['payload'], elmt['description'], elmt['user'], elmt['uid']))
			self.trace.setUpdatesEnabled(True)

	def rebuildClassificationDropDown(self):
		self.classification_name.clear()
		for elmt in self.findingdb.getCategoryNames():
			self.classification_name.addItem(QString(elmt))

	def addFinding_Slot(self):
		pass

	def refreshFinding_Slot(self):
		if self.current_findingid:
			self.loadFromFindingID(self.current_findingid)

	def persistFinding_Slot(self):
		findingid = self.current_findingid
		if findingid:
			info = self.findingdb.getFindingInfo(findingid)
			olduid = info['uid']
			uid = self.findingdb.getCategoryUID(str(self.classification_name.currentText()))
			if uid:
				self.findingdb.updateFindingParameter(findingid, 'uid', uid)
			self.findingdb.updateFindingParameter(findingid, 'severity', str(self.severity.text()))
			self.findingdb.updateFindingParameter(findingid, 'impact', str(self.impact.text()))
			self.findingdb.updateFindingParameter(findingid, 'description', unicode(self.description.toPlainText()))
			self.findingdb.updateFindingParameter(findingid, 'reference', unicode(self.reference.toPlainText()))
			self.findingdb.updateFindingParameter(findingid, 'type', str(self.typefinding.text()))
			self.findingdb.updateFindingParameter(findingid, 'domain', unicode(self.domain.text()))
			oldqurlstr = info['qurlstr']
			qurlstr = unicode(self.qurlstr.text())
			self.findingdb.updateFindingParameter(findingid, 'qurlstr', qurlstr)

			# update trace
			trace_iter = QTreeWidgetIterPy(self.trace)
			for elmt in trace_iter:
				req_id = int(str(elmt.text(0)))
				#"Request ID", "HTTP Method", "URL", "Parameter", "Payload", "Description", "User Information"
				self.findingdb.updateFindingTraceParameter(findingid, req_id, "parameter", unicode(elmt.text(3)))
				self.findingdb.updateFindingTraceParameter(findingid, req_id, "payload", unicode(elmt.text(4)))
				self.findingdb.updateFindingTraceParameter(findingid, req_id, "description", unicode(elmt.text(5)))
				self.findingdb.updateFindingTraceParameter(findingid, req_id, "user", unicode(elmt.text(6)))

			self.findingdb.propagateChangeFindingID_UID(findingid, olduid, uid)
			self.findingdb.propagateChangeFindingID_URL(findingid, oldqurlstr, qurlstr)

			self.emit(SIGNAL("updateFindingTree"))
