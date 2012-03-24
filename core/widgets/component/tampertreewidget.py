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

from core.widgets.component.widgetiterator import QTreeWidgetIterPy

import core.network
import core.management

class TamperTreeWidget(QTreeWidget):
	def __init__(self, parent=None):
		QTreeWidgetItem.__init__(self, parent)
		self.contextmenu = QMenu(self)
		# item might be a finding or a category (depends on the action triggered)
		self.current_item = None
		self.add_row = QAction("Add row", self)
		self.add_row.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/add.png'))
		self.duplicate_row = QAction("Duplicate row", self)
		self.duplicate_row.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/split.png'))
		self.delete_row = QAction("Delete row", self)
		self.delete_row.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/delete.png'))
		self.copy_clipboard = QAction("Copy rows to clipboard", self)
		self.copy_clipboard.setIcon(QIcon(core.management.configuration['path']['resources'] + '/images/icons/page_copy.png'))

		QObject.connect(self.add_row, SIGNAL("triggered()"), self.addRow_Slot)
		QObject.connect(self.duplicate_row, SIGNAL("triggered()"), self.duplicateRow_Slot)
		QObject.connect(self.delete_row, SIGNAL("triggered()"), self.deleteRow_Slot)
		QObject.connect(self.copy_clipboard, SIGNAL("triggered()"), self.copyHeaderClipboard_Slot)

	def contextMenuEvent(self, event):
		self.current_item = self.currentItem()
		item = self.current_item
		# if the item has a finding ID -> Show delete and duplicate
		# else.. show "add category"
		self.contextmenu.clear()
		self.contextmenu.addAction(self.add_row)
		if item:
			self.contextmenu.addAction(self.duplicate_row)
			self.contextmenu.addAction(self.delete_row)
		self.contextmenu.addSeparator()
		self.contextmenu.addAction(self.copy_clipboard)

		self.contextmenu.exec_(event.globalPos())
		QTreeWidget.contextMenuEvent(self, event)

	def addRow_Slot(self):
		if self.current_item:
			self.emit(SIGNAL('addRowTreeWidget'), self.current_item)

	def duplicateRow_Slot(self):
		if self.current_item:
			self.emit(SIGNAL('duplicateRowTreeWidget'), self.current_item)

	def deleteRow_Slot(self):
		if self.current_item:
			self.emit(SIGNAL('deleteRowTreeWidget'), self.current_item)

	def copyHeaderClipboard_Slot(self):
		clipboard = QApplication.clipboard()
		http_iter = QTreeWidgetIterPy(self)
		clip_text = ""
		for elmt in http_iter:
			clip_text += (elmt.text(0) + ': ' + elmt.text(1)) + '\n'
		clipboard.setText(clip_text)
