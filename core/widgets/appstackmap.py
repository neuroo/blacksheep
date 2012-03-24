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
import sys, os

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.Qsci import *

import core.management


class ApplicationStackMap(QWidget):
	"""display the visited websites as a tree"""
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)

		self.group = {}
		self.dict = {}

		self.tree = QTreeWidget()
		QObject.connect(self.tree, SIGNAL('itemClicked(QTreeWidgetItem *, int)'), self.selectedItem_Slot)

		layout = QGridLayout()
		layout.addWidget(self.tree, 0, 0)

		layout.setColumnStretch(0,1)
		layout.setColumnStretch(1,1)
		self.setLayout(layout)

	def selectedItem_Slot(self, item, int):
		return
