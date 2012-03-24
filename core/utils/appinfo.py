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
import os, sys

from PySide.QtCore import *
from PySide.QtNetwork import *

import core.network
from core.utils.domain import extract_domain
from core.utils.mimes import probe_mime


# define a global container for the application structure
# this olds URL (w/o query string) -> different parameters
class SiteInfoStore(QObject):
	__unique = None
	def __init__(self, netmanager):
		if SiteInfoStore.__unique:
			raise SiteInfoStore.__unique
		SiteInfoStore.__unique = self
		QObject.__init__(self)
		self.netmanager = netmanager

		# heuristics inspect the content of the returned by a URl to retrive links, GET/POST parameters, etc.
		self.heuristics = False
		self.heurisitcsImpl = []

		# user interaction
		# domain {
		#  url-string {
		#    request_id {
		#      [url, origin (mouse, keyboard, etc.), buffer, followedLink, element]
		self.interaction = {}

		# domain {
		#  url-string {
		#  'method' : []
		#  'request_id' : []
		#  'original' : True if user clicked on link or if link was directly requested
		#               False if it's a subsequent request
		#  'tampered' : True if user tampered this request once... will help to extract
		#               the coverage of pen-test
		#  'spidered' : True if spider discovered the link
		#  'content-type' : [image, xml, html, js, css, flash, binary, etc.]
		#  'get' : { '$PARAMETER_NAME$' :  []}
		#  'post' : { '$PARAMETER_NAME$' :  []}
		#  'headers' : { '$PARAMETER_NAME$' :  []}
		#  'cookies' : { '$PARAMETER_NAME$' :  [('value', 'raw')]}
		#  'fragment' : []
		#  'comment' : Info if this is coming from a plugin or something...
		# } }
		self.db = {}
		self.last_request_id = -1
		# domain -> {last original request ID, list of original request ID}
		self.original_requests = {}
		self.linkClicked = []
		self.linkTampered = []
		self.linkSpidered = []
		self.findingURLs = {}

	def renew(self):
		self.heuristics = False
		self.heurisitcsImpl = []
		self.db = {}
		self.last_request_id = -1
		self.original_requests = {}
		self.linkClicked = []
		self.linkTampered = []
		self.linkSpidered = []
		self.findingURLs = {}

	def newFindingForURL(self, qurlstr):
		if qurlstr not in self.findingURLs:
			self.findingURLs[qurlstr] = True

	def hasFindingForURL(self, qurlstr):
		return qurlstr in self.findingURLs

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	def linkRequested_Slot(self, url):
		url = SiteInfoStore.__url_str(url)
		if url not in self.linkClicked:
			self.linkClicked.append(url)

	def linkTampered_Slot(self, url):
		url = SiteInfoStore.__url_str(url)
		if url not in self.linkTampered:
			self.linkTampered.append(url)

	def linkSpidered_Slot(self, url):
		url = SiteInfoStore.__url_str(url)
		if url not in self.linkSpidered:
			self.linkSpidered.append(url)

	def addSpideredURL(self, url, comment):
		qurlstr = SiteInfoStore.__url_str(url)
		domain = extract_domain(qurlstr)
		if domain not in self.db:
			self.db[domain] = {}
		if qurlstr not in self.db[domain]:
			self.db[domain][qurlstr] = {'method' : ['GET'], 'request_id' : [], 'original' : None, 'tampered' : None, 'spidered' : True,
										'content-type' : [], 'headers': {}, 'get' : {}, 'post' : {},
										'cookies' : {}, 'fragment' : [], 'redirected_from' : {}, 'comment' : comment}
		else:
			self.db[domain][qurlstr]['spidered'] = True
			if self.db[domain][qurlstr]['comment']:
				self.db[domain][qurlstr]['comment'] = self.db[domain][qurlstr]['comment'] + ", " + comment
			else:
				self.db[domain][qurlstr]['comment'] = comment
		if qurlstr not in self.linkSpidered:
			self.linkSpidered.append(qurlstr)

		# Do not update the AFG
		# self.emit(SIGNAL('appInfoStored'), domain, qurlstr, None)


	# Store the user interaction on a given page
	def storeUserInteractionData_Slot(self, eventOrigin, currentFrameUrl, elmtXPath, buffer, linkFollowedUrl):
		qurlstr = SiteInfoStore.__url_str(currentFrameUrl)
		request_id = self.netmanager.getNetworkRequestIDFromURL(qurlstr)
		domain = extract_domain(qurlstr)
		if domain not in self.interaction:
			self.interaction[domain] = {}
		if qurlstr not in self.interaction[domain]:
			self.interaction[domain][qurlstr] = {}
		if request_id not in self.interaction[domain][qurlstr]:
			self.interaction[domain][qurlstr][request_id] = []

		linkFollowedUrl = linkFollowedUrl if not linkFollowedUrl.isEmpty() else None
		buffer = buffer if 0 < len(buffer) else None

		data = {'url' : currentFrameUrl, 'origin' : eventOrigin, 'element' : elmtXPath, 'buffer' : buffer, 'followedLink' : linkFollowedUrl}
		self.interaction[domain][qurlstr][request_id].append(data)
		self.emit(SIGNAL('newUserInteractionData'), domain, qurlstr, request_id, eventOrigin, buffer, linkFollowedUrl, elmtXPath)

	@staticmethod
	def __insert_pair(d, name, value):
		if name not in d:
			d[name] = []
		if value not in d[name]:
			d[name].append(value)

	@staticmethod
	def __query_items_from_string(rts):
		qurl = QUrl("http://sheep")
		qurl.setEncodedQuery(rts)
		return qurl.queryItems()

	# return the full entry for qurlstr in domain
	def getInfo(self, domain, qurlstr):
		return self.db[domain][qurlstr] if domain in self.db and qurlstr in self.db[domain] else None

	# return a full entry as long as the request_id is in the request_id list
	def getInfoByRequestID(self, domain, request_id):
		if not request_id:
			return None, None
		if domain not in self.db:
			return None
		for qurlstr in self.db[domain]:
			if request_id in self.db[domain][qurlstr]['request_id']:
				return self.db[domain][qurlstr], qurlstr

	def extractSiteInfo(self, request_id):
		info = self.netmanager.getNetworkHistory(request_id)
		if not info:
			core.management.logger.error("SiteInfoStore: The request ID %s doesn't have any entry in the network history database" % str(request_id))
			return
		# store latest request_id
		if self.last_request_id < request_id:
			self.last_request_id = request_id

		qurl = info['request']['url']
		qurlstr = SiteInfoStore.__url_str(qurl)
		domain = extract_domain(qurlstr)

		if domain not in self.db:
			self.db[domain] = {}
		if qurlstr not in self.db[domain]:
			self.db[domain][qurlstr] = {'method' : [], 'request_id' : [], 'original' : None, 'tampered' : None, 'spidered' : None,
										'content-type' : [], 'headers': {}, 'get' : {}, 'post' : {},
										'cookies' : {}, 'fragment' : [], 'redirected_from' : {}, 'comment' : None}
		if request_id not in self.db[domain][qurlstr]['request_id']:
			self.db[domain][qurlstr]['request_id'].append(request_id)
		self.db[domain][qurlstr]['tampered'] = qurlstr in self.linkTampered
		self.db[domain][qurlstr]['spidered'] = qurlstr in self.linkSpidered

		transitive_clicked = False
		if info['request']['redirected_from']:
			req = info['request']['redirected_from']
			redir_info = self.netmanager.getNetworkHistory(req)
			if redir_info:
				transitive_clicked = True
				redir_qurlstr = SiteInfoStore.__url_str(redir_info['request']['url'])
				if redir_qurlstr not in self.db[domain][qurlstr]['redirected_from']:
					self.db[domain][qurlstr]['redirected_from'][redir_qurlstr] = req

		if qurlstr in self.linkClicked or transitive_clicked:
			self.db[domain][qurlstr]['original'] = True
			if domain not in self.original_requests:
				self.original_requests[domain] = {'last_request_id' : request_id, 'originals' : []}
			if request_id not in self.original_requests[domain]['originals']:
				self.original_requests[domain]['originals'].append(request_id)
			# store the latest original request id
			if request_id > self.original_requests[domain]['last_request_id']:
				self.original_requests[domain]['last_request_id'] = request_id

		# store the fragment
		fragment = qurl.fragment()
		if len(fragment) and fragment not in self.db[domain][qurlstr]['fragment']:
			self.db[domain][qurlstr]['fragment'].append(fragment)

		for h in info['request']['headers']:
			SiteInfoStore.__insert_pair(self.db[domain][qurlstr]['headers'], h[0], h[1])

		for h in info['response']['headers']:
			if str(h[0]).lower() == "content-type":
				content_type = probe_mime(str(h[1]).lower())
				if content_type not in self.db[domain][qurlstr]['content-type']:
					self.db[domain][qurlstr]['content-type'].append(content_type)

		queryItems = qurl.queryItems()
		if 0 < len(queryItems):
			for e in queryItems:
				SiteInfoStore.__insert_pair(self.db[domain][qurlstr]['get'], e[0], e[1])

		post = info['request']['content-QByteArray']
		if post and 0 < len(post):
			queryItems = SiteInfoStore.__query_items_from_string(post)
			for e in queryItems:
				SiteInfoStore.__insert_pair(self.db[domain][qurlstr]['post'], e[0], e[1])

		cookies = info['request']['cookies']
		if cookies and 0 < len(cookies):
			for e in cookies:
				SiteInfoStore.__insert_pair(self.db[domain][qurlstr]['cookies'], e.name(), e.value())

		self.emit(SIGNAL('appInfoStored'), domain, qurlstr, request_id)

	def clear(self):
		self.db = {}
