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
import sys, os, re

from PyQt4.QtCore import *
from PyQt4.QtGui import *
from PyQt4.QtWebKit import *
from PyQt4.Qsci import *

import core.management
from core.utils.domain import extract_domain

# try to get the type of icon needed by the element (token)
def probe_icon(token, last = False, forced = None):
	res = core.management.configuration['path']['resources']
	token = str(token).lower()
	if forced:
		if forced == 'domain':
			return res + 'images/icons/world.png'
		elif forced == 'host':
			return res + 'images/icons/connect.png'
	else:
		if '.' not in token:
			if not last:
				return res + 'images/icons/folder.png'
			else:
				return res + 'images/icons/page_white.png'
		else:
			if not last:
				return res + 'images/icons/folder.png'
			# else, get the type
			extension = token[token.rfind('.')+1:]
			if extension in ('png','gif','jpg','jpeg','bmp'):
				return res + 'images/icons/image.png'
			elif extension in ('mpg','mpeg','avi','divx','swf','mov'):
				return res + 'images/icons/film.png'
			elif extension in ('mp3','wav','ogg','flac'):
				return res + 'images/icons/music.png'
			return res + 'images/icons/page_white.png'
	return res + 'images/icons/page_white.png'


REGEXP_TEXT_CONTENT = re.compile(r'.*(html|script|css|xml|text).*', re.I)

# Container displays the different type of elements depending on their type:
# - text: scintilla
# - images: iamge viewer + hex
# - binary: hex
# - others: web browser
#
# TODO: implement hex viewer
#
class DisplayContainer(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.scintilla = QsciScintilla()
		lexer = QsciLexerHTML(self.scintilla)
		self.scintilla.setLexer(lexer)
		self.scintilla.setReadOnly(True)
		self.scintilla.setMarginLineNumbers(1, True)
		self.scintilla.setMarginWidth(1, 45)
		self.scintilla.setWrapMode(QsciScintilla.WrapWord)
		self.scintilla.setBraceMatching(QsciScintilla.SloppyBraceMatch)
		self.scintilla.setFolding(QsciScintilla.BoxedTreeFoldStyle)
		fsize = 8 if 'win32' == sys.platform else 10

		for sty in range(128):
			if not lexer.description(sty).isEmpty():
				f = lexer.font(sty)
				f.setFamily('courier new')
				f.setPointSize(fsize)
				lexer.setFont(f, sty)

		self.pan = QWebView(self)
		self.page = QWebPage()
		self.websettings = self.page.settings()
		self.websettings.setAttribute(QWebSettings.PluginsEnabled, True)
		self.websettings.setAttribute(QWebSettings.DeveloperExtrasEnabled, False)
		self.page.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
		self.page.setForwardUnsupportedContent(True)
		self.pan.setPage(self.page)
		self.pan.load(QUrl.fromLocalFile(os.path.abspath(core.management.configuration['path']['resources'] + 'sitemap.html')))

		layout = QVBoxLayout()
		layout.addWidget(self.scintilla)
		layout.addWidget(self.pan)
		self.setLayout(layout)

		# default view is with the web browser
		self.scintilla.hide()

	def dispatchContent(self, content, content_type):
		# probe display depending on content type
		if REGEXP_TEXT_CONTENT.match(content_type):
			# dispatch to scintilla
			self.scintilla.setText(QString(content))
			self.scintilla.show()
			self.pan.hide()
		else:
			self.pan.setContent(content, content_type)
			self.pan.show()
			self.scintilla.hide()

	def dispatchWebContent(self, url):
		self.pan.load(url)
		self.pan.show()
		self.scintilla.hide()


class Sitemap(QWidget):
	"""display the visited websites as a tree"""
	def __init__(self, netmanager, parent = None):
		QWidget.__init__(self, parent)
		self.map = {}
		self.netmanager = netmanager
		self.tree = QTreeWidget()
		self.configureTree()
		QObject.connect(self.tree, SIGNAL('itemClicked(QTreeWidgetItem *, int)'), self.selectedItem_Slot)

		self.display = DisplayContainer()

		self.splitter = QSplitter()
		self.splitter.addWidget(self.tree)
		self.splitter.addWidget(self.display)

		layout = QVBoxLayout()
		layout.addWidget(self.splitter)
		self.setLayout(layout)

	def renew(self):
		self.tree.clear()

	def selectedItem_Slot(self, item, column):
		rid_str = str(item.text(1))
		if 0 < len(rid_str):
			request_id = int(str(item.text(1)))
			info = self.netmanager.getNetworkHistory(request_id)
			qurl = info['request']['url']
			content = info['response']['content']
			if not content:
				self.display.dispatchWebContent(qurl)
			else:
				content_type = None
				for h in info['response']['headers']:
					if "content-type" == str(h[0]).lower():
						content_type = str(h[1]).lower()
				self.display.dispatchContent(content, content_type)
		else:
			# backtrack to display the URL?
			names = []
			while item:
				names.append(str(item.text(0)))
				item = item.parent()
			names = names[::-1]
			self.display.dispatchWebContent(QUrl('http://' + '/'.join(names[1:])))

	def configureTree(self):
		self.tree.setColumnCount(2)
		self.tree.setColumnHidden(1, True)
		self.tree.setSortingEnabled(False)
		self.tree.setHeaderLabels(["Remote site structure", "Request ID"])

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	def addTreeItem(self, request_id):
		info = self.netmanager.getNetworkHistory(request_id)
		if not info:
			core.management.logger.error("Sitempa::addTreeItem- The request_id %s is not accessible at this time" % str(request_id))
			return
		qurl = info['request']['url']
		scheme = str(qurl.scheme())
		if scheme not in ('http', 'https'):
			return
		host, port, query = qurl.host(), qurl.port(), qurl.queryItems()
		path, domain = qurl.path(), extract_domain(Sitemap.__url_str(qurl))

		domain_item, path_item = None, None
		# find the proper domain node or create it
		if domain not in self.map:
			self.map[domain] = {}
			domain_item = QTreeWidgetItem()
			domain_item.setText(0, domain)
			domain_item.setIcon(0, QIcon(probe_icon(None, None, 'domain')))
			self.map[domain]['item'] = domain_item
			self.tree.addTopLevelItem(domain_item)
		else:
			domain_item = self.map[domain]['item']

		# find the host
		if host not in self.map[domain]:
			self.map[domain][host] = {}
			host_item = QTreeWidgetItem()
			host_item.setText(0, host)
			host_item.setIcon(0, QIcon(probe_icon(None, None, 'host')))
			# if no path this was the request page
			if str(path) in ('', '/'):
				host_item.setText(1, QString(str(request_id)))
			domain_item.addChild(host_item)
			self.map[domain][host]['item'] = host_item
		else:
			host_domain = self.map[domain][host]['item']

		length = len(path)
		if length > 0:
			if path[0] == '/':
				path = path[1:]
				length -= 1
			if length > 1 and path[length-1] == '/':
				path = path[:length-1]
			paths = path.split('/')
			d = self.map[domain][host]
			cur, prev = None, self.map[domain][host]['item']
			length, i = len(paths), 0
			for elmt in paths:
				i +=1
				if len(elmt) < 1:
					continue
				elif elmt not in d:
					d[elmt] = {'item' : QTreeWidgetItem()}
					d[elmt]['item'].setText(0, elmt)
					d[elmt]['item'].setIcon(0, QIcon(probe_icon(elmt, i == length)))
					if i == length:
						d[elmt]['item'].setText(1, QString(str(request_id)))
					cur = d[elmt]['item']
					prev.addChild(cur)
					prev = cur
					d = d[elmt]
				else:
					d[elmt]['item'].setIcon(0, QIcon(probe_icon(elmt, i == length)))
					if i == length:
						d[elmt]['item'].setText(1, QString(str(request_id)))
					prev = d[elmt]['item']
					d = d[elmt]
