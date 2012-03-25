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
from PyQt4.QtNetwork import *


PROXY_STRING_METHOD = {
	"No proxy" : QNetworkProxy.NoProxy,
	"Socks5 proxy" : QNetworkProxy.Socks5Proxy,
	"HTTP proxy" : QNetworkProxy.HttpProxy,
	"HTTP caching proxy" : QNetworkProxy.HttpCachingProxy,
	"FTP caching proxy" : QNetworkProxy.FtpCachingProxy
}
PROXY_METHOD_STRING = dict((v, k) for (k, v) in PROXY_STRING_METHOD.iteritems())


class ProxyDialog(QDialog):
	def __init__(self, netmanager, parent=None):
		QDialog.__init__(self, parent)

		self.netmanager = netmanager
		cur_proxy = self.netmanager.proxy()

		self.checkBoxGroups = QButtonGroup()
		self.noproxy = QCheckBox("No prox&y")
		self.noproxy.setChecked(True)
		# QObject.connect(self.noproxy, SIGNAL('stateChanged(int)'), self.noproxy_Slot)
		self.manualproxy = QCheckBox("&Manual proxy configuration")
		QObject.connect(self.manualproxy, SIGNAL('stateChanged(int)'), self.manualproxy_Slot)
		self.checkBoxGroups.addButton(self.noproxy)
		self.checkBoxGroups.addButton(self.manualproxy)

		self.proxyType = QComboBox()
		for proxy_str in PROXY_STRING_METHOD:
			if "No proxy" == proxy_str:
				continue
			self.proxyType.addItem(QString(proxy_str))

		self.host = QLineEdit()
		self.host.setText(cur_proxy.hostName())
		self.port = QSpinBox()
		self.port.setMinimum(0)
		self.port.setValue(cur_proxy.port())
		self.port.setMaximum(65536)
		self.user = QLineEdit()
		self.user.setText(cur_proxy.user())
		self.password = QLineEdit()
		self.password.setEchoMode(QLineEdit.Password)
		self.user.setText(cur_proxy.password())

		self.helping_activator = [self.proxyType, self.host, self.port, self.user,self.password]

		self.acceptButton = QPushButton("OK")
		self.cancelButton = QPushButton("Cancel")
		QObject.connect(self.acceptButton, SIGNAL("pressed()"), self.accept_Slot)
		QObject.connect(self.cancelButton, SIGNAL("pressed()"), self.cancel_Slot)

		hhost_port = QHBoxLayout()
		hhost_port.addWidget(self.host)
		hhost_port.addWidget(self.port)

		glayout = QGridLayout()
		glayout.addWidget(QLabel("Proxy type:"), 0, 0)
		glayout.addWidget(self.proxyType, 0, 1)
		glayout.addWidget(QLabel("Proxy address:"), 1, 0)
		glayout.addLayout(hhost_port, 1, 1)
		glayout.addWidget(QLabel("Username:"), 2, 0)
		glayout.addWidget(self.user, 2, 1)
		glayout.addWidget(QLabel("Password:"), 3, 0)
		glayout.addWidget(self.password, 3, 1)

		for widget in self.helping_activator:
			widget.setEnabled(False)

		hbuttons = QHBoxLayout()
		hbuttons.addWidget(self.acceptButton)
		hbuttons.addWidget(self.cancelButton)

		layout = QVBoxLayout()
		layout.addWidget(self.noproxy)
		layout.addWidget(self.manualproxy)

		layout.addLayout(glayout)
		layout.addLayout(hbuttons)

		self.setModal(False)
		self.setLayout(layout)

	def manualproxy_Slot(self, state):
		if Qt.Unchecked == state:
			for widget in self.helping_activator:
				widget.setEnabled(False)
		else:
			for widget in self.helping_activator:
				widget.setEnabled(True)

	def accept_Slot(self):
		# store information in the networkmanager
		if self.noproxy.isChecked():
			self.netmanager.setProxy_Slot(QNetworkProxy.NoProxy)
		else:
			self.netmanager.setProxy_Slot(PROXY_STRING_METHOD[str(self.proxyType.currentText())], self.host.text(),
										  self.port.value(), self.user.text(), self.password.text())
		self.accept()

	def cancel_Slot(self):
		self.reject()
