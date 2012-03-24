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
from PyQt4.QtCore import QObject, SIGNAL

import core.management

# Plugin interface that specify the QObject base class
# it's only necessary to enable the Qt emit/connect signals
# process
class Plugin(QObject):
	__unique = None
	def __init__(self):
		#if Plugin.__unique:
		#	raise Plugin.__unique
		#Plugin.__unique = self
		self.puid = None
		self.bs = None
		QObject.__init__(self)
		core.management.logger.debug("Plugin::__init__")

	def setBSInstance(self, bs):
		self.bs = bs

	def setPUID(self, puid):
		self.puid = puid

	def process(self, url, request, response, content_type, content):
		pass

	def register(self, information_type, data):
		pass

	def notify(self):
		pass

# plugin that receive content and share some information with BlackSheep
# information could be passive analysis, artifacts analysis (GIF inspection, etc.),
# but also providing information to disaplay (e.g., flash decompiler)
class PluginMonitor(Plugin):
	def __init__(self):
		Plugin.__init__(self)
		core.management.logger.debug("PluginMonitor::__init__")

	def process(self, url, request, response, content_type, content):
		pass

	def register(self, information_type, data):
		self.emit(SIGNAL('plugin_RegisterInformation'), self.puid, information_type, data)

	def notify(self, information_type, data):
		self.emit(SIGNAL('plugin_NotifyInformation'), self.puid, information_type, data)


# definitions of other types of plugins
class PluginInjector(Plugin):
	pass

class PluginState(Plugin):
	pass
