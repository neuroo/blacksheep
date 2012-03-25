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
from PyQt4.QtCore import *
from PyQt4.QtGui import *

class NewFindingCategoryDialog(QDialog):
	def __init__(self, parent=None):
		QDialog.__init__(self, parent)

		self.category_name = QLineEdit()
		self.cwe_list = QLineEdit()
		self.cwe_list.setValidator(QRegExpValidator(QRegExp('[\d\s,]+'), self))
		self.capec_list = QLineEdit()
		self.capec_list.setValidator(QRegExpValidator(QRegExp('[\d\s,]+'), self))
		self.description = QTextEdit()
		self.description.setAcceptRichText(False)
		self.description.setAutoFormatting(QTextEdit.AutoNone)
		self.reference = QTextEdit()
		self.reference.setAcceptRichText(False)
		self.reference.setAutoFormatting(QTextEdit.AutoNone)

		self.acceptButton = QPushButton("OK")
		self.cancelButton = QPushButton("Cancel")
		QObject.connect(self.acceptButton, SIGNAL("pressed()"), self.accept_Slot)
		QObject.connect(self.cancelButton, SIGNAL("pressed()"), self.cancel_Slot)

		glayout = QGridLayout()
		glayout.addWidget(QLabel("Category name:"), 0, 0)
		glayout.addWidget(self.category_name, 0, 1)
		glayout.addWidget(QLabel("Description:"), 1, 0)
		glayout.addWidget(self.description, 1, 1)
		glayout.addWidget(QLabel("CWE ID list:"), 2, 0)
		glayout.addWidget(self.cwe_list, 2, 1)
		glayout.addWidget(QLabel("CAPEC ID list:"), 3, 0)
		glayout.addWidget(self.capec_list, 3, 1)
		glayout.addWidget(QLabel("Reference:"), 4, 0)
		glayout.addWidget(self.reference, 4, 1)

		hlayout = QHBoxLayout()
		hlayout.addWidget(self.acceptButton)
		hlayout.addWidget(self.cancelButton)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("Add a new category and generic information that will beintegratedin the different findings.\nWe use CWE and CAPEC for generic mapping."))
		layout.addLayout(glayout)
		layout.addLayout(hlayout)

		self.setModal(False)
		self.setLayout(layout)

	def accept_Slot(self):
		self.accept()

	def cancel_Slot(self):
		self.reject()
