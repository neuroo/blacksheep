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
from PySide.QtCore import *
from PySide.QtGui import *

class Authentication(QDialog):
	def __init__(self, parent, reply):
		QDialog.__init__(self, parent)

		self.blockedUrl = reply.url().toString()

		self.usernameLabel = QLabel("Username:")
		self.passwordLabel = QLabel("Password:")

		self.usernameInput = QLineEdit()
		self.passwordInput = QLineEdit()
		self.passwordInput.setEchoMode(QLineEdit.Password)

		self.acceptButton = QPushButton("Log In")
		self.cancelButton = QPushButton("Cancel")

		QObject.connect(self.acceptButton, SIGNAL("pressed()"), self.accept_Slot)
		QObject.connect(self.cancelButton, SIGNAL("pressed()"), self.cancel_Slot)

		layout = QVBoxLayout()

		self.messageLabel = QLabel("The server %s requires a username and a password" % self.blockedUrl)
		self.messageLabel.setWordWrap(True)

		layout.addWidget(self.messageLabel)

		g_layout = QGridLayout()
		g_layout.addWidget(self.usernameLabel, 0, 0)
		g_layout.addWidget(self.usernameInput, 0, 1)
		g_layout.addWidget(self.passwordLabel, 1, 0)
		g_layout.addWidget(self.passwordInput, 1, 1)

		layout.addLayout(g_layout)

		h_layout = QHBoxLayout()
		h_layout.addWidget(self.acceptButton)
		h_layout.addWidget(self.cancelButton)

		layout.addLayout(h_layout)

		self.setModal(True)
		self.setLayout(layout)

	def accept_Slot(self):
		self.accept()

	def cancel_Slot(self):
		self.reject()
