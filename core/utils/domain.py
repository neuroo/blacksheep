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
import sys, re
from PyQt4.QtCore import QUrl, QString


REGEXP_IP_ADDRESS = re.compile(r'^(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)\.(25[0-5]|2[0-4][0-9]|[01]?[0-9][0-9]?)$')

def extract_domain(hstr, qstr=True):
	if not isinstance(hstr, QUrl):
		hstr = QUrl(hstr)
	hstr = hstr.authority()
	if not isinstance(hstr, unicode):
		hstr = unicode(hstr)
	if '.' not in hstr or REGEXP_IP_ADDRESS.match(hstr):
		return QString(hstr) if qstr else hstr
	hstr = hstr.split('.')
	lhstr = len(hstr)
	hstr = hstr[lhstr-2] + '.' + hstr[lhstr-1]
	return QString(hstr) if qstr else hstr
