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

from core.coddec.encoding import CharsetEncoding

class ToolKit(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self.charsetEncoding = CharsetEncoding()

		# mainwindget is the HTML editor
		self.input = QsciScintilla()
		self.input.setReadOnly(False)
		self.input.setMarginLineNumbers(1, True)
		self.input.setMarginWidth(1, 25)
		lexer_input = QsciLexerJavaScript(self.input)
		self.input.setLexer(lexer_input)
		self.output = QsciScintilla()
		self.output.setReadOnly(True)
		self.output.setMarginLineNumbers(1, True)
		self.output.setMarginWidth(1, 25)
		lexer_output = QsciLexerJavaScript(self.output)
		self.output.setLexer(lexer_output)
		fsize = 8
		for sty in range(128):
			if not lexer_input.description(sty).isEmpty():
				f = lexer_input.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				lexer_input.setFont(f, sty)
			if not lexer_output.description(sty).isEmpty():
				f = lexer_output.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				lexer_output.setFont(f, sty)

		bottomLayout = QHBoxLayout()
		bottomLayout.addWidget(self.input)
		bottomLayout.addWidget(self.output)

		toolBar = QHBoxLayout()
		self.pushButton = QPushButton("Convert")
		QObject.connect(self.pushButton, SIGNAL("pressed()"), self.convert_Slot)

		self.input_label = QLabel("Input encoding:")
		self.input_list = QComboBox()

		self.output_label = QLabel("Output encoding:")
		self.output_list = QComboBox()

		self.display_list = self.charsetEncoding.getAvailableCodecs()

		for elmt in self.display_list:
			self.input_list.addItem(elmt)
			self.output_list.addItem(elmt)

		toolBar.addWidget(self.input_label)
		toolBar.addWidget(self.input_list)

		toolBar.addWidget(self.output_label)
		toolBar.addWidget(self.output_list)
		toolBar.addWidget(self.pushButton)

		layout = QVBoxLayout()
		layout.addLayout(toolBar)
		layout.addLayout(bottomLayout)

		self.setLayout(layout)

	def convert_Slot(self):
		input_charset = self.input_list.currentText()
		output_charset = self.output_list.currentText()
		i = self.input.text()
		if len(i) < 1:
			self.output.setText("Empty...")
		else:
			t = self.charsetEncoding.encode(i, input_charset, output_charset)
			if t:
				self.output.setText(t)
