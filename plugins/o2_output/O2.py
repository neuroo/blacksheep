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
import re, sys, json
from core.plugins.interfaces import PluginMonitor

URL_REGEXP = re.compile(r"https?://([-\w\.]+)+(:\d+)?(/([\w/_\.]*(\?\S+)?)?)?", re.I)

class O2(PluginMonitor):
	def __init__(self):
		PluginMonitor.__init__(self)

	def process(self, url, request, response, content_type, content):
		req_json = json.dumps(request)
		rep_json = json.dumps(response)
		sys.stdout.write("""O2::REACHED_CONTENT-[url="%s"][request=\%s"][response="%s"][content-type="%s"]""" %  (O2.__escape(url), O2.__escape(req_json), O2.__escape(req_json), O2.__escape(content_type)))
		sys.stdout.flush()

		list_urls = O2.__find_urls(url, content)
		for u in list_urls:
			sys.stdout.write("O2::DISCOVERED_URL-[url=\"%s\"]" %  O2.__escape(u))
			sys.stdout.flush()
	
	@staticmethod
	def __escape(rts):
		return rts.replace('"', "\"")

	@staticmethod
	def __find_urls(url, content):
		urls = URL_REGEXP.findall(content)
		if urls and 0 < len(urls):
			return urls
		return None