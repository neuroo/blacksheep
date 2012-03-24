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
import os, sys, time

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import core.management
import core.network
import core.interface.application

def main(argc, argv):
	core.management.enable_configuration()
	core.management.enable_plugins()

	app = QApplication(argv)
	app.setWindowIcon(QIcon(core.management.configuration['path']['resources'] + "images/sheep_head.png"))

	mainwindow = core.interface.application.MainWindow()
	QObject.connect(app, SIGNAL('aboutToQuit()'), mainwindow.saveStateObject_Slot)
	core.management.maininstance = mainwindow
	mainwindow.show()
	sys.exit(app.exec_())

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
