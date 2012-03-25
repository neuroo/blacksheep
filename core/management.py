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

import logging
import logging.config
import sys, time, os

import core.plugin

from core.utils.scandir import scandir
from core.utils.useragent import user_agent
from core.plugin import PluginStore

__author__          = "Romain Gaucher"
__contact__ =           " r@rgaucher.info"
__website__ = "http://rgaucher.info"
__application__ = "BlackSheep"
__version__ = "0.1c"
__release__ = __application__ + '/' + __version__

configuration = {}
logger = None
maininstance = None
cookieJar = None
plugins = None
findingdb = None

__default_user_agent__  = user_agent["BlackSheep"]

def enable_plugins():
	global plugins
	plugins = PluginStore()

def set_useragent(ua_key):
	global __default_user_agent__
	sua_key = str(ua_key)
	if sua_key in user_agent:
		__default_user_agent__ = user_agent[sua_key]

def enable_configuration():
	global configuration, logger
	configuration = {'path' : {'resources' : '', 'application' : '', 'plugins' : '', 'user' : '', 'log' : '', 'cache' : 'user\cache' }, 'log' : None}
	configuration['path']['resources'] = os.path.abspath(os.path.join(os.path.curdir, 'resources')) + os.path.sep
	configuration['path']['application'] = os.path.abspath(os.path.curdir) + os.path.sep
	configuration['path']['plugins'] = os.path.abspath(os.path.join(os.path.curdir, 'plugins'))  + os.path.sep
	configuration['path']['user'] = os.path.abspath(os.path.join(os.path.curdir, 'user'))  + os.path.sep
	configuration['path']['log-conf'] = os.path.abspath(os.path.join(configuration['path']['resources'], 'sheep-log.conf'))
	configuration['path']['cache'] = os.path.abspath(os.path.join(configuration['path']['user'], 'cache')) + os.sep
	configuration['path']['certificates'] = os.path.abspath(os.path.join(configuration['path']['user'], 'certificates')) + os.sep

	# make the user directory if doesnt exist
	if not os.path.isdir(configuration['path']['user']):
		os.mkdir(configuration['path']['user'])
	# make the cache directory if doesnt exist
	if not os.path.isdir(configuration['path']['cache']):
		os.mkdir(configuration['path']['cache'])
	# make the certificates directory if doesnt exist
	if not os.path.isdir(configuration['path']['certificates']):
		os.mkdir(configuration['path']['certificates'])

	logging.config.fileConfig(configuration['path']['log-conf'])
	logger = logging.getLogger("sheep")
