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
from PySide.QtGui import *
from PySide.QtNetwork import *

import hashlib
import re
import base64
import core.security.sheep.xss as sxss

class RequestTokensInformation:
	def __init__(self):
		self.req = {}
		self.last_id = 0
		self.cached_regexp = None
		self.unique_tokens = {}

	def lookup(self, token):
		if token not in self.unique_token:
			return None
		return self.unique_token[token]

	def computeUniqueToken(self, parameter, value, location, req_id, method="GET", seed=0):
		ustr = u"%s:%s:%s:%d:%s:%d" % (unicode(parameter), unicode(value), unicode(location), req_id, method, seed)
		ustr = hashlib.md5(ustr).hexdigest()
		if ustr not in self.unique_tokens:
			self.unique_tokens[ustr] = {'location' : location, 'parameter' : parameter, 'value' : value, 'req_id' : req_id, 'type' : method}
		self.last_id = req_id
		return ustr

	# return found tokens (compile a OR regexp with all tokens to retrieve findings)
	def inspectContent_Alert(self, buffer, last_id):
		if not self.cached_regexp or last_id != self.last_id:
			if 1 > len(self.unique_tokens):
				return None
			self.cached_regexp = re.compile('('+'|'.join(self.unique_tokens.keys())+')', re.I)
		return [self.unique_tokens[str(token)] for token in self.cached_regexp.findall(buffer)]

	def renew(self):
		self.req = {}
		self.last_id = 0
		slf.cached_regexp = None
		self.unique_tokens = {}

class TamperData(QWidget):
	def __init__(self, active = False, default_token = "SHEEPTOKEN", default_domain = "fuckthespam.com", netmanager = None, parent = None):
		QWidget.__init__(self, parent)
		self.db = RequestTokensInformation()
		self.netmanager = netmanager
		self.netmanager.setRequestTokensInfoReference(self.db)
		self.cookiejar = self.netmanager.cookieJar()

		# Store the QBuffer(QByteArray) here so that they don't get destructed
		# during the request -- I love Qt
		# req_id -> {OriginalQByteArray, QByteArray, QBuffer(QByteArray)}
		# outgoingData = QBuffer(QByteArray)
		self.tampered_post = {}

		self.req_id = 0
		self.mutex = QMutex()
		self.token = default_token
		self.active, self.manual_active = False, False
		self.domain_name, self.restrict_domain = default_domain, False

	def renew(self):
		self.tampered_post = {}
		self.db.renew()

	def updateDomain(self, new_domain):
		self.domain_name = new_domain

	def restrictDomain(self, restrict = False):
		self.restrict_domain = restrict

	def setActive(self):
		self.active = True

	def setInactive(self):
		self.active = False

	def setManualActive(self):
		self.manual_active = True

	def setManualInactive(self):
		self.manual_active = False

	def updateToken(self, new_token):
		self.token = new_token

	def inspectContent_Alert(self, buffer):
		return self.db.inspectContent_Alert(buffer, self.req_id)

	def injectUniqueTokenProbe_List(self, tuple, url, id, _type = "GET"):
		new_list = []
		for (param, value) in tuple:
			if value == self.token:
				value = sxss.generate_probe(self.db.computeUniqueToken(param, value, url, id, _type))
			new_list.append((str(param), value))
		return new_list

	def injectUniqueTokenProbe(self, param_value, url, id, _type = "GET"):
		if not isinstance(param_value, tuple) or 2 != len(param_value):
			raise Exception("TamperData::injectUniqueTokenProbe- Wrong type passed as 'name_value' - (%s | %s)" % (str(type(name_value))), str(param_value))
		param = param_value[0]
		value = param_value[1]
		if self.token == value:
			value = sxss.generate_probe(self.db.computeUniqueToken(param, value, url, id, _type, 0))
		if self.token == param:
			param = sxss.generate_probe(self.db.computeUniqueToken(param, value, url, id, _type, 1))
		return (param, value)

	def replaceUniqueToken_List(self, tuple, url, id, _type = "GET"):
		new_list = []
		for (param, value) in tuple:
			param, value = str(param), str(value)
			if self.token in value:
				token = self.db.computeUniqueToken(param, value, url, id, _type)
				value = value.replace(self.token, token)
			new_list.append((str(param), value))
		return new_list

	def replaceUniqueToken(self, param_value, url, id, _type = "GET"):
		if not isinstance(param_value, tuple) or 2 != len(param_value):
			raise Exception("TamperData::injectUniqueTokenProbe- Wrong type passed as 'name_value' - (%s | %s)" % (str(type(name_value))), str(param_value))
		param = param_value[0]
		value = param_value[1]
		if self.token in value:
			value = value.replace(self.token, self.db.computeUniqueToken(param, value, url, id, _type, 0))
		if self.token in param:
			param = param.replace(self.token, self.db.computeUniqueToken(param, value, url, id, _type, 1))
		return (param, value)

	# Tamper POST data to include the unique ID
	def tamperRequestPOSTData(self, post_data, url, id):
		_type = "POST"
		if id in self.tampered_post:
			core.management.logger.error("TamperData::tamperRequestPOSTData- Conflict of request_ids, '%s' already exists in tamper_post repository" % str(id))
			return None
		postQueryStringURL = QUrl("http://sheep")
		postQueryStringURL.setEncodedQuery(post_data)

		new_postQueryStringURL = QUrl("http://sheep")
		# apply the proper tampering method (either fully automated- probe or manual- simple replacement)
		new_postQueryString = []
		if self.active:
			new_postQueryString = self.injectUniqueTokenProbe_List(postQueryStringURL.queryItems(), url, self.req_id, _type)
		elif self.manual_active:
			new_postQueryString = self.replaceUniqueToken_List(postQueryStringURL.queryItems(), url, self.req_id, _type)

		new_postQueryStringURL.setQueryItems(new_postQueryString)
		new_postQueryString = new_postQueryStringURL.encodedQuery()

		# store results
		self.tampered_post[id] = {'content-QByteArray' : None, 'content' : None}
		self.tampered_post[id]['content-QByteArray'] = new_postQueryString
		self.tampered_post[id]['content'] = QBuffer(self.tampered_post[id]['content-QByteArray'])
		return self.tampered_post[id]['content']


	# Tamper the HTTP headers (tokens -> unique ID)
	def tamperRequestHEADERData(self, qrequest, url, id):
		_type = "HEADER"
		# loop through request header name/value
		nqrequest = QNetworkRequest(qrequest)
		list_headers = qrequest.rawHeaderList()
		for param in list_headers:
			value = qrequest.rawHeader(param)
			if self.active:
				param, value = self.injectUniqueTokenProbe((param, value), url, self.req_id, _type)
			elif self.manual_active:
				param, value = self.replaceUniqueToken((param, value), url, self.req_id, _type)
			nqrequest.setRawHeader(param, value)

		# need to tamper cookie too...
		_type = "COOKIE"
		ncookies = []
		cookies = self.netmanager.cookieJar().cookiesForUrl(url)
		for cookie in cookies:
			name, value = cookie.name(), cookie.value()
			if self.active:
				name, value = self.injectUniqueTokenProbe((name, value), url, self.req_id, _type)
			elif self.manual_active:
				name, value = self.replaceUniqueToken((name, value), url, self.req_id, _type)
			cookie.setName(name)
			cookie.setValue(value)
			ncookies.append(cookie)
		self.netmanager.cookieJar().setCookiesFromUrl(ncookies, url)
		return nqrequest

	def tamperRequest(self, op, req, outgoingData):
		if self.restrict_domain and not req.url().host().contains(self.domain_name):
			self.emit(SIGNAL('consoleLogMessage_Signal'), "Restricted domain: Domain = " + str(self.domain_name) + ", Found = " + str(req.url().host()))
			return op, req, outgoingData

		self.mutex.lock()
		self.req_id +=1
		req_id = self.req_id
		new_url = req.url()
		self.mutex.unlock()

		_type = "GET"
		if self.active:
			url_parameters = new_url.queryItems()
			url_parameters = self.injectUniqueTokenProbe_List(url_parameters, new_url, req_id, _type)
			new_url.setQueryItems(url_parameters)
			req.setUrl(new_url)
		elif self.manual_active:
			url_parameters = new_url.queryItems()
			url_parameters = self.replaceUniqueToken_List(url_parameters, new_url, req_id, _type)
			new_url.setQueryItems(url_parameters)
			req.setUrl(new_url)

		if outgoingData and outgoingData.isReadable():
			outgoingData = self.tamperRequestPOSTData(outgoingData.readAll(), new_url, req_id)

		req = self.tamperRequestHEADERData(req, new_url, req_id)
		return op, req, outgoingData
