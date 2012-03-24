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
import re, os, time

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtWebKit import *
from PySide.QtNetwork import *


import core.management

from core.utils.domain import extract_domain
from core.utils.jsonify import jsonify_headers

url_np_regexp = re.compile("([^/\s]+\.[\w:\d]+)(.*)", re.I)
url_regexp = re.compile("([^/]+):///?([^/]+)(.*)", re.I)
url_var = re.compile("(\?|&)([^ = ]+)")
class URLSyntaxHighlighter(QSyntaxHighlighter):
	"""Syntax highlighter for the URL, this should help the user to see
	important information just by the color"""
	def __init__(self, document = None):
		QSyntaxHighlighter.__init__(self, document)

		self.domainFormat = QTextCharFormat()
		self.domainFormat.setFontWeight(QFont.Normal)
		self.domainFormat.setForeground(Qt.black)

		self.httpsFormat = QTextCharFormat()
		self.httpsFormat.setFontWeight(QFont.Normal)
		self.httpsFormat.setForeground(Qt.darkGreen)

		self.pathFormat = QTextCharFormat()
		self.pathFormat.setFontWeight(QFont.Normal)
		self.pathFormat.setForeground(Qt.gray)

	def highlightBlock_PartRegExp(self, text, string, format):
		pattern = QRegExp(string)
		index = text.indexOf(pattern)
		while index >= 0:
			length = pattern.matchedLength()
			self.setFormat(index, length, format)
			index = text.indexOf(pattern, index + length)

	def highlightBlock_PartString(self, text, string, format):
		length = len(string)
		index = text.indexOf(string)
		if index >= 0:
			self.setFormat(index, length, format)

	def highlightBlock(self, text):
		t = text
		if url_regexp.match(t):
			out = url_regexp.search(t)
			protocol = out.group(1)
			domain = out.group(2)
			path = out.group(3)
			self.highlightBlock_PartString(text, ":///", self.pathFormat)
			self.highlightBlock_PartString(text, "://", self.pathFormat)
			self.highlightBlock_PartString(text, path, self.pathFormat)
			self.highlightBlock_PartString(text, domain, self.domainFormat)

			vars = url_var.findall(path)
			if len(vars) > 0:
				for v in vars:
					self.highlightBlock_PartString(text, v[1], self.httpsFormat)
			if 'https' in protocol:
				self.highlightBlock_PartString(text, protocol, self.httpsFormat)
				self.emit(SIGNAL('httpsBackground_Signal'))
			else:
				self.highlightBlock_PartString(text, protocol, self.pathFormat)
				self.emit(SIGNAL('whiteBackground_Signal'))
		else:
			self.emit(SIGNAL('searchBackground_Signal'))

class LineEdit(QTextEdit):
	"""personnal line edith for URL bar; inspired from Google Chrome design"""
	def __init__(self):
		QTextEdit.__init__(self)
		#self.c = None
		self.setAcceptRichText(False)
		self.setAutoFormatting(QTextEdit.AutoNone)
		self.setLineWrapMode(QTextEdit.NoWrap)
		self.setAutoFillBackground(True)
		self.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setVerticalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
		self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
		self.setMinimumHeight(25)
		self.setMaximumHeight(25)
		self.eow = QString("~!@#$%^&*()_+{}|:\"<>?,./;'[]\\-= ")

	def keyPressEvent(self, event):
		if event.key() == Qt.Key_Return or event.key() == Qt.Key_Enter:
			self.emit(SIGNAL('returnPressed()'))
		else:
			QTextEdit.keyPressEvent(self, event)

	def setText(self, text):
		QTextEdit.setPlainText(self, text)


class AddressBar(QWidget):
	"""global container for the address bar; completion should come in some time"""
	def __init__(self, parent=None):
		QWidget.__init__(self, parent)

		self.url = LineEdit()
		self.bg_style = "QTextEdit {background-color: rgb(255, 255, 255)}"
		self.size_font = 13
		self.urlFont = QFont("Helvetica", self.size_font, QFont.Light)
		self.metrics = QFontMetrics(self.urlFont)
		QObject.connect(self.url, SIGNAL("returnPressed()"), self.returnPressed_Slot)
		self.url.setFont(self.urlFont)

		self.hlr = URLSyntaxHighlighter(self.url.document())
		QObject.connect(self.hlr, SIGNAL("httpsBackground_Signal"), self.setHttpsBackground_Slot)
		QObject.connect(self.hlr, SIGNAL("whiteBackground_Signal"), self.setWhiteBackground_Slot)
		QObject.connect(self.hlr, SIGNAL("searchBackground_Signal"), self.setSearchBackground_Slot)

		layout = QHBoxLayout()
		layout.addWidget(self.url)
		self.setLayout(layout)

	def modelFromFile(self, filename):
		list = QStringList()
		try:
			o = open(filename, 'r')
			list = o.readlines()
			o.close()
		except IOError:
			core.management.logger.warning("Cannot open the completer database in: %s" % filename)
			return QStringListModel(QStringList(), self.completer)
		return QStringListModel(list, self.completer)

	def adjustFontSizeBar(self):
		width_text = self.metrics.width(self.url.toPlainText())
		widget_width = self.url.width()
		if widget_width <= width_text:
			self.size_font = max(self.size_font - 1, 8)
		else:
			# if size+1 font fits, then use it
			local_metric = QFontMetrics(QFont("Helvetica", self.size_font + 1, QFont.Light))
			next_width = local_metric.width(self.url.toPlainText())
			if next_width <= widget_width:
				self.size_font = min(self.size_font + 1, 13)
		self.urlFont = QFont("Helvetica", self.size_font, QFont.Light)
		self.metrics = QFontMetrics(self.urlFont)
		self.url.setFont(self.urlFont)

	def resizeEvent(self, event):
		self.adjustFontSizeBar()
		QWidget.resizeEvent(self, event)

	def returnPressed_Slot(self):
		self.url.setStyleSheet(self.bg_style)
		self.emit(SIGNAL('returnPressed()'))

	def setHttpsBackground_Slot(self):
		self.bg_style = "QTextEdit {background-color: rgb(255,250,205)}"

	def setWhiteBackground_Slot(self):
		self.bg_style = "QTextEdit {background-color: rgb(255, 255, 255)}"

	def setSearchBackground_Slot(self):
		self.bg_style = "QTextEdit {background-color: rgb(233, 244, 255)}"

	def text(self):
		return self.url.toPlainText()

	def setText(self, text):
		self.url.setText(text)
		self.adjustFontSizeBar()
		self.url.setStyleSheet(self.bg_style)


class Overlay(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.setAttribute(Qt.WA_TransparentForMouseEvents)
		self.helpMsg = None
		self.blocking = False
		self.size_font = 9
		self.helpFont = QFont("Helvetica", self.size_font, QFont.Light)
		self.metrics = QFontMetrics(self.helpFont)

	def paintEvent(self, event):
		if self.helpMsg:
			painter = QPainter(self)
			painter.setRenderHint(QPainter.Antialiasing)
			painter.setPen(QPen(Qt.black))
			painter.setBrush(QBrush(QColor(233, 244, 255, 220))) # 193, 193, 193, 240)))
			painter.drawRoundRect(0, 0, self.metrics.width(self.helpMsg) + 15, self.height(), 2, 2)
			painter.setFont(self.helpFont)
			painter.drawText(self.size_font, self.size_font + self.size_font / 2, self.helpMsg)

	def setHelpMsg(self, msg, blocking = False):
		if blocking:
			self.blocking = not self.blocking
			if self.blocking:
				self.helpMsg = msg
			else:
				self.helpMsg = None
		else:
			self.helpMsg = msg
	def show(self):
		self.setVisible(True)

	def hide(self):
		# should wait a bit before setting invisible...
		self.setVisible(False)

class Communication(QWidget):
	def __init__(self, parent = None):
		QWidget.__init__(self, parent)
		self.setAttribute(Qt.WA_TransparentForMouseEvents)
		self.helpMsg = None
		self.blocking = False
		self.size_font = 9
		self.defaultIcon = QPixmap(core.management.configuration['path']['resources'] + "images/asterisk_orange.png")
		self.helpFont = QFont("Helvetica", self.size_font, QFont.Light)
		self.metrics = QFontMetrics(self.helpFont)

	def paintEvent(self, event):
		if self.helpMsg:
			painter = QPainter(self)
			painter.setRenderHint(QPainter.Antialiasing)
			painter.setPen(QPen(Qt.white))
			painter.setBrush(QBrush(QColor(136, 0, 0, 222)))
			painter.drawRoundRect(0, 0, self.metrics.width(self.helpMsg) + 15, self.height(), 2, 2)
			painter.setFont(self.helpFont)
			painter.drawText(self.size_font, self.size_font + self.size_font / 2, self.helpMsg)
			self.setGeometry(self.width() - self.metrics.width(self.helpMsg) - 45, self.height() + self.metrics.height(), self.width(), self.height())

	def setHelpMsg(self, msg = None, blocking = False):
		if not msg or 1 > len(msg):
			self.hide()
		else:
			self.helpMsg = QString(msg)
			self.show()
			self.repaint()

	def show(self):
		self.setVisible(True)

	def hide(self):
		self.setVisible(False)


class WebView(QWebView):
	def __init__(self, parent = None):
		QWebView.__init__(self, parent)
		self.acc_buffer = ""
		self.cursorCurrentPos = None
		self.sheepURI = QUrl.fromLocalFile(core.management.configuration['path']['resources']).toString()

	def createWindow(self, type):
		if QWebPage.WebBrowserWindow == type:
			self.emit(SIGNAL('setHelpMsg_Signal'), "The application tried to open a new window... ")
			# ask for naviguation on the other site...
			# if yes, replace the
		else:
			self.emit(SIGNAL('setHelpMsg_Signal'), "The application tried to open a popup...")

	@staticmethod
	def __xpath_attributes(elmt, att_selections=(u'id', u'name', u'class')):
		if not elmt.hasAttributes():
			return ""
		attrs = ""
		attributes = elmt.attributeNames()
		for attribute in attributes:
			if unicode(attribute) not in att_selections:
				continue
			attr_condition = '@%s="%s"' % (attribute, elmt.attribute(attribute))
			if 0 < len(attrs):
				attrs = attrs + " and " + attr_condition
			else:
				attrs = attr_condition
		return "[" + attrs + "]" if 0 < len(attrs) else ""

	@staticmethod
	def __webelmt_path(elmt):
		path = ""
		while not elmt.isNull():
			locpath = "/" + elmt.tagName() + WebView.__xpath_attributes(elmt)
			path = locpath + path
			elmt = elmt.parent()
		return path

	def elmtFromPosition(self, eventOrigin="mouse", rts=None):
		currentFrame = self.page().currentFrame()
		if currentFrame and not currentFrame.url().toString().contains(self.sheepURI):
			hitResult = currentFrame.hitTestContent(self.cursorCurrentPos)
			if not hitResult.isNull():
				linkFollowed = hitResult.linkUrl()
				blockElmt, currentElmt = hitResult.enclosingBlockElement(), hitResult.element()
				blockXPath = WebView.__webelmt_path(blockElmt)
				elmtXPath = WebView.__webelmt_path(currentElmt)
				path = blockXPath if 1 > len(elmtXPath) else elmtXPath
				self.emit(SIGNAL('userInteractionData'), eventOrigin, currentFrame.url(), path, self.acc_buffer, linkFollowed)
			else:
				print "No HitTest result..."

	def mousePressEvent(self, mouseEvent):
		pos = mouseEvent.pos()
		self.cursorCurrentPos = pos
		but = mouseEvent.buttons()
		self.elmtFromPosition()
		QWebView.mousePressEvent(self, mouseEvent)

	def clearAccBuffer_Slot(self):
		self.acc_buffer = ""

	def keyPressEvent(self, keyEvent):
		key = keyEvent.key()
		# TODO: handle changed position due to the TAB navigation
		if key in (Qt.Key_Return, Qt.Key_Enter):
			# validate of some sort?!
			self.elmtFromPosition("keyboard", self.acc_buffer)
			self.clearAccBuffer_Slot()
		else:
			self.acc_buffer += keyEvent.text()

		QWebView.keyPressEvent(self, keyEvent)



# dynamically enable or not the monitoring of JavaScript alerts
# or not in the WebPage
class MonitorWebPage(QWebPage):
	def __init__(self, parent = None):
		QWebPage.__init__(self, parent)
		self.testing = False

	def toggleTesting(self):
		self.testing = not self.testing

	def setActiveTesting(self):
		self.testing = True

	def setInactiveTesting(self):
		self.testing = False

	def createWindow(self, windowType):
		self.emit(SIGNAL('createWindow_Signal'), windowType)
		if not self.testing:
			QWebPage.createWindow(self, windowType)

	def javaScriptAlert(self, webframe, msg):
		self.emit(SIGNAL('javascriptAlertEvent_Signal'), msg)
		if not self.testing:
			QWebPage.javaScriptAlert(self, webframe, msg)

	def javaScriptConfirm(self, webframe, msg):
		self.javaScriptAlert(webframe, msg)

	def javaScriptPrompt(self, webframe, msg, value, result):
		if not self.testing:
			QWebPage.javaScriptPrompt(self, webframe, msg, value, result)

	def javaScriptConsoleMessage(self, msg, line, srcId):
		self.emit(SIGNAL('javaScriptConsoleMessage_Signal'), msg, line, srcId)

	def jsAlertsConfiguration_Slot(self, testing, manualTesting):
		self.testing = testing or manualTesting

class DownloadManager(QWidget):
	def __init__(self, networkManager = None, initFile = ""):
		QWidget.__init__(self)
		self.netmanager = networkManager
		self.files = {}
		self.downloaded = []

	def downloadRequested_Slot(self, qrequest):
		orgFileName = QFileInfo(qrequest.url().toString()).fileName()
		filename = QFileDialog.getSaveFileName(self, "Save file as...", orgFileName)
		if filename.isEmpty():
			filename = core.management.configuration['path']['user'] + orgFileName
		if filename.isEmpty():
			today = str(QDateTime.currentDateTime().toString("yyyy-MM-d_hh-mm-ss"))
			filename = core.management.configuration['path']['user'] + 'bsheep-download_%s_.ext' % (today, self.sshort_id)

		nrequest = QNetworkRequest(qrequest)
		nrequest.setAttribute(QNetworkRequest.User, filename)
		self.files[filename] = self.netmanager.get(nrequest)
		QObject.connect(self.files[filename], SIGNAL("finished()"), self.downloadFinished_Slot)

	def downloadFinished_Slot(self):
		self.processDownloadedFiles()

	def processDownloadedFiles(self):
		downloadFileNames = self.files.keys()
		for fname in downloadFileNames:
			if self.files[fname].isFinished():
				# QNetworkReply finished, process to the copy of the file to its destination: fname
				buffer = self.files[fname].readAll()
				file = QFile(fname)
				file.open(QIODevice.WriteOnly)
				file.write(buffer)
				file.close()
				# remove this entry from our dict and add to the list of download file names
				del self.files[fname]
				self.downloaded.append(fname)
				self.emit(SIGNAL("downloadedFile_Signal"), fname)


class WebBrowser(QWidget):
	def __init__(self, networkManager=None, initFile=""):
		QWidget.__init__(self)
		layout = QVBoxLayout()
		addressLayout = QHBoxLayout()

		self.netmanager = networkManager
		self.downloadManager = DownloadManager(self.netmanager)
		# QObject.connect(self.downloadManager, SIGNAL("downloadedFile_Signal"), self.com)

		self.sshort_id = 0
		self.loadingMessage = False
		self.autoDiscovery = False
		self.addressBar = AddressBar(self)
		self.addressLoad = QLabel(self)
		self.addressLoad.setMaximumHeight(25)
		self.addressLoad.setMinimumWidth(60)
		self.animation = QMovie(core.management.configuration['path']['resources'] + "images/ajax-loader.gif")
		self.buttons_map = QPixmap(core.management.configuration['path']['resources'] + "images/tbar.png")
		self.buttons_on,self.buttons_off = {}, {}

		# l0: left right star down clock refresh stop none none print home cut none none none
		# l2: left right refresh stop cut none none
		self.buttons_on['left'] = self.buttons_map.copy(  0, 0,24,24)
		self.buttons_on['right'] = self.buttons_map.copy( 24, 0,24,24)
		self.buttons_on['refresh'] = self.buttons_map.copy(120, 0,24,24)
		self.buttons_on['stop'] = self.buttons_map.copy(144, 0,24,24)

		self.buttons_off['left'] = self.buttons_map.copy(  0, 48,24,24)
		self.buttons_off['right'] = self.buttons_map.copy( 24, 48,24,24)
		self.buttons_off['refresh'] = self.buttons_map.copy( 48, 48,24,24)
		self.buttons_off['stop'] = self.buttons_map.copy( 72, 48,24,24)

		self.toolBar = QToolBar()
		self.toolBar.setStyleSheet("QToolBar {margin:0;border:0;padding:0}")

		self.backAction = QAction(QIcon(self.buttons_off['left']), "Back", self)
		self.backAction.setEnabled (False)
		self.toolBar.addAction(self.backAction)
		self.forwAction = QAction(QIcon(self.buttons_off['right']), "Forward", self)
		self.forwAction.setEnabled(False)
		self.toolBar.addAction(self.forwAction)
		self.reloadAction = QAction(QIcon(self.buttons_on['refresh']), "Refresh", self)
		self.toolBar.addAction(self.reloadAction)
		self.stopAction = QAction(QIcon(self.buttons_off['stop']), "Stop", self)
		self.stopAction.setEnabled(False)
		self.toolBar.addAction(self.stopAction)

		self.toolBar.addWidget(self.addressBar)

		# set the actions
		QObject.connect(self.reloadAction, SIGNAL("triggered()"), self.reloadAction_Slot)
		QObject.connect(self.stopAction,   SIGNAL("triggered()"), self.stopLoading_Slot)

		self.addressLoad.setText(core.management.__release__)
		addressLayout.addWidget(self.toolBar)
		addressLayout.addWidget(self.addressLoad)

		addressLayout.setSizeConstraint(QLayout.SetMinimumSize)

		self.webpage = MonitorWebPage() # QWebPage()
		self.webpage.setNetworkAccessManager(self.netmanager)
		self.webpage.setLinkDelegationPolicy(QWebPage.DelegateAllLinks)
		self.webpage.setForwardUnsupportedContent(True)
		self.web = WebView(self)
		self.web.setPage(self.webpage)

		# web settings
		self.websettings = self.webpage.settings()
		self.websettings.setAttribute(QWebSettings.PluginsEnabled, True)
		self.websettings.setAttribute(QWebSettings.DeveloperExtrasEnabled, True)
		self.websettings.setAttribute(QWebSettings.OfflineStorageDatabaseEnabled, True)
		self.websettings.setAttribute(QWebSettings.OfflineWebApplicationCacheEnabled, True)
		self.websettings.setAttribute(QWebSettings.LocalStorageDatabaseEnabled, True)
		self.websettings.setLocalStoragePath(core.management.configuration['path']['user'] + 'webkit')

		QObject.connect(self.web, SIGNAL("setHelpMsg_Signal"), self.setHelpMsg_Slot)

		layout.addLayout(addressLayout)
		layout.addWidget(self.web)
		self.setLayout(layout)

		self.overlay = Overlay(self)
		self.overlay.setGeometry(-5, self.height(), self.width(), self.height() - 15)

		self.communication = Communication(self)

		QObject.connect(self.addressBar, SIGNAL("returnPressed()"), self.newUrl_Slot)
		QObject.connect(self.webpage, SIGNAL("linkHovered(const QString&, const QString&, const QString&)"), self.setUrlHovered_Slot)
		QObject.connect(self.webpage, SIGNAL("linkClicked(const QUrl&)"), self.linkClicked_Slot)
		QObject.connect(self.webpage, SIGNAL("unsupportedContent(QNetworkReply *)"), self.unsupportedContent)
		QObject.connect(self.webpage, SIGNAL("downloadRequested(const QNetworkRequest&)"), self.downloadManager.downloadRequested_Slot)
		# QObject.connect(self.webpage, SIGNAL("contentsChanged()"), self.web.clearAccBuffer_Slot)
		QObject.connect(self.web, SIGNAL("loadFinished(bool)"), self.loadFinished_Slot)
		QObject.connect(self.web, SIGNAL("loadStarted()"), self.loadStarted_Slot)
		QObject.connect(self.web, SIGNAL("userInteractionData"), self.userInteraction_Slot)
		QObject.connect(self.forwAction, SIGNAL("triggered()"), self.historyForward)
		QObject.connect(self.backAction, SIGNAL("triggered()"), self.historyBack)

		# init
		self.loadFile(initFile)

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		# specifc version of url_str to keep most variants
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment)

	def enableAutoDiscovery(self, enabled=False):
		self.autoDiscovery = enabled

	def execute_plugins(self):
		lplugins = core.management.plugins.getActivatedPlugins('JavaScript')
		if 0 < len(lplugins):
			for puid in lplugins:
				plugin_info = core.management.plugins.getPluginData(puid)
				if plugin_info['json_headers']:
					# JSONify the HTTP request and pass it as 'sheep_headers' in the JavaScript context
					headers = self.netmanager.getHistoryFromURL(WebBrowser.__url_str(self.web.url()))
					if headers:
						self.webpage.mainFrame().evaluateJavaScript(jsonify_headers(headers, 'sheep_headers'))
				for preload_script in plugin_info['load']:
					self.webpage.mainFrame().evaluateJavaScript(preload_script)
				self.webpage.mainFrame().evaluateJavaScript(plugin_info['script-source'])

	def screenShot(self, filename=None):
		# create a full screenshot, output in PNG of the webpage
		painter = QPainter()
		self.webpage.setViewportSize(self.webpage.mainFrame().contentsSize())
		img = QImage(self.webpage.viewportSize(), QImage.Format_ARGB32_Premultiplied)
		painter.begin(img)
		self.webpage.mainFrame().render(painter)
		painter.end()
		# save image output
		self.sshort_id +=1
		if not filename:
			today = str(QDateTime.currentDateTime().toString("yyyy-MM-d_hh-mm-ss"))
			filename = core.management.configuration['path']['user'] + 'bsheep_%s_%d.png' % (today, self.sshort_id)
		img.save(filename, "PNG")

	def userInteraction_Slot(self, eventOrigin, currentFrameUrl, elmtXPath, buffer, linkFollowedUrl):
		self.emit(SIGNAL('userInteractionData'), eventOrigin, currentFrameUrl, elmtXPath, buffer, linkFollowedUrl)

	def unsupportedContent(self, reply):
		core.management.logger.debug("Unsupported content at: %s (mime=%s)" % (unicode(reply.url().toString()), str(reply.rawHeader("Content-Type"))))

	def makeRequest(self, op, qrequest, pdata = None):
		self.emit(SIGNAL('linkTampered_Browser'), qrequest.url())
		self.emit(SIGNAL('linkRequested_Browser'), qrequest.url())
		self.web.load(qrequest, op, QByteArray() if not pdata else pdata)

	def historyBack(self):
		self.emit(SIGNAL('linkRequested_Browser'), self.webpage.history().backItem().url())
		self.webpage.history().back()

	def historyForward(self):
		self.emit(SIGNAL('linkRequested_Browser'), self.webpage.history().forwardItem().url())
		self.webpage.history().forward()

	def setHistory(self):
		if self.webpage.history().canGoBack():
			self.backAction.setIcon(QIcon(self.buttons_on['left']))
			self.backAction.setEnabled(True)
		else:
			self.backAction.setIcon(QIcon(self.buttons_off['left']))
			self.backAction.setEnabled(False)

		if self.webpage.history().canGoForward():
			self.forwAction.setIcon(QIcon(self.buttons_on['right']))
			self.forwAction.setEnabled(True)
		else:
			self.forwAction.setIcon(QIcon(self.buttons_off['right']))
			self.forwAction.setEnabled(False)

	def setSSLErrors_Slot(self, reply, errors):
		raise Exception("SSL Errors: %s" % str(errors))

	def resizeEvent(self, event):
		QWidget.resizeEvent(self, event)
		self.overlay.setGeometry(-5, self.height() - 15, self.width(), self.height() - 30)
		self.communication.setGeometry(self.width() - 30, self.height() - 15, self.width()+30, self.height() - 30)
		self.repaint()

	def prepareHelpMsg(self):
		self.overlay.setGeometry(-5, self.height() - 15, self.width(), self.height() - 30)

	def finishHelpMsg(self):
		self.repaint()
		self.overlay.repaint()
		self.communication.repaint()

	def setHelpMsg(self, msg, blocking=False):
		self.prepareHelpMsg()
		self.overlay.setHelpMsg(msg, blocking)
		self.finishHelpMsg()

	def setCommunicationMsg(self, msg):
		self.communication.setHelpMsg(msg)

	def setUrlHovered_Slot(self, link, title, content):
		self.setHelpMsg(QString(link))
		if link.length() < 1 and not self.loadingMessage:
			self.overlay.hide()
		else:
			self.overlay.show()

	def setHelpMsg_Slot(self, msg):
		self.setHelpMsg(msg)

	def evaluateJS_Slot(self, s):
		# evaluate on the page the source code...
		self.webpage.mainFrame().evaluateJavaScript(s)

	def getJavaScriptValue_Slot(self, s):
		return self.webpage.mainFrame().evaluateJavaScript(s)

	def loadStarted_Slot(self):
		self.stopAction.setIcon(QIcon(self.buttons_on['stop']))
		self.stopAction.setEnabled(True)
		# self.addressLoad.setScaledContents(True)
		self.addressLoad.setMovie(self.animation)
		self.animation.start()

	def guessUrlFromEntry(self, url, engine='http://google.com/search?q = '):
		if 'www' in url[:3] or url_np_regexp.match(url):
			return 'http://' + url
		elif 'about:' in url:
			if 'inspector' in url:
				self.inspect()
			return core.management.configuration['path']['resources'] + 'start.html'
		return engine + url

	def linkClicked_Slot(self, url):
		self.addressBar.setText(url.toString())
		self.loadUrl(url)

	def newUrl_Slot(self):
		# guess the URL if not std mode
		url = str(self.addressBar.text())
		if not url_regexp.match(url):
			url = self.guessUrlFromEntry(url)
		if 'http' not in url[:4] and './resources' in url:
			# should be a file
			self.addressBar.setText(QUrl.fromLocalFile(os.path.abspath(url)).toString())
			self.web.load(QUrl.fromLocalFile(os.path.abspath(url)))
		else:
			self.addressBar.setText(QString(url))
			self.loadUrl(self.addressBar.text())

	def loadUrl(self, url):
		if not isinstance(url, QUrl):
			url = QUrl(url)
		self.loadStarted_Slot()
		self.setHelpMsg("Loading %s..." % (url.toString()))
		self.loadingMessage = True
		self.overlay.show()
		self.emit(SIGNAL('linkRequested_Browser'), url)
		self.web.load(url)

	def setPage_Slot(self, page):
		self.web.setPage(page)

	def setHTMLSource(self, html):
		self.web.setHtml(html, self.web.url())

	def loadFile(self, filename):
		html = ""
		try:
			html = open(filename, 'r').read()
			html = html.replace('$NAME_VERSION$', core.management.__release__)
			html = html.replace('$APP_PATH$', core.management.configuration['path']['resources'])
		except IOError:
			pass
		self.web.setHtml(html, QUrl.fromLocalFile(os.path.abspath(filename)))

	def inspect(self):
		return self.web.triggerPageAction(QWebPage.InspectElement, True)

	def stopLoading_Slot(self):
		self.web.stop()
		self.loadFinished_Slot()

	def reloadAction_Slot(self):
		self.emit(SIGNAL('linkRequested_Browser'), self.web.url())
		self.web.reload()
		self.stopAction.setEnabled(True)
		self.stopAction.setIcon(QIcon(self.buttons_on['stop']))

	def getElementAttribute(self, webelement, tag, attribute):
		ret = []
		findings = webelement.findAll(tag)
		for i in xrange(findings.count()):
			find = findings.at(i)
			if find.hasAttribute(attribute):
				value = find.attribute(attribute)
				if value not in ret:
					ret.append(value)
		return ret

	@staticmethod
	def correctURL(url, current_url, domain, scheme):
		if '#' == url[0]:
			return None
		elif '/' == url[0]:
			return unicode(QUrl(scheme + '://' + domain + url).toString())
		elif './' == url[0:2]:
			return unicode(QUrl(current_url + url[1:]).toString())
		elif scheme not in url:
			if 'javascript:' == url[:11]:
				return None
			return unicode(QUrl(scheme + '://' + domain + '/' + url).toString())
		return url

	def loadFinished_Slot(self):
		self.overlay.hide()
		self.loadingMessage = False
		self.setHistory()
		self.animation.stop()
		self.stopAction.setIcon(QIcon(self.buttons_off['stop']))
		self.stopAction.setEnabled(False)
		self.addressLoad.setText(core.management.__release__)
		self.addressBar.setText (self.web.url().toString())
		self.emit(SIGNAL('newHTMLSource_Signal'), self.webpage.mainFrame().toHtml())
		self.emit(SIGNAL('newDOM_Signal'), self.webpage.mainFrame().documentElement())

		if self.autoDiscovery:
			# if the URL auto discovery has been enabled, we will scan the page to get the URL (definitely flawed)
			temp_found_urls, found_urls = [], []
			web_elmt = self.webpage.currentFrame().documentElement()

			for tag in ('a', 'link', 'base', 'area'):
				temp_found_urls += self.getElementAttribute(web_elmt, tag, 'href')
			for tag in ('script', 'style', 'embed', 'frame', 'iframe', 'video', 'audio', 'source', 'input'):
				temp_found_urls += self.getElementAttribute(web_elmt, tag, 'src')

			current_url = self.web.url()
			current_scheme = current_url.scheme()
			current_domain = extract_domain(current_url)
			current_url = unicode(current_url.toString())

			for url in temp_found_urls:
				url = WebBrowser.correctURL(url, current_url, current_domain, current_scheme)
				if url and url not in found_urls:
					found_urls.append(url)

			# register everything to the appinfo, show notification?
			for url in found_urls:
				self.netmanager.appinfo.addSpideredURL(url, "URL found by BlackSheep auto-discovery")

		self.execute_plugins()
