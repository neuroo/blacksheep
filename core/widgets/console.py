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

# Main console of Sheep, show info to user (javasript events and plugins custom msg)
class Console(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.log = "# Start Sheep"
		bottomLayout = QVBoxLayout()
		self.console = QsciScintilla()
		lexer = QsciLexerProperties(self.console)
		self.console.setLexer(lexer)
		self.console.setMarginLineNumbers(1,True)
		self.console.setMarginWidth(1, 25)
		self.console.setReadOnly(True)
		fsize = 8
		for sty in range(128):
			if not lexer.description(sty).isEmpty():
				f = lexer.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				lexer.setFont(f, sty)

		layout = QVBoxLayout()
		layout.addWidget(self.console)
		self.setLayout(layout)
		self.setText_Slot()

	def addConsole_Slot(self, l):
		self.log += "\n" + l
		self.setText_Slot()

	def setText_Slot(self):
		self.console.setText(self.log)
