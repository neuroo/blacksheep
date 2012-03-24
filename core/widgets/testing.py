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

import core.coddec.encoding
import core.security.tamper
import core.security.context as cx
import core.security.sheep.xss as sxss

DEFAULT_TOKEN = "SHEEPTOKEN"
DEFAULT_DOMAIN = "fuckthespam.com"

class SheepTesting(QWidget):
	def __init__(self, netmanager, parent = None):
		QWidget.__init__(self, parent)
		self.netmanager = netmanager
		self.tamperUtility = core.security.tamper.TamperData(False, DEFAULT_TOKEN, DEFAULT_DOMAIN, self.netmanager)

		self.testlogs = QTreeWidget()
		self.testing, self.domainRestriction, self.manualTesting = False, False, False
		self.enableTesting = QCheckBox("Sheep Testing")
		self.enableManualTesting = QCheckBox("Manual Testing")
		self.labelToken = QLabel("ID token:")
		self.domainTesting = QCheckBox("Restrict Domain")

		self.token = QLineEdit(DEFAULT_TOKEN)
		self.token.setValidator(QRegExpValidator(QRegExp('[\w\d]+'), self))

		self.domain = QLineEdit(DEFAULT_DOMAIN)
		self.domain.setValidator(QRegExpValidator(QRegExp('[^\s]+'), self))

		QObject.connect(self.token, SIGNAL("textChanged(QString)"), self.tokenChanged_Slot)
		QObject.connect(self.domain, SIGNAL("textChanged(QString)"), self.domainChanged_Slot)

		self.token.setReadOnly(True)
		self.token.setStyleSheet("QLineEdit {color:#999;}")

		QObject.connect(self.enableTesting, SIGNAL("stateChanged(int)"), self.stateChanged_Slot)
		QObject.connect(self.enableManualTesting, SIGNAL("stateChanged(int)"), self.stateManualChanged_Slot)
		QObject.connect(self.domainTesting, SIGNAL("stateChanged(int)"), self.domainStateChanged_Slot)


		hlayout = QHBoxLayout()
		hlayout.addWidget(self.enableTesting)
		hlayout.addWidget(self.enableManualTesting)
		hlayout.addWidget(self.labelToken)
		hlayout.addWidget(self.token)
		hlayout.addWidget(self.domainTesting)
		hlayout.addWidget(self.domain)

		layout = QVBoxLayout()
		layout.addLayout(hlayout)
		layout.addWidget(self.testlogs)
		self.setLayout(layout)

	# handle a JS event
	def probeJSEvent(self, msg):
		attacksdata = self.tamperUtility.inspectContent_Alert(msg)
		if attacksdata:
			self.emit(SIGNAL('addFinding_Signal'), 'Cross-Site Scripting', attacksdata)

	def tokenChanged_Slot(self, new_token):
		self.tamperUtility.updateToken(new_token)

	def domainStateChanged_Slot(self, state):
		if Qt.Unchecked == state:
			self.domainRestriction = False
		else:
			self.domainRestriction = True
		self.tamperUtility.restrictDomain(self.domainRestriction)

	def domainChanged_Slot(self, new_domain):
		self.tamperUtility.updateDomain(new_domain)

	def emitProperMessage(self):
		if self.testing:
			self.emit(SIGNAL('testingInProgress_Signal'), 'Sheep testing in progress...')
			self.token.setReadOnly(False)
			self.token.setStyleSheet("QLineEdit {color:#000;}")
		elif self.manualTesting:
			self.emit(SIGNAL('testingInProgress_Signal'), 'Manual testing in progress...')
			self.token.setReadOnly(False)
			self.token.setStyleSheet("QLineEdit {color:#000;}")
		else:
			self.emit(SIGNAL('testingInProgress_Signal'), '')
			self.token.setReadOnly(True)
			self.token.setStyleSheet("QLineEdit {color:#999;}")

	def stateChanged_Slot(self, state):
		if Qt.Unchecked == state:
			self.testing = False
			self.tamperUtility.setInactive()
			self.emit(SIGNAL('setTamperingMethod_Signal'), None)
		else:
			self.testing = True
			self.tamperUtility.setActive()
			self.emit(SIGNAL('setTamperingMethod_Signal'), self.tamperUtility.tamperRequest)
		self.emitProperMessage()
		self.emit(SIGNAL('jsAlertsConfiguration_Signal'), self.testing, self.manualTesting)

	def stateManualChanged_Slot(self, state):
		if Qt.Unchecked == state:
			self.manualTesting = False
			self.tamperUtility.setManualInactive()
			self.emit(SIGNAL('setTamperingMethod_Signal'), None)
		else:
			self.manualTesting = True
			self.tamperUtility.setManualActive()
			self.emit(SIGNAL('setTamperingMethod_Signal'), self.tamperUtility.tamperRequest)
		self.emitProperMessage()
		self.emit(SIGNAL('jsAlertsConfiguration_Signal'), self.testing, self.manualTesting)

	def getInterceptToken(self):
		return self.token.text()
