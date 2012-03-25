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
import sys, json
from PyQt4.QtCore import *

def jsonify_headers(headers, variable_name):
	cookies_list = []
	if  headers['request']['cookies']:
		for c in headers['request']['cookies']:
			cookies_list.append((str(c.name()), str(c.value()), str(c.toRawForm())))

	if 'content-QByteArray' not in headers['response'] or 'content-QByteArray' not in headers['request']:
		return "console.log('No header found.');"

	js_header = {
		'method' : headers['type'],
		'request' : {
			'url' : unicode(headers['request']['url'].toString()),
			'headers' : [(str(h1), str(h2)) for h1, h2 in headers['request']['headers']],
			'cookies' : cookies_list,
			'content' : unicode(headers['request']['content-QByteArray'] if headers['request']['content-QByteArray'] else ""),
			'cookies' : []
		},
		'response' : {
			'headers' : [(str(h1), str(h2)) for h1, h2 in headers['response']['headers']],
			'content' : unicode(headers['response']['content-QByteArray'] if headers['response']['content-QByteArray'] else ""),
		}
	}
	return "var %s = %s;" % (variable_name, json.dumps(js_header))
