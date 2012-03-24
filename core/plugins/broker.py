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

"""
	The plugin broker gets the data sent over by a plugin and register
	it to the particular components.
	This allows a plugin to communicate and adds data directly to the BS
	internal system.
"""
class PluginBroker(QObject):
	def __init__(self, netmanager, plugins, findingsdb):
		self.netmanager = netmanager
		self.appinfo = self.netmanager.appinfo
		self.plugins = plugins
		self.findings = findingsdb

		# prepare the signal wire for all python plugins
		for puid in self.plugins.getPlugins('Python'):
			QObject.connect(self.plugins.getPluginData(puid, 'Python')['instance'], SIGNAL('plugin_RegisterInformation'), self.info_dispatch)
			QObject.connect(self.plugins.getPluginData(puid, 'Python')['instance'], SIGNAL('plugin_NotifyInformation'), self.info_notify)


	def info_dispatch(self, puid, information_type, data):
		print "Received from %s: %s - {%s}" % (puid, information_type, data)
		if 'url' == information_type:
			# add the discovered URL to the application info repository
			self.appinfo.addSpideredURL(data, "URL spidered by the plugin %s" % puid)

	def info_notify(self, puid, information_type, data):
		print "Received: %s - {%s}" % (information_type, data)
