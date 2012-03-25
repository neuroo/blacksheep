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
from PyQt4.QtGui import *
from PyQt4.QtNetwork import *

import core.management
import core.dialog.http_tamper
import core.interface.application

from core.utils.urlrewriting import URLRewritingStore
from core.utils.http_request import HTTPRequest
from core.utils.appinfo import SiteInfoStore
from core.utils.qtify import prepare_plugin_headers, unqtify_string

HTTP_METHOD_STRING = {
	QNetworkAccessManager.GetOperation  : "GET",
	QNetworkAccessManager.PostOperation : "POST",
	QNetworkAccessManager.HeadOperation : "HEAD",
	QNetworkAccessManager.PutOperation  : "PUT",
	QNetworkAccessManager.DeleteOperation : "DELETE"
}

HTTP_STRING_METHOD = dict((v, k) for (k, v) in HTTP_METHOD_STRING.iteritems())

def getHTTPMethodString(op):
	return HTTP_METHOD_STRING[op] if op in HTTP_METHOD_STRING else "-"

# return GET if an error is occuring
def getHTTPMethodEnum(rts):
	rts = str(rts)
	if rts in HTTP_STRING_METHOD:
		return HTTP_STRING_METHOD[rts]
	else:
		core.management.logger.error("HTTP method %s not found in HTTP_STRING_METHOD" % rts)
	return QNetworkAccessManager.GetOperation


# NetworkHistory stores all the network interaction related to the
# web pages accessed during testing.
# Structure of 'data':
# data -> request_id -> {
#  'type' : GET/POST/HEAD/PUT
#  'request' : {'headers' : list<string, string>, 'content' : string}
#  'response' : {'headers' : list<string, string>, 'content' : string}
# }
class NetworkHistory(QObject):
	def __init__(self, cache = None, networkManager = None):
		self.request_id = 0
		self.networkCache = cache
		self.netmanager = networkManager

		# facilitate the retrieval of the request_id
		# QNetworkRequest -> request_id
		self.mutex_requestid, self.mutex_storage = QMutex(), QMutex()
		self.request_storage = {}
		self.qurlstr_requestid = {}
		self.last_redirections = {}
		self.data = {}

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		# specifc version of url_str to keep most variants
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment)

	def renew(self):
		self.mutex_requestid.lock()
		self.request_id = 0
		self.data = {}
		self.request_storage = {}
		self.mutex_requestid.unlock()

	def __insert_data(self, req_id, object):
		url = unicode(object.url().toString())
		if url not in self.request_storage:
			self.mutex_storage.lock()
			self.request_storage[url] = [req_id]
			self.mutex_storage.unlock()
		else:
			self.mutex_storage.lock()
			self.request_storage[url].append(req_id)
			self.mutex_storage.unlock()

	def __lookup_data(self, object):
		url = unicode(object.url().toString())
		ret = None
		if url in self.request_storage:
			if 1 == len(self.request_storage[url]):
				ret = self.request_storage[url][0]
				self.mutex_storage.lock()
				del self.request_storage[url]
				self.mutex_storage.unlock()
			else:
				# pop first elmt if list empty after, delete url key
				ret = self.request_storage[url][0]
				self.mutex_storage.lock()
				self.request_storage[url].remove(ret)
				self.mutex_storage.unlock()
		return ret

	def getHistory(self, request_id):
		if request_id not in self.data:
			core.management.logger.error("The HTTP request ID %s isn't in the database" % str(request_id))
			return None
		return self.data[request_id]

	def getHistoryFromURL(self, qurlstr):
		if qurlstr in self.qurlstr_requestid:
			return self.getHistory(self.qurlstr_requestid[qurlstr])
		return None

	# get the last RequestID associated to the qurlstr
	def getRequestIDFromURL(self, qurlstr):
		if qurlstr in self.qurlstr_requestid:
			return self.qurlstr_requestid[qurlstr]
		return None

	def getRequestType(self, request_id):
		return self.data[request_id]['type'] if request_id in self.data else None

	def getURL(self, request_id):
		return self.data[request_id]['request']['url'] if request_id in self.data else None

	def getResponseHeaders(self, request_id):
		return self.data[request_id]['response']['headers'] if request_id in self.data else None

	def getResponseContent(self, request_id):
		content = self.data[request_id]['response']['content'] if request_id in self.data else None
		if content:
			return content, self.data[request_id]['response']['content-type']
		return None, None

	def getRequestHeaders(self, request_id):
		return self.data[request_id]['request']['headers'] if request_id in self.data else None

	def getRequestContent(self, request_id):
		return self.data[request_id]['request']['content'] if request_id in self.data else None

	def processRequest(self, op, qrequest, outgoingData = None):
		new_outgoingData = False
		request_id = 0

		# lock access to class resource request_id
		self.mutex_requestid.lock()
		self.request_id +=1
		request_id = self.request_id
		self.__insert_data(request_id, qrequest)
		if request_id not in self.data:
			rewritten_url = None
			if self.netmanager.rewrite_stored_url:
				rewritten_url = self.netmanager.urlrewriting.rewrite(qrequest.url())

			qurlstr = NetworkHistory.__url_str(qrequest.url())
			headers = qrequest.rawHeaderList()
			self.qurlstr_requestid[qurlstr] = request_id

			self.data[request_id] = {
				'type' : getHTTPMethodString(op),
				'request' : {'url' : qrequest.url(), 'headers' : [(h, qrequest.rawHeader(h)) for h in headers], 'content-QByteArray' : None,'content' : None, 'cookies' : None, 'url_rewrite' : rewritten_url, 'redirected_from' : None},
				'response' : {'error' : None, 'headers' : [], 'content-QByteArray' : None, 'content' : None, 'secure' : False, 'status' : None, 'redirect' : None}
			}

			if request_id > 1 and qurlstr in self.last_redirections:
				self.data[request_id]['request']['redirected_from'] = self.last_redirections[qurlstr]
				del self.last_redirections[qurlstr]

			# add the cookies if they exist
			cookies = self.netmanager.cookieJar().cookiesForUrl(qrequest.url())
			if len(cookies):
				self.data[request_id]['request']['cookies'] = cookies

			if outgoingData:
				if not outgoingData.isReadable():
					outgoingData.open(QIODevice.ReadOnly)
				d = outgoingData.readAll()
				self.data[request_id]['request']['content-QByteArray'] = d
				self.data[request_id]['request']['content'] = QBuffer(self.data[request_id]['request']['content-QByteArray'])
				new_outgoingData = True
		self.mutex_requestid.unlock()

		return op, qrequest, self.data[request_id]['request']['content'] if new_outgoingData else None

	def storeReplyContent(self, request_id, buffer):
		if request_id in self.data and buffer and 0 < len(buffer):
			self.data[request_id]['response']['content'] = buffer
			content_type = str(self.data[request_id]['response']['content-type'])

			# has an active monitor plugin that matches the conntent-type?
			monitors = core.management.plugins.getActivatedPluginsGeneric('Python', 'monitor', content_type)
			if 0 < len(monitors):
				plugin_url = unqtify_string(self.data[request_id]['request']['url'].toString())
				plugin_request = prepare_plugin_headers(self.data[request_id]['request']['headers'])
				plugin_response = prepare_plugin_headers(self.data[request_id]['response']['headers'])
				plugin_buffer = unqtify_string(buffer)
				for puid in monitors:
					plugin_info = core.management.plugins.getPluginData(puid, 'Python')
					if plugin_info:
						# call the plugin.process url, request, response, content
						try:
							plugin_info['instance'].process(plugin_url, plugin_request, plugin_response, content_type, plugin_buffer)
						except Exception, error:
							core.management.logger.exception("Error raised from the plugin %s on URL %s (Exception: %s))" % (plugin_info['puid'], plugin_url, error))

	def processReply(self, qreply):
		request_id = self.__lookup_data(qreply.request())
		if request_id and request_id in self.data:
			# extract headers
			headers = qreply.rawHeaderList()
			status = qreply.attribute(QNetworkRequest.HttpStatusCodeAttribute).toString()
			secure = qreply.attribute(QNetworkRequest.ConnectionEncryptedAttribute).toString()
			redirect = NetworkHistory.__url_str(qreply.attribute(QNetworkRequest.RedirectionTargetAttribute).toString())
			if 1 > len(redirect):
				redirect = None
			else:
				self.last_redirections[redirect] = request_id
			# Might store the page content... if needed at some point
			self.data[request_id]['response'] = {'error' : None, 'headers' : [(h, qreply.rawHeader(h)) for h in headers], 'content' : None, 'secure' : secure, 'status' : status, 'redirect' : redirect, 'content-type' : qreply.header(QNetworkRequest.ContentTypeHeader).toString()}
		return qreply, request_id

class POSTHistory:
	__unique = None
	def __init__(self):
		if POSTHistory.__unique:
			raise POSTHistory.__unique
		POSTHistory.__unique = self
		# just a URL -> list of POST data
		self.history = {}

	def renew(self):
		self.history = {}

	def getPOSTList(self, url):
		if url in self.history:
			return self.history[url]['l']
		return None

	def getQBuffer(self, url):
		if url in self.history:
			return self.history[url]['b']
		return None

	def makePost(self, post_data, url):
		if not post_data:
			return None
		postQueryStringURL = QUrl("http://sheep")
		if isinstance(post_data, QIODevice):
			d = post_data.readAll()
			postQueryStringURL.setEncodedQuery(d)
		elif isinstance(post_data, list) or isinstance(post_data, tuple):
			postQueryStringURL.setQueryItems(post_data)
		elif isinstance(post_data, QByteArray):
			postQueryStringURL.setEncodedQuery(QString(post_data).toAscii())
		else:
			raise Exception("Unhandled POST data format for POSTHistory, type = %s" % str(type(post_data)))

		self.history[url] = {'q' : QByteArray(postQueryStringURL.encodedQuery()), 'b' : None, 'l' : postQueryStringURL.queryItems()}
		self.history[url]['b'] = QBuffer(self.history[url]['q'])
		return self.history[url]['q']


# overload the default network manager to implement the data tampering
# methods
class NetworkAccessManager(QNetworkAccessManager):
	__unique = None
	def __init__(self):
		if NetworkAccessManager.__unique:
			raise NetworkAccessManager.__unique
		NetworkAccessManager.__unique = self
		QNetworkAccessManager.__init__(self)

		self.requestTokensInfo = None
		self.proxy_instance = QNetworkProxy(QNetworkProxy.NoProxy)

		# overloaded 'finished' signal so that we can store them in the history
		self.finished[QNetworkReply].connect(self.finished_overload)

		# setup network disk cache directoru (./user/cache)
		self.diskCache = QNetworkDiskCache()
		self.diskCache.setCacheDirectory(core.management.configuration['path']['cache'])
		self.setCache(self.diskCache)

		self.sheepURI = QUrl.fromLocalFile(core.management.configuration['path']['resources']).toString()

		# history model keeps all transaction in memory
		self.history = NetworkHistory(self.diskCache, self)
		self.post_history = POSTHistory()
		self.appinfo = SiteInfoStore(self)

		self.rewrite_stored_url = False
		self.urlrewriting = URLRewritingStore()

		# did we enable tampering data? if so, what is the tampering method
		self.tampering = False
		self.tampering_method = None
		self.intercept = False
		self.disable_referer = False

		# set the personnal cookie jar
		if not core.management.cookieJar:
			core.management.cookieJar = QNetworkCookieJar()
			self.setCookieJar(core.management.cookieJar)

		# store the SSL certificates
		self.sslCfg = QSslConfiguration.defaultConfiguration()
		sslCa = self.sslCfg.caCertificates()
		sslNew = QSslCertificate.fromPath(core.management.configuration['path']['certificates'])
		sslCa +=sslNew
		self.sslCfg.setCaCertificates(sslCa)
		QSslConfiguration.setDefaultConfiguration(self.sslCfg)

		QObject.connect(self, SIGNAL("authenticationRequired(QNetworkReply*, QAuthenticator*)"), self.authenticationRequired_Slot)

	def renew(self):
		#self.history.renew()
		#self.post_history.renew()
		#self.appinfo.renew()
		#self.urlrewriting.renew()
		self.rewrite_stored_url = False

	def setRequestTokensInfoReference(self, requestTokenInfoInstance):
		self.requestTokensInfo = requestTokenInfoInstance

	def getHistoryFromURL(self, qurlstr):
		return self.history.getHistoryFromURL(qurlstr)

	def setIntercept(self, value):
		self.intercept = value
		self.emit(SIGNAL('networkManagerIntercept_Signal'), self.intercept)

	def toggleIntercept(self):
		self.intercept = not self.intercept
		self.emit(SIGNAL('networkManagerIntercept_Signal'), self.intercept)

	def setURLRewriting(self, value = True):
		self.rewrite_stored_url = value

	def toggleDisableReferer(self):
		self.disable_referer = not self.disable_referer

	def getDiskCache(self):
		return self.diskCache

	def setProxy_Slot(self, proxy_type, host=None, port=None, user=None, password=None):
		self.proxy_instance = QNetworkProxy()
		if not QNetworkProxy.NoProxy == proxy_type:
			self.proxy_instance.setType(proxy_type)
			self.proxy_instance.setHostName(host)
			self.proxy_instance.setPort(int(port))
			self.proxy_instance.setUser(user)
			self.proxy_instance.setPassword(password)
		else:
			self.proxy_instance.setType(QNetworkProxy.NoProxy)
		self.setProxy(self.proxy_instance)

	def getNetworkHistory(self, request_id):
		return self.history.getHistory(request_id)

	def getNetworkRequestIDFromURL(self, qurlstr):
		return self.history.getRequestIDFromURL(qurlstr)

	def getResponseContent(self, request_id):
		return self.history.getResponseContent(request_id)

	def getCookieJar(self):
		return self.cookieJar()

	def finished_overload(self, qreply):
		url = qreply.request().url()
		if url.toString().contains(self.sheepURI):
			return qreply
		qreply, request_id = self.history.processReply(qreply)

		# query the cache to get the download content by this request
		data = self.diskCache.data(url)
		if data:
			self.history.storeReplyContent(request_id, data.readAll())
			if self.tampering:
				self.emit(SIGNAL('networkManagerInspectContent'), request_id)
			data.reset()

		# emit the request_id for the HTTP transactions view widget
		self.emit(SIGNAL('availableNetworkReply_Signal'), request_id)
		self.emit(SIGNAL('newUrl_Signal'), request_id)
		self.appinfo.extractSiteInfo(request_id)
		return qreply

	def createRequest(self, op, req, outgoingData = None):
		if req.url().toString().contains(self.sheepURI):
			return QNetworkAccessManager.createRequest(self, op, req, outgoingData)

		# TODO: further test if the user-agent isn't already set in the request
		# TODP: check for conflicts with existing user-agent from Qt
		req.setRawHeader("User-Agent", core.management.__default_user_agent__)

		if self.disable_referer:
			if req.hasRawHeader("Referer"):
				req.setRawHeader("Referer", "")
			elif req.hasRawHeader("Referrer"):
				req.setRawHeader("Referrer", "")

		# allow all tampering happening here
		if self.tampering and self.tampering_method:
			# automated tampering. last action should be replacement of tokens
			op, req, outgoingData = self.tampering_method(op, req, outgoingData)

		# interception code here, after the automated tampering to let flexibility
		# to the pen-tester
		if self.intercept:
			loc_url = req.url()
			try:
				outgoingDataList = None
				if outgoingData:
					self.post_history.makePost(outgoingData, loc_url)
					outgoingDataList = self.post_history.getPOSTList(loc_url)
				tamper_dialog = core.dialog.http_tamper.HTTPTamperDialog(self, op, req, outgoingDataList, core.management.maininstance)
				if tamper_dialog.exec_() == QDialog.Accepted:
					nrequest = tamper_dialog.getHTTPRequest()
					if nrequest:
						op, req, outgoingDataByteArray = nrequest.networkRequest()
						self.emit(SIGNAL('linkTampered_NetManager'), req.url())
						if outgoingDataByteArray:
							self.post_history.makePost(outgoingDataByteArray, loc_url)
							outgoingData = self.post_history.getQBuffer(loc_url)
			except Exception, error:
				core.management.logger.exception("NetworkManager::createRequest- Exception during the request interception handling. (Exception: " + error + ")")

		# prefer getting data from cache when possible
		req.setAttribute(QNetworkRequest.CacheLoadControlAttribute, QNetworkRequest.PreferCache)
		op, req, new_outgoingData = self.history.processRequest(op, req, outgoingData)

		return QNetworkAccessManager.createRequest(self, op, req, new_outgoingData)

	def createHTTPRequest(self, data):
		if isinstance(data, HTTPRequest):
			op, req, post = request.networkRequest()
			self.emit(SIGNAL('browserMakeForgedRequest'), op, req, post)
		else:
			try:
				cookies, post = None, None
				request = HTTPRequest()
				if isinstance(data, int):
					dct = self.history.getHistory(data)
					data = {}
					data['method'] = dct['type']
					data['url'] = dct['request']['url']
					data['headers'] = dct['request']['headers']
					data['post'] = dct['request']['content-QByteArray']
					data['cookies'] = dct['request']['cookies']
				# fill data in the HTTPRequest
				request.setMethod(data['method'])
				request.setUrl(data['url'])
				request.setHeaders(data['headers'])
				# set tampered cookies in the current cookiejar
				if data['cookies']:
					request.setCookies(data['cookies'])
					self.cookieJar().setCookiesFromUrl(request.getQtCookies(), request.url)
				# process and store the POST data using post_history structure
				if data['post']:
					request.setData(data['post'])
				op, req, post = request.networkRequest()
				self.emit(SIGNAL('browserMakeForgedRequest'), op, req, post)
			except Exception, error:
				core.management.logger.exception("NetworkManager::createHTTPrequest- Error while replicating the HTTP request (Exception: %s)" % error)

	# define the tampering method coming from 'testing module'
	def setTamperingMethod(self, method = None):
		if method:
			self.tampering = True
			self.tampering_method = method
		else:
			self.tampering = False
			self.tampering_method = None

	def authenticationRequired_Slot(self, reply, auth):
		core.management.logger.debug("Authentication needed for accessing the website: %s" % (reply.url().toString()))
		from core.dialog.authentication import Authentication
		authentication = Authentication(core.management.maininstance, reply)

		if authentication.exec_() == QDialog.Accepted:
			auth.setUser(authentication.usernameInput.text())
			auth.setPassword(authentication.passwordInput.text())

	def save(self):
		core.management.logger.debug("NetworkManager::save- Save isn't implemented yet for the network manager")
		pass
