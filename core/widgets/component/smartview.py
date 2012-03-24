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
from PyQt4.Qsci import *

DISPLAY_CONTENT_TYPE = {
	'html' : QsciLexerHTML,
	'javascript' : QsciLexerJavaScript,
	'json' : QsciLexerJavaScript,
	'xml' : QsciLexerXML,
	'css' : QsciLexerCSS,
	'text' : QsciLexerProperties,
}

# remove 'text' because of the text/html etc.
LIST_DISPLAY_CONTENT_TYPE = DISPLAY_CONTENT_TYPE.keys()
LIST_DISPLAY_CONTENT_TYPE.remove('text')

# SmartView is a view of an HTTP response body
# it will evolve in dual views of items (e.g., images and hexdump of the image content)
# might add format knowledge extraction (zip, format headers, etc.)
class SmartView(QWidget):
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)
		self.scintilla = QsciScintilla()
		lexer = SmartView.__prepare_lexer(QsciLexerProperties, self.scintilla)
		self.scintilla.setLexer(lexer)
		self.scintilla.setReadOnly(True)
		self.scintilla.setMarginLineNumbers(1, True)
		self.scintilla.setMarginWidth(1, 45)
		self.scintilla.setWrapMode(QsciScintilla.WrapWord)

		layout = QVBoxLayout()
		layout.addWidget(self.scintilla)
		self.setLayout(layout)
		self.setMinimumWidth(400)
		# self.setWindowTitle()

	@staticmethod
	def __prepare_lexer(cls, scintilla_instance):
		lexer = cls(scintilla_instance)
		fsize = 8
		for sty in range(128):
			if not lexer.description(sty).isEmpty():
				f = lexer.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				lexer.setFont(f, sty)
		return lexer

	@staticmethod
	def __display_content_type(content_type):
		for i in LIST_DISPLAY_CONTENT_TYPE:
			if i in content_type:
				return i
		if 'text' in content_type:
			return 'text'
		return None

	def setContent(self, content, content_type):
		display_ct = SmartView.__display_content_type(content_type)
		if not display_ct:
			content = SmartView.hexdump(str(content))
		else:
			lexer = SmartView.__prepare_lexer(DISPLAY_CONTENT_TYPE[display_ct], self.scintilla)
			self.scintilla.setLexer(lexer)
		self.scintilla.setText(QString(content))

	# stolen from stackoverflow
	@staticmethod
	def hexdump(src, length=8):
		result = []
		digits = 4 if isinstance(src, unicode) else 2
		for i in xrange(0, len(src), length):
			s = src[i:i+length]
			hexa = ' '.join(["%0*X" % (digits, ord(x))  for x in s])
			text = ''.join([x if 0x20 <= ord(x) < 0x7F else b'.'  for x in s])
			result.append("%04X   %-*s   %s" % (i, length * (digits + 1), hexa, text))
		return '\n'.join(result)
