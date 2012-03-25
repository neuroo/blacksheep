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

import re, sys
from PyQt4.QtCore import *
from core.utils.domain import extract_domain

"""
	Store the URL rewriting rule

	ex:
		RewriteRule ^page/([^/\.]+)/([^/\.]+)/?$ index.php?page = $1 [L]
		match = ^/page/([^/\.]+)/([^/\.]+)/?$
		replace = index.php?page = \\1&subpage = \\2
"""
class URLRewritingStore:
	def __init__(self):
		self.urlr_id = 0
		self.store = {}

	def renew(self):
		self.urlr_id = 0
		self.store = {}

	def hasDomain(self, domain):
		return domain in self.store

	@staticmethod
	def __prepare(match):
		try:
			return re.compile(match, re.U)
		except Exception, error:
			return None

	def statusRule(self, domain, urlr_id, status = False):
		if not self.hasDomain() or urlr_id not in self.store[domain]:
			return False
		self.store[domain][urlr_id]['active'] = status

	def updateValues(self, domain, urlr_id, match, replace, status):
		if not self.hasDomain(domain) or urlr_id not in self.store[domain]:
			return False
		if not isinstance(match, unicode):
			match = unicode(match)
		if not isinstance(replace, unicode):
			replace = unicode(replace)
		self.store[domain][urlr_id] = {'active' : status, 'match' : match, 'replace' : replace, 'regexp' :  URLRewritingStore.__prepare(match)}
		return True

	def addRule(self, domain, match, replace, active = False):
		if domain not in self.store:
			self.store[domain] = {}
		if not isinstance(match, unicode):
			match = unicode(match)
		if not isinstance(replace, unicode):
			replace = unicode(replace)
		self.urlr_id +=1
		urlr_id = self.urlr_id
		self.store[domain][urlr_id] = {'active' : active, 'match' : match, 'replace' : replace, 'regexp' :  URLRewritingStore.__prepare(match)}

	def removeRule(self, domain, urlr_id):
		if not self.hasDomain(domain) or urlr_id not in self.store[domain]:
			return False
		del self.store[domain][urlr_id]
		return True

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	@staticmethod
	def __modified_components(resultant):
		qurl = QUrl("http://sheep.com/" + resultant)
		return qurl.path(), qurl.encodedQuery()

	# convert URL to unicode string
	# apply modification if necessary and return the new URL as QUrl
	def rewrite(self, qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		domain = extract_domain(URLRewritingStore.__url_str(qurl))
		if not self.hasDomain(domain):
			return qurl
		original_path = unicode(qurl.path())
		upath = None
		original_query = str(qurl.encodedQuery())
		for urlr_id in self.store[domain]:
			if self.store[domain][urlr_id]['active'] and self.store[domain][urlr_id]['regexp'].match(original_path):
				upath = self.store[domain][urlr_id]['regexp'].sub(self.store[domain][urlr_id]['replace'], original_path)
				if upath != original_path:
					break
		new_path, new_query = URLRewritingStore.__modified_components(upath)
		qurl.setPath(new_path)
		qurl.setEncodedQuery(str(original_query) + str("&" + new_query) if 0 < len(new_query) else "")
		return qurl

"""
test_url = QUrl("http://sheep.com/page/foo/bar")
domain = extract_domain(test_url)
path = test_url.path()
store = URLRewritingStore()
store.addRule(domain, "^/page/([^/\.]+)/([^/\.]+)/?$", "index.php?page = \\1&subpage = \\2", True)
print store.rewrite(test_url)
sys.exit()
"""
