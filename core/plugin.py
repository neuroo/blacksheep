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
import os, sys, re, hashlib
import ConfigParser, imp

import core.management

from core.utils.scandir import scandir

def encodeHTMLEntities(s):
	return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"","&quot;").replace("'", "&#39;")

# main structure to store the different plugins
class PluginStore:
	def __init__(self):
		self.plugins = {
			'JavaScript' : {},
			'QtScript' : {},
			'Python' : {}
		}
		self.puid_type = {}
		self.python_plugins = {'monitor' : [], 'injector' : [], 'state' : []}
		self.load_plugins()

	def getPlugins(self, type = 'JavaScript'):
		return self.plugins[type]

	def getPluginTypes(self):
		return self.plugins.keys()

	def getPluginData(self, puid, type='JavaScript'):
		if puid in self.plugins[type]:
			return self.plugins[type][puid]
		return None

	def getActivatedPlugins(self, type='JavaScript'):
		return [puid for puid in self.plugins[type] if self.plugins[type][puid]['active']]

	def getActivatedPluginsGeneric(self, language='Python', type='monitor', content_type=None):
		if 'Python' == language:
			if content_type:
				ret = []
				for puid in self.python_plugins[type]:
					if self.plugins[language][puid]['active']:
						if not self.plugins[language][puid]['prereq'] or self.plugins[language][puid]['prereq']['mime'].match(content_type):
							ret.append(puid)
				return ret
			else:
				return [puid for puid in self.python_plugins[type] if self.plugins[language][puid]['active']]
		else:
			# javascript for now..
			pass

	def register_javascript(self, d):
		puid = d['puid']
		if puid not in self.puid_type and puid not in self.plugins['JavaScript']:
			self.plugins['JavaScript'][puid] = d
			self.puid_type[puid] = 'JavaScript'

	def register_python(self, d, plugin_type):
		puid = d['puid']
		if puid not in self.puid_type and puid not in self.plugins['Python']:
			self.plugins['Python'][puid] = d
			self.puid_type[puid] = 'Python'
			if plugin_type in self.python_plugins and puid not in self.python_plugins[plugin_type]:
				self.python_plugins[plugin_type].append(puid)
			# import the proper module and instanciate the class
			# instanciation is based on the name given in the config file
			self.load_python(d, puid)

	@staticmethod
	def __plugin_module(sname):
		# hoozy lazy for naoh!
		return sname[sname.rfind(os.sep)+1:sname.rfind('.')]

	@staticmethod
	def __plugin_module_dir(sname):
		if os.sep not in sname:
			raise Exception("Ouchy Touchy! Error in PluginStore::__plugin_module_dir. No directory provided as script name. That's pretty bad indeed!")
		return sname[:sname.rfind(os.sep)]

	def load_python(self, d, puid):
		if 'name' in d and 'script' in d:
			sys.path.append(PluginStore.__plugin_module_dir(d['script']))
			try:
				self.plugins['Python'][puid]['puid'] = puid
				self.plugins['Python'][puid]['module'] = __import__(PluginStore.__plugin_module(d['script']))
				self.plugins['Python'][puid]['class'] = getattr(self.plugins['Python'][puid]['module'], d['name'])
				self.plugins['Python'][puid]['instance'] = self.plugins['Python'][puid]['class']()
				self.plugins['Python'][puid]['instance'].setPUID(puid)
			except ImportError, error:
				core.management.logger.error("PluginStore::load_python- Cannot import the plugin '%s' (ImportError: %s)" % (d['script'], error))

	def activeatePlugin(self, puid):
		if puid not in self.puid_type:
			return
		self.plugins[self.puid_type[puid]][puid]['active'] = True

	def deactiveatePlugin(self, puid):
		if puid not in self.puid_type:
			return
		self.plugins[self.puid_type[puid]][puid]['active'] = False

	def togglePlugin(self, puid):
		if puid not in self.puid_type:
			return None
		self.plugins[self.puid_type[puid]][puid]['active'] = not self.plugins[self.puid_type[puid]][puid]['active']
		return self.plugins[self.puid_type[puid]][puid]['active']

	def prepareDescription(self, puid):
		if puid not in self.puid_type:
			return None
		p = self.plugins[self.puid_type[puid]][puid]
		rts = "%s plugin by %s" % (self.puid_type[puid], p['author']['name'])
		if p['author']['email']:
			rts +=" &lt;%s&gt;" % p['author']['email']
		if p['author']['company']:
			rts +=", %s" % p['author']['company']
		rts +="<br /><br /><b>%s</b><br />%s" % (p['name'], encodeHTMLEntities(p['description']))
		return rts

	@staticmethod
	def __bufferize(fname):
		return open(fname).read()

	@staticmethod
	def __parse_config(ini_file, plugin_path):
		config = ConfigParser.RawConfigParser()
		config.read(ini_file)
		if not config.has_section('plugin') or not config.has_option('plugin', 'language'):
			core.management.logger.error("PluginStore::__parse_config- No plugin or plugin::language found for the plugin in '%s'" % plugin_path)
			return None
		# no plugin activated by default
		d = {'active' : False, 'type' : '', 'load' : [], 'author' : {}, 'prereq' : None}
		author = {}
		if config.has_section('author'):
			for item in ('name', 'email', 'website', 'company'):
				value = config.get('author', item) if config.has_option('author', item) else None
				author[item] = value
			d['author'] = author
		language = config.get('plugin', 'language').lower()
		if 'javascript' == language:
			d['type'] = 'JavaScript'
			# JavaScript are the simplest plugins, simply loaded in the DOM when webpage are rendered
			for item in ('script', 'puid', 'name', 'description'):
				d[item] = config.get('plugin', item) if config.has_option('plugin', item) else None
				if item == 'script' and d[item]:
					d[item] = os.path.join(plugin_path, d[item])

			# specify if the plugin gets the HTTP header as JSON
			d['json_headers'] = config.getboolean('plugin', 'json_headers') if config.has_option('plugin', 'json_headers') else False

			if 'script' in d:
				d['script-source'] = PluginStore.__bufferize(d['script'])
			if 'puid' not in d:
				d['puid'] = d['script'] + '_' + hashlib.md5(d['script']).hexdigest()

			load_sequence = []
			if config.has_section('require'):
				load_d = {}
				items = config.items('require')
				for elmt in items:
					config_name = elmt[0]
					if 'load_' in config_name:
						config_name = int(config_name.replace('load_', ''))
					if config_name not in load_d:
						load_d[config_name] = os.path.join(plugin_path, elmt[1])
				sorted_elmts = load_d.keys()
				sorted_elmts.sort()
				for s in sorted_elmts:
					d['load'].append(PluginStore.__bufferize(load_d[s]))
		elif 'python' == language:
			# different type of pluginsL Monitor, Injector, State, Base
			if not config.has_option('plugin', 'type'):
				core.management.logger.error("PluginStore::__parse_config- No plugin::type found for the plugin in '%s'" % plugin_path)
				return None
			d['type'] = config.get('plugin', 'type').lower()

			for item in ('script', 'puid', 'name', 'description'):
				d[item] = config.get('plugin', item) if config.has_option('plugin', item) else None
				if item == 'script' and d[item]:
					d[item] = os.path.join(plugin_path, d[item])

			if config.has_section('prerequisites'):
				d['prereq'] = {}
				if config.has_option('prerequisites', 'mime'):
					mimes = ''.join(config.get('prerequisites', 'mime').split()).split(',')
					regexp_mimes = []
					for elmt in mimes:
						if '*' in elmt:
							elmt = elmt.replace('*', '(.*)')
						regexp_mimes.append(elmt)
					regexp_mimes = '(' + '|'.join(regexp_mimes) + ')'
					try:
						regexp_mimes = re.compile(regexp_mimes, re.I)
					except Exception, error:
						core.management.logger.error("PluginStore::__parse_config- Regexp compile error when processing MIMES in prerequisite section for '%s' (Exception: %s)" % (plugin_path, error))
					d['prereq']['mime'] = regexp_mimes
				else:
					d['prereq']['mime'] = None
			# simple plugins don't require...
			if d['type'] in ('monitor'):
				return d
		return d

	# scan plugin directory and read 'config.ini' to determine the type
	# and other important attributes of a plugin
	def load_plugins(self):
		plugin_directory = core.management.configuration['path']['plugins']
		list_folders = []
		scandir(plugin_directory, list_folders, None, None, True)
		for folder in list_folders:
			ini_file = folder + os.sep + 'config.ini'
			if not os.path.isfile(ini_file):
				continue
			contained_files = []
			scandir(folder, contained_files)

			config = PluginStore.__parse_config(ini_file, folder)
			if config:
				if 'JavaScript' == config['type']:
					self.register_javascript(config)
				elif config['type'] in ('monitor', 'injector', 'state'):
					self.register_python(config, config['type'])
