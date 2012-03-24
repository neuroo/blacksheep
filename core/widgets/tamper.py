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

import re, csv

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

import core.network
import core.management
import core.utils.http_messages

from core.widgets.component.widgetiterator import QTreeWidgetIterPy
from core.widgets.component.tampertreewidget import TamperTreeWidget
from core.widgets.component.smartview import SmartView

COLUMN_KEYWORDS = {
	'filetype' : 4,
	'url' : 3,
	'method' : 0,
	'charset' : 5
}

FILTER_TOKENIZER = re.compile("(" + '|'.join(COLUMN_KEYWORDS.keys()) + "):([^\\s]+)", re.I)


FILTER_TOOLTIP = """Filter commands:
%s are the different directives used
to create a particular selection on the HTTP history
view. The search works with an exact match (case insensitive).

ex: filetype:html filetype:swf will
only show the HTTP request to those
contents.""" % ', '.join(COLUMN_KEYWORDS.keys())


class NetBrowser(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self.filter_activated = False
		self.filter_text = None

		# the most important component of sheep...
		self.manager = core.network.NetworkAccessManager()
		QObject.connect(self.manager, SIGNAL("availableNetworkReply_Signal"), self.storeNetworkHistory_Slot)


		self.clear_history = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/database_delete.png"), "Clear History", self)
		self.export_history = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/database_table.png"), "Export History As CSV", self)
		QObject.connect(self.clear_history, SIGNAL('triggered()'), self.clearHistory_Slot)
		QObject.connect(self.export_history, SIGNAL('triggered()'), self.exportHistory_Slot)

		self.toolBar = QToolBar()
		self.toolBar.setStyleSheet("QToolBar {margin:1;border:0;padding:1}")
		self.toolBar.addAction(self.clear_history)
		self.toolBar.addAction(self.export_history)

		# manage the GUI now...
		self.ssl_color = QColor(255, 250, 205)
		self.groupBox = QGroupBox("HTTP requests and responses")

		# TODO: Use acustom ItemModel to store types like Integer (for sorting)
		self.headers = ["HTTP Method", "Status code", "Secure", "URL", "Content-Type", "Charset", "Content-Length", "Internal Request ID"]
		self.model = QStandardItemModel(0, len(self.headers), parent)
		for i in range(len(self.headers)):
			self.model.setHorizontalHeaderItem(i, QStandardItem(self.headers[i]))

		self.root_item = self.model.invisibleRootItem()
		self.current_selection = []
		self.selectionModel = QItemSelectionModel(self.model)
		QObject.connect(self.selectionModel, SIGNAL('selectionChanged(const QItemSelection&, const QItemSelection&)'), self.selectionChanged)

		self.proxyModel = QSortFilterProxyModel()
		self.proxyModel.setSourceModel(self.model)

		self.treeview = QTreeView()
		self.treeview.setRootIsDecorated(False)
		self.treeview.setAlternatingRowColors(True)
		self.treeview.setSortingEnabled(True)
		self.treeview.setModel(self.model)
		# self.treeview.setColumnHidden(7, True)
		self.treeview.setSelectionMode(QAbstractItemView.ExtendedSelection)
		self.treeview.setSelectionModel(self.selectionModel)
		self.treeview.setUniformRowHeights(True)
		self.updateTreeViewSizes()
		QObject.connect(self.treeview, SIGNAL("clicked(const QModelIndex&)"), self.clickedIndex_Slot)

		# filter
		self.active_filter = QCheckBox("Filter HTTP request")
		self.filter_label = QLabel("Filter:")
		self.filter_edit = QLineEdit()
		self.filter_edit.setToolTip(FILTER_TOOLTIP)
		self.add_finding = QPushButton("Add to findings")
		self.add_finding.setEnabled(False)
		QObject.connect(self.add_finding, SIGNAL("pressed()"), self.addFindingRequest_Slot)
		self.add_testcase = QPushButton("Add to test cases")
		self.add_testcase.setEnabled(False)
		QObject.connect(self.add_testcase, SIGNAL("pressed()"), self.addTestCaseRequest_Slot)
		QObject.connect(self.filter_edit, SIGNAL("editingFinished()"), self.filter_Slot)
		QObject.connect(self.active_filter, SIGNAL("stateChanged(int)"), self.filterStateChanged_Slot)

		self.vertical_separator = QLabel("|")
		hlayout = QHBoxLayout()
		hlayout.addWidget(self.toolBar)
		hlayout.addWidget(self.active_filter)
		hlayout.addWidget(self.filter_label)
		hlayout.addWidget(self.filter_edit)
		hlayout.addWidget(self.vertical_separator)
		hlayout.addWidget(QLabel("Selection:"))
		hlayout.addWidget(self.add_finding)
		hlayout.addWidget(self.add_testcase)

		layout = QVBoxLayout()
		layout.addLayout(hlayout)
		layout.addWidget(self.treeview)
		self.groupBox.setLayout(layout)
		mainLayout = QVBoxLayout()
		mainLayout.addWidget(self.groupBox)
		self.setLayout(mainLayout)

	def renew(self):
		self.current_selection = []
		self.model.removeRows(0, self.model.rowCount())

	def clearHistory_Slot(self):
		self.renew()

	def exportHistory_Slot(self):
		orgFileName = core.management.configuration['path']['user'] + 'bsheep_history_.csv'
		filename = QFileDialog.getSaveFileName(self, "Save file as...", orgFileName, "Comma Separater Values (*.csv)")
		if not filename.isEmpty():
			nrows = range(self.model.rowCount())
			writer = csv.writer(open(filename, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
			writer.writerow(self.headers)
			for rowindex in nrows:
				writer.writerow([unicode(self.model.item(rowindex, i).text()) for i in range(8)])

	def selectionChanged(self, selected, deselected):
		if self.selectionModel.hasSelection():
			# add the req_id in order in the current selection
			self.current_selection = [self.model.item(index.row(), 7).text().toInt()[0] for index in self.selectionModel.selectedRows()]
			if 0 < len(self.current_selection):
				self.add_finding.setEnabled(True)
				self.add_testcase.setEnabled(True)
				return
		self.current_selection = []
		self.add_finding.setEnabled(False)
		self.add_testcase.setEnabled(False)

	def addFindingRequest_Slot(self):
		self.emit(SIGNAL('addRequestIDtoFindings_Signal'), self.current_selection)

	def addTestCaseRequest_Slot(self):
		self.emit(SIGNAL('addRequestIDtoTestCases_Signal'), self.current_selection)

	def filterStateChanged_Slot(self, state):
		self.filter_activated = False if Qt.Unchecked == state else True
		self.updateTreeView()

	def filter_Slot(self):
		self.filter_text = self.filter_edit.text()
		self.updateTreeView()

	def paintEvent(self, event):
		self.updateTreeViewSizes()

	def sslError_Slot(self, reply, errors):
		self.emit(SIGNAL('sslErrors(reply,errors)'), reply, errors)

	def clickedIndex_Slot(self, index):
		value = self.model.item(index.row(), 7).text().toInt()[0]
		# populate the specialized view with the information from
		self.emit(SIGNAL('updateDocTamperView_Signal'), value)

	def showAllTreeViewItems(self):
		nitems_range = range(self.model.rowCount())
		for i in nitems_range:
			self.treeview.setRowHidden(i, self.root_item.index(), False)

	def updateTreeView(self):
		if 0 == self.model.rowCount():
			return
		# hiding the matches from the filter_text
		show_everything = True
		if self.filter_activated:
			filter_str_py = unicode(self.filter_text)
			if 4 < len(filter_str_py):
				list_findings = FILTER_TOKENIZER.findall(filter_str_py)
				nitems_range = range(self.model.rowCount())
				keepItems_rows = []

				if 0 < len(list_findings):
					show_everything = False

				for finding in list_findings:
					if finding[0] in COLUMN_KEYWORDS:
						colnum = COLUMN_KEYWORDS[finding[0]]
						value = QString(finding[1])
						# found items to match the given criteria for the column
						items = self.model.findItems(value, Qt.MatchContains, colnum)
						for item in items:
							row = item.row()
							if row not in keepItems_rows:
								keepItems_rows.append(row)
				# hide items to be hidden
				self.treeview.setUpdatesEnabled(False)
				for i in nitems_range:
					if i not in keepItems_rows:
						self.treeview.setRowHidden(i, self.root_item.index(), True)
					else:
						self.treeview.setRowHidden(i, self.root_item.index(), False)
				self.updateTreeViewSizes()
				self.treeview.setUpdatesEnabled(True)
		if show_everything:
			self.showAllTreeViewItems()

	def extractHeadersInfo(self, headers):
		content_type, content_length, charset = '-', '-', '-'
		for (name, value) in headers:
			name = str(name).lower()
			if "content-type" == name:
				content_type = str(value)
				if "charset = " in content_type:
					index = content_type.find("charset = ")
					charset = content_type[index + len("charset = "):]
				if ';' in content_type:
					content_type = content_type[:content_type.find(';')]
			elif "content-length" == name:
				content_length = str(value)
		return content_type, content_length, charset

	def storeNetworkHistory_Slot(self, request_id):
		info = self.manager.getNetworkHistory(request_id)
		if not info:
			core.management.logger.error("NetBrowser::storeNetworkHistory_Slot- The request_id %s is not accessible at this time" % str(request_id))
			return
		url = info['request']['url'].toString(QUrl.StripTrailingSlash)
		method = info['type']
		status = "-"
		if info['response']['status']:
			status = info['response']['status'].toInt()[0]
			if status in core.utils.http_messages.HTTP_MESSAGES:
				status = QString(str(status)) + " - " + QString(core.utils.http_messages.HTTP_MESSAGES[status][0])
		secure = '-' if info['response']['secure'] == "false" else info['response']['secure']
		content_type, content_length, charset = self.extractHeadersInfo(info['response']['headers'])

		# process request/response to add in the Tree
		elmModelItem = []
		elmModelItem.append(QStandardItem(method))
		elmModelItem.append(QStandardItem(status))
		elmModelItem.append(QStandardItem(secure))
		elmModelItem.append(QStandardItem(url))
		elmModelItem.append(QStandardItem(content_type))
		elmModelItem.append(QStandardItem(charset))
		elmModelItem.append(QStandardItem(content_length))
		elmModelItem.append(QStandardItem(str(request_id)))
		self.model.appendRow(elmModelItem)
		self.updateTreeView()

	def updateTreeViewSizes(self):
		self.treeview.setColumnWidth(3, int(.5 * float(self.width())))
		self.treeview.resizeColumnToContents(0)
		self.treeview.resizeColumnToContents(1)
		self.treeview.resizeColumnToContents(2)
		self.treeview.resizeColumnToContents(4)
		self.treeview.resizeColumnToContents(5)

class TamperingData(QWidget):
	""" tampering data widget in dock """
	def __init__(self, netmanager, parent = None):
		QWidget.__init__(self, parent)
		self.netmanager = netmanager
		self.current_request_id = 0

		self.smartview = SmartView(self)
		self.smartview.hide()

		self.requestview = TamperTreeWidget()
		self.requestview.setRootIsDecorated(False)
		self.requestview.setAlternatingRowColors(True)
		self.requestview.setSortingEnabled(False)
		self.requestview.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.requestview.setHeaderLabels(['HTTP Request Header', 'Value'])
		self.requestview.resizeColumnToContents(0)
		self.requestview.setWordWrap(True)
		QObject.connect(self.requestview, SIGNAL("itemChanged(QTreeWidgetItem *, int)"), self.requestChangedItem_Slot)
		QObject.connect(self.requestview, SIGNAL("addRowTreeWidget"), self.addRowTreeWidget_Slot)
		QObject.connect(self.requestview, SIGNAL("duplicateRowTreeWidget"), self.duplicateRowTreeWidget_Slot)
		QObject.connect(self.requestview, SIGNAL("deleteRowTreeWidget"), self.deleteRowTreeWidget_Slot)

		self.responseview = QTreeWidget()
		self.responseview.setRootIsDecorated(False)
		self.responseview.setAlternatingRowColors(True)
		self.responseview.setSortingEnabled(False)
		self.responseview.setHeaderLabels(['HTTP Response Header', 'Value'])
		self.responseview.resizeColumnToContents(0)

		self.gbox = QGroupBox("&HTTP Request")

		self.refresh_button = QPushButton("Refresh")
		self.refresh_button.setEnabled(False)
		QObject.connect(self.refresh_button, SIGNAL("pressed()"), self.refreshViews_Slot)

		self.response_button = QPushButton("HTTP response body")
		QObject.connect(self.response_button, SIGNAL("pressed()"), self.viewResponse_Slot)

		self.replay_button = QPushButton("Make request")
		QObject.connect(self.replay_button, SIGNAL("pressed()"), self.replayRequest_Slot)

		self.export_button = QPushButton("Export as...")
		QObject.connect(self.replay_button, SIGNAL("pressed()"), self.exportRequest_Slot)

		self.addTestCases_button = QPushButton("Add to test cases")
		QObject.connect(self.addTestCases_button, SIGNAL("pressed()"), self.addTestCaseRequest_Slot)

		self.addFinding_button = QPushButton("Add to findings")
		QObject.connect(self.addFinding_button, SIGNAL("pressed()"), self.addFindingRequest_Slot)

		vlayout = QVBoxLayout()
		vlayout.addWidget(self.response_button)
		vlayout.addWidget(self.refresh_button)
		vlayout.addWidget(self.replay_button)
		vlayout.addWidget(self.export_button)
		vlayout.addWidget(self.addTestCases_button)
		vlayout.addWidget(self.addFinding_button)
		self.gbox.setLayout(vlayout)

		layout = QHBoxLayout()
		layout.addWidget(self.gbox)
		layout.addWidget(self.requestview)
		layout.addWidget(self.responseview)
		self.setLayout(layout)

	def addRowTreeWidget_Slot(self, item):
		p = item.parent()
		new_item = QTreeWidgetItem()
		new_item.setText(0, "")
		new_item.setText(1, "")
		new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
		if p:
			p.addChild(new_item)
		else:
			self.requestview.invisibleRootItem().addChild(new_item)

	def duplicateRowTreeWidget_Slot(self, item):
		p = item.parent()
		new_item = QTreeWidgetItem()
		new_item.setText(0, item.text(0))
		new_item.setText(1, item.text(1))
		new_item.setFlags(new_item.flags() | Qt.ItemIsEditable)
		if p:
			p.addChild(new_item)
		else:
			self.requestview.invisibleRootItem().addChild(new_item)

	def deleteRowTreeWidget_Slot(self, item):
		self.requestview.invisibleRootItem().removeChild(item)

	def viewResponse_Slot(self):
		# create popup with smart document preview
		if 0 < self.current_request_id:
			self.smartview.setWindowFlags(Qt.Window)
			content, content_type = self.netmanager.getResponseContent(self.current_request_id)
			if content:
				self.smartview.show()
				self.smartview.setContent(content, content_type)

	def retrieveHeader(self):
		headers = []
		self.requestview

	def addFindingRequest_Slot(self):
		if 0 < self.current_request_id:
			self.emit(SIGNAL('addRequestIDtoFindings_Signal'), [self.current_request_id])

	def addTestCaseRequest_Slot(self):
		if 0 < self.current_request_id:
			self.emit(SIGNAL('addRequestIDtoTestCases_Signal'), [self.current_request_id])

	def exportRequest_Slot(self):
		# if modified, send to tamper.create_request to forge the new request
		# else, send the request_id for a simple replay based on historical requests
		if self.refresh_button.isEnabled():
			# retrieve data
			nrequest = {'method' : None, 'url' : None, 'headers' : [], 'cookies' : [], 'post' : []}
			request_iter = QTreeWidgetIterPy(self.requestview)
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

					nrequest[state].append((elmt.text(0), elmt.text(1)))
			self.emit(SIGNAL('createHTTPRequest'), nrequest)
		else:
			self.emit(SIGNAL('createHTTPRequest'), self.current_request_id)


	def replayRequest_Slot(self):
		request_headers = self.retrieveHeader()

	def requestChangedItem_Slot(self, item, col):
		self.refresh_button.setEnabled(True)

	def refreshViews_Slot(self):
		self.setRequestResponse_Slot(self.current_request_id)
		self.refresh_button.setEnabled(False)

	@staticmethod
	def __create_treeitem(name, value, icon = None):
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

	def setRequestResponse_Slot(self, request_id):
		self.current_request_id = request_id
		info = self.netmanager.getNetworkHistory(request_id)

		self.requestview.setUpdatesEnabled(False)
		self.requestview.clear()
		# process request
		item = QTreeWidgetItem()
		item.setText(0, info['type'])
		item.setText(1, info['request']['url'].toString(QUrl.StripTrailingSlash))
		item.setFlags(item.flags() | Qt.ItemIsEditable)
		self.requestview.invisibleRootItem().addChild(item)
		for h in info['request']['headers']:
			self.requestview.invisibleRootItem().addChild(TamperingData.__create_treeitem(h[0], h[1] if 2 == len(h) else ""))

		# add Cookies view for request
		if info['request']['cookies']:
			cookies = info['request']['cookies']
			tree_cookies = TamperingData.__create_treeseparator("Cookies")
			self.requestview.invisibleRootItem().addChild(tree_cookies)
			for elmt in cookies:
				tree_cookies.addChild(TamperingData.__create_treeitem(QString(elmt.name()), QString(elmt.toRawForm()).remove(QString(elmt.name()+' = '))))
			self.requestview.expandAll()

		# add POST data for request
		if info['request']['content']:
			post_data = QString(info['request']['content-QByteArray'])
			tree_post = TamperingData.__create_treeseparator("POST data")
			self.requestview.invisibleRootItem().addChild(tree_post)
			postQueryStringURL = QUrl("http://sheep")
			postQueryStringURL.setEncodedQuery(info['request']['content-QByteArray'])
			for elmts in postQueryStringURL.queryItems():
				tree_post.addChild(TamperingData.__create_treeitem(QString(elmts[0]), elmts[1] if 2 == len(elmts) else ""))
			self.requestview.expandAll()
		self.requestview.setUpdatesEnabled(True)

		self.responseview.setUpdatesEnabled(False)
		self.responseview.clear()
		# process request
		for h in info['response']['headers']:
			item = QTreeWidgetItem()
			item.setText(0, QString(h[0]))
			if 2 == len(h):
				item.setText(1, QString(h[1]))
			self.responseview.invisibleRootItem().addChild(item)
		self.responseview.setUpdatesEnabled(True)
