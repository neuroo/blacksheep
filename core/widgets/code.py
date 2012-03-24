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
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.Qsci import *
from PyQt4.QtXmlPatterns import *

class CodeBrowserOptions(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self.search_mode = 'Text'
		self.doc_view = 'Code View'

		self.sci_readonly = QCheckBox("Editable code")
		self.sci_readonly.setChecked(False)
		QObject.connect(self.sci_readonly, SIGNAL('stateChanged(int)'), self.setReadOnlySci_Slot)

		self.toggle_button = QPushButton("Code View")

		self.codeAction = QAction('Code View', self)
		self.domAction = QAction('DOM View', self)

		QObject.connect(self.codeAction, SIGNAL("triggered()"), self.codeView_Slot)
		QObject.connect(self.domAction, SIGNAL("triggered()"), self.domView_Slot)

		self.view_menu = QMenu()
		self.view_menu.addAction(self.codeAction)
		self.view_menu.addAction(self.domAction)

		self.toggle_button.setMenu(self.view_menu)

		self.search_label = QLabel("Search:")
		self.search_line = QLineEdit()
		QObject.connect(self.search_line, SIGNAL("editingFinished()"), self.search_Slot)

		self.search_select = QPushButton("Search Mode: Text")

		self.textAction = QAction('Text', self)
		self.regexpAction = QAction('RegExp', self)
		self.xpathAction = QAction('XPath', self)
		self.nodeAction = QAction('Node', self)

		QObject.connect(self.textAction, SIGNAL("triggered()"), self.text_Slot)
		QObject.connect(self.regexpAction, SIGNAL("triggered()"), self.regexp_Slot)
		QObject.connect(self.xpathAction, SIGNAL("triggered()"), self.xpath_Slot)
		QObject.connect(self.nodeAction, SIGNAL("triggered()"), self.node_Slot)

		self.search_mode_menu = QMenu()
		self.search_mode_menu.addAction(self.textAction)
		self.search_mode_menu.addAction(self.regexpAction)
		# TODO: integrate the XPath search
		#self.search_mode_menu.addAction(self.xpathAction)
		self.search_mode_menu.addAction(self.nodeAction)

		self.search_select.setMenu(self.search_mode_menu)

		layout = QHBoxLayout()
		layout.addWidget(self.sci_readonly)
		layout.addWidget(self.toggle_button)
		layout.addWidget(self.search_label)
		layout.addWidget(self.search_line)
		layout.addWidget(self.search_select)
		self.setLayout(layout)

	def setReadOnlySci_Slot(self, state):
		self.sci_readonly.setChecked(Qt.Unchecked != state)
		self.emit(SIGNAL('readOnlyCheckBox_Scintilla_Unchecked'), self.sci_readonly.checkState() == Qt.Unchecked)

	def text_Slot(self):
		self.search_mode = 'Text'
		self.search_select.setText("Search Mode: Text")
		if 0 < len(self.search_line.text()):
			self.search_Slot()

	def regexp_Slot(self):
		self.search_mode = 'RegExp'
		self.search_select.setText("Search Mode: RegExp")
		if 0 < len(self.search_line.text()):
			self.search_Slot()

	def xpath_Slot(self):
		self.search_mode = 'XPath'
		self.search_select.setText("Search Mode: XPath")
		if 0 < len(self.search_line.text()):
			self.search_Slot()

	def node_Slot(self):
		self.search_mode = 'Node'
		self.search_select.setText("Search Mode: Node")
		if 0 < len(self.search_line.text()):
			self.search_Slot()

	def codeView_Slot(self):
		self.doc_view = 'Code View'
		self.toggle_button.setText("Code View")
		self.emit(SIGNAL('codeView_Signal'))

	def domView_Slot(self):
		self.doc_view = 'DOM View'
		self.toggle_button.setText("DOM View")
		self.emit(SIGNAL('domView_Signal'))

	def search_Slot(self):
		self.emit(SIGNAL('search_Signal'), self.search_line.text(), self.search_mode)


class DisplayContainer(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self.active_item = 'source'
		self.text_modified = False
		self.last_pos = None

		self.dom = None
		self.tree = QTreeWidget()
		self.tree.setColumnCount(2)
		self.tree.setWordWrap(True)
		self.tree.resizeColumnToContents(0)
		self.tree.setAlternatingRowColors(True)
		self.tree.setHeaderLabels(['HTML Node', 'Node Content'])
		self.tree.setUniformRowHeights(True)

		self.scintilla = QsciScintilla()
		lexer = QsciLexerHTML(self.scintilla)
		self.scintilla.setLexer(lexer)
		self.scintilla.setReadOnly(True)

		self.scintilla.setMarginLineNumbers(1, True)
		self.scintilla.setMarginWidth(1, 45)
		self.scintilla.setWrapMode(QsciScintilla.WrapWord)
		self.scintilla.setBraceMatching(QsciScintilla.SloppyBraceMatch)
		self.scintilla.setFolding(QsciScintilla.BoxedTreeFoldStyle)
		QObject.connect(self.scintilla, SIGNAL('textChanged()'), self.textChanged_Slot)

		fsize = 10
		for sty in range(128):
			if not lexer.description(sty).isEmpty():
				f = lexer.font(sty)
				f.setFamily('monaco, monospace, sans-sherif')
				f.setPointSize(fsize)
				lexer.setFont(f, sty)

		layout = QVBoxLayout()
		layout.addWidget(self.scintilla)
		layout.addWidget(self.tree)
		self.setLayout(layout)

		self.tree.hide()

	def repaint(self, event):
		self.setPosition()

	def uncheckedReadOnly_Slot(self, unchecked):
		self.scintilla.setReadOnly(unchecked)

	def textPositionChanged_slot(self, line, pos):
		self.last_pos = (line, pos)

	def setPosition(self):
		self.scintilla.setCursorPosition(self.last_pos[0], self.last_pos[1])

	def textChanged_Slot(self):
		self.text_modified = True

	def processChildren_Tree(self, parentItem, parentElmt):
		elmt = parentElmt.firstChild()
		while not elmt.isNull():
			# create the sub-node item
			item = QTreeWidgetItem()
			item.setText(0, elmt.tagName())
			item.setText(1, elmt.toPlainText().remove("\n").remove("\r"))
			item.setFlags(item.flags() | Qt.ItemIsEditable)
			parentItem.addChild(item)
			# process attributes
			if elmt.hasAttributes():
				for e in elmt.attributeNames():
					citem = QTreeWidgetItem()
					citem.setText(0, '@' + e)
					citem.setText(1, elmt.attribute(e).remove("\n").remove("\r"))
					citem.setFlags(item.flags() | Qt.ItemIsEditable)
					# set bg color of attributes to efefef
					citem.setBackgroundColor(0, QColor(225, 230, 250))
					citem.setBackgroundColor(1, QColor(225, 230, 250))
					item.addChild(citem)
			self.processChildren_Tree(item, elmt)
			elmt = elmt.nextSibling()

	def populateTree(self):
		self.tree.clear()
		if self.dom:
			self.tree.setUpdatesEnabled(False)
			self.processChildren_Tree(self.tree.invisibleRootItem(), self.dom)
			self.tree.expandAll()
			self.tree.setUpdatesEnabled(True)
			self.tree.resizeColumnToContents(0)

	def setActiveWidget(self, view_item = 'source'):
		if 'source' == view_item:
			self.tree.hide()
			self.scintilla.show()
		elif 'dom' == view_item:
			self.scintilla.hide()
			self.tree.show()

	def traverseTreeSearch(self, text):
		# switch display to DOM view
		self.scintilla.hide()
		self.tree.show()
		utext = text.toUpper()
		self.populateTree()
		foundItems = self.tree.findItems(utext, Qt.MatchRecursive)
		c_found = len(foundItems)
		self.emit(SIGNAL('foundItems_Signal'), utext, c_found)
		if 0 < c_found:
			self.tree.setCurrentItem(foundItems[0])
			# for all found Items, set a light yellow background color
			self.tree.setUpdatesEnabled(False)
			for citem in foundItems:
				citem.setBackgroundColor(0, QColor(255, 250, 205))
				citem.setBackgroundColor(1, QColor(255, 250, 205))
			self.tree.setUpdatesEnabled(True)

	# TODO: integrate the XPath search
	def xpathSearchDOM(self, text):
		if self.dom:
			xpath_query = QXmlQuery()
			xpath_query.setFocus(self.dom.toPlainText())
			xpath_query.setQuery(text)
			if not xpath_query.isValid():
				return
			res = None
			xpath_query.evaluateTo(res)
			return res



class CodeBrowser(QWidget):
	""" Tab widget to print the HTML source code """
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		# Options for code explorer (Source code, DOM, Search...)
		self.options = CodeBrowserOptions()
		QObject.connect(self.options, SIGNAL("codeView_Signal"), self.optionCodeView_Slot)
		QObject.connect(self.options, SIGNAL("domView_Signal"), self.optionDOMView_Slot)
		QObject.connect(self.options, SIGNAL("search_Signal"), self.search_Slot)

		self.display = DisplayContainer()
		QObject.connect(self.options, SIGNAL('readOnlyCheckBox_Scintilla_Unchecked'), self.display.uncheckedReadOnly_Slot)

		layout = QVBoxLayout()
		layout.addWidget(self.options)
		layout.addWidget(self.display)
		self.setLayout(layout)

	def setText_Slot(self, s):
		self.display.scintilla.setText(s)
		self.display.text_modified = False

	def setDOM_Slot(self, d):
		if not d == self.display.dom:
			self.display.dom = d
			self.display.populateTree()

	def optionCodeView_Slot(self):
		self.display.setActiveWidget('source')

	def optionDOMView_Slot(self):
		self.display.setActiveWidget('dom')

	def search_Slot(self, text, mode):
		if mode in ('Text', 'RegExp'):
			# search in scintilla widget
			reg = 'RegExp' == mode
			cs = False
			wo = False
			wrap = True
			# scintilla handles a classic behavior of the search
			self.display.scintilla.findFirst(text, reg,cs,wo,wrap)
		elif mode in ('Node', 'XPath'):
			if 'Node' == mode:
				self.display.traverseTreeSearch(text)
			else:
				self.display.xpathSearchDOM(text)
