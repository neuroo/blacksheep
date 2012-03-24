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

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.Qsci import *

import core.management

class JSEvaluator(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

		self.evalJS = QsciScintilla()
		self.lexer = QsciLexerJavaScript(self.evalJS)
		# set the auto complete mode
		self.evalJS.setAutoCompletionSource(QsciScintilla.AcsAPIs)
		self.evalJS.setAutoCompletionReplaceWord(True)
		self.evalJS.setAutoCompletionThreshold(2)
		self.jsAPI = QsciAPIs(self.lexer)
		self.jsAPI.load(core.management.configuration['path']['resources'] + 'syntax/javascript.txt')
		self.jsAPI.prepare()
		self.lexer.setAPIs(self.jsAPI)
		self.evalJS.setMarginLineNumbers(1, True)
		self.evalJS.setMarginWidth(1, 25)
		fsize = 8
		for sty in range(128):
			if not self.lexer.description(sty).isEmpty():
				f = self.lexer.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				self.lexer.setFont(f, sty)
		self.evalJS.setLexer(self.lexer)

		self.load_action =  QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/folder.png"), "Load JavaScript file...", self)
		self.clear_action = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/page_white.png"), "Clear editor", self)
		self.eval_action = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/cog.png"), "Execute current script",  self)
		self.get_action = QAction(QIcon(core.management.configuration['path']['resources'] + "images/icons/folder_go.png"), "Get value from JavaScript", self)
		QObject.connect(self.clear_action, SIGNAL("triggered()"), self.clear_Slot)
		QObject.connect(self.eval_action, SIGNAL("triggered()"), self.evaluateJS_Slot)
		QObject.connect(self.get_action, SIGNAL("triggered()"), self.getEvaluatedJS_Slot)
		QObject.connect(self.load_action, SIGNAL("triggered()"), self.loadEvaluatedJS_Slot)

		self.pb_clear = JSEvaluator.__create_pushbutton(self, core.management.configuration['path']['resources'] + "images/icons/page_white.png", "Clear editor content")
		self.pb_load = JSEvaluator.__create_pushbutton(self, core.management.configuration['path']['resources'] + "images/icons/folder.png", "Load JavaScript file...")
		self.pb_get = JSEvaluator.__create_pushbutton(self, core.management.configuration['path']['resources'] + "images/icons/folder_go.png", "Get value from JavaScript")
		self.pb_exec = JSEvaluator.__create_pushbutton(self, core.management.configuration['path']['resources'] + "images/icons/cog.png", "Execute current script")

		QObject.connect(self.pb_clear, SIGNAL("pressed()"), self.clear_Slot)
		QObject.connect(self.pb_exec, SIGNAL("pressed()"), self.evaluateJS_Slot)
		QObject.connect(self.pb_get, SIGNAL("pressed()"), self.getEvaluatedJS_Slot)
		QObject.connect(self.pb_load, SIGNAL("pressed()"), self.loadEvaluatedJS_Slot)

		hlayout = QHBoxLayout()
		hlayout.setSpacing(10)
		hlayout.setGeometry(QRect(0, 0, 150, 30))
		hlayout.addWidget(self.pb_load)
		hlayout.addWidget(self.pb_clear)
		hlayout.addWidget(self.pb_exec)
		hlayout.addWidget(self.pb_get)
		hlayout.addStretch(0)

		layout = QVBoxLayout()
		layout.addLayout(hlayout)
		layout.addWidget(self.evalJS)
		self.setLayout(layout)

	@staticmethod
	def __create_pushbutton(instance, icon_file, text):
		b = QPushButton(QIcon(icon_file), "", instance)
		b.setStyleSheet("QPushButton:hover {border:1px solid #ccc;}")
		b.setToolTip(text)
		b.setFlat(True)
		b.setMaximumSize(30, 30)
		return b

	def clear_Slot(self):
		self.evalJS.setText('')

	def evaluateJS_Slot(self):
		self.emit(SIGNAL('evalJavaScript_Signal'), self.evalJS.text())

	def getEvaluatedJS_Slot(self):
		self.emit(SIGNAL('getJavaScript_Signal'), self.evalJS.text())

	def loadEvaluatedJS_Slot(self):
		fileName = QFileDialog.getOpenFileName(self, "Load JavaScript", "./", "JavaScript Files (*.js)")
		if 0 < len(fileName):
			self.evalJS.setText(open(unicode(fileName)).read())
