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
import os, sys

from PyQt4.QtCore import *
from PyQt4.QtNetwork import *

import core.network

# define a global container for an HTTP request
class HTTPRequest:
	def __init__(self):
		self.method = None
		self.url = None
		self.headers = []
		self.cookies = None
		self.post = None

	def setMethod(self, method = QNetworkAccessManager.GetOperation):
		if not isinstance(method, int):
			self.method = core.network.getHTTPMethodEnum(method)
		else:
			self.method = method

	def setUrl(self, url):
		if isinstance(url, QUrl):
			self.url = url
		else:
			self.url = QUrl(url)

	def setHeaders(self, headers):
		if headers and 0 < len(headers):
			self.headers = [(str(a[0]), str(a[1])) for a in headers]

	def setCookies(self, cookies):
		if cookies and 0 < len(cookies):
			self.cookies = []
			for a in cookies:
				if isinstance(a, QNetworkCookie):
					self.cookies.append((a.name(), a.value()))
				else:
					self.cookies.append((a[0], a[1]))

	def setData(self, post):
		if isinstance(post, str) or isinstance(post, unicode) or isinstance(post, QString) or isinstance(post, QByteArray):
			# create a POST data string
			postQueryStringURL = QUrl("http://sheep")
			postQueryStringURL.setEncodedQuery(QString(post).toAscii())
			self.post = postQueryStringURL.encodedQuery()
		else:
			# we assume the passed post data is a list of key/value
			postQueryStringURL = QUrl("http://sheep")
			for elmts in post:
				postQueryStringURL.addQueryItem(QString(elmts[0]), QString(elmts[1] if 2 == len(elmts) else ''))
			self.post = postQueryStringURL.encodedQuery()

	def getQtCookies(self):
		cookies = []
		for c in self.cookies:
			cookie = QNetworkCookie()
			cookie.setName(QString(c[0]).toAscii())
			cookie.setValue(QString(c[1]).toAscii())
			cookies.append(cookie)
		return cookies

	def networkRequest(self):
		# build the network request
		qrequest = QNetworkRequest()
		qrequest.setUrl(self.url)
		for header in self.headers:
			qrequest.setRawHeader(QByteArray(header[0]), QByteArray(header[1]))
		return self.method, qrequest, self.post if self.post else None
