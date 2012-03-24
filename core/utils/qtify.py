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

from PySide.QtCore import *


def unqtify_string(rts):
	if isinstance(rts, QString):
		return unicode(rts)
	elif isinstance(rts, QByteArray):
		return str(rts)
	return rts

def unqtify_url(qurl):
	if not isinstance(qurl, QUrl):
		qurl = QUrl(qurl)
	return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

def prepare_plugin_headers(hdr):
	return [(unqtify_string(e[0]), unqtify_string(e[1])) for e in hdr]

