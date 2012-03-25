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
import sys

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import core.interface.browser

import core.dialog.urlrewriting
import core.dialog.plugins
import core.dialog.proxy

import core.widgets.code
import core.widgets.tamper
import core.widgets.javascript
import core.widgets.sitemap
import core.widgets.toolkit
import core.widgets.console
import core.widgets.findings
import core.widgets.testing
import core.widgets.appstackmap
import core.widgets.testcases
import core.widgets.siteinfo

import core.utils.useragent as ua
import core.management

from core.plugins.broker import PluginBroker


class MainWindow(QMainWindow):
	def __init__(self, parent = None):
		QMainWindow.__init__(self, parent)

		# NetBrowser instanciante the network manager
		# central place for all the network communication, tampering, etc.
		self.net = core.widgets.tamper.NetBrowser()

		# rest of widgets
		self.code = core.widgets.code.CodeBrowser()
		self.site = core.widgets.sitemap.Sitemap(self.net.manager)
		self.appstackmap = core.widgets.appstackmap.ApplicationStackMap()

		self.findings = core.widgets.findings.Findings(self.net.manager)
		core.management.findingdb = self.findings.findingsdb

		self.sheepTesting = core.widgets.testing.SheepTesting(self.net.manager)
		self.siteinfo = core.widgets.siteinfo.SiteInfo(self.net.manager.appinfo)
		self.testcases = core.widgets.testcases.TestCases(self.net.manager)
		self.pluginBroker = PluginBroker(self.net.manager, core.management.plugins, self.findings.findingsdb)

		self.web = core.interface.browser.WebBrowser(self.net.manager, "./resources/start.html")

		QObject.connect(self.findings, SIGNAL('forceTabSwitchedTo'), self.switchTabWidget)
		QObject.connect(self.findings, SIGNAL('newFindingForURL'), self.siteinfo.newFindingForURL_Slot)
		QObject.connect(self.sheepTesting, SIGNAL('addFinding_Signal'), self.findings.populateFinding_Slot)
		QObject.connect(self.web.webpage, SIGNAL('javascriptAlertEvent_Signal'), self.sheepTesting.probeJSEvent)
		QObject.connect(self.web, SIGNAL('linkRequested_Browser'), self.net.manager.appinfo.linkRequested_Slot)
		QObject.connect(self.web, SIGNAL('linkTampered_Browser'), self.net.manager.appinfo.linkTampered_Slot)
		QObject.connect(self.web, SIGNAL('userInteractionData'), self.net.manager.appinfo.storeUserInteractionData_Slot)

		QObject.connect(self.net.manager, SIGNAL('linkTampered_NetManager'), self.net.manager.appinfo.linkTampered_Slot)
		QObject.connect(self.net.manager.appinfo, SIGNAL('appInfoStored'), self.siteinfo.appInfoAvailable_Slot)
		QObject.connect(self.net.manager.appinfo, SIGNAL('newUserInteractionData'), self.testcases.userInteractionInfoAvailable_Slot)

		QObject.connect(self.sheepTesting, SIGNAL("setTamperingMethod_Signal"), self.net.manager.setTamperingMethod)
		QObject.connect(self.sheepTesting, SIGNAL("testingInProgress_Signal"), self.web.setCommunicationMsg)
		QObject.connect(self.sheepTesting, SIGNAL("jsAlertsConfiguration_Signal"), self.web.webpage.jsAlertsConfiguration_Slot)
		QObject.connect(self.code.display , SIGNAL('scintillaTextChanged'), self.web.setHTMLSource)

		self.toolKit = core.widgets.toolkit.ToolKit()
		self.tamperingData = core.widgets.tamper.TamperingData(self.net.manager)
		self.jsEval = core.widgets.javascript.JSEvaluator()
		self.console = core.widgets.console.Console()

		self.list_widgets = [self.net, self.code, self.testcases, self.site, self.appstackmap, self.findings, self.toolKit, self.tamperingData, self.jsEval, self.console]

		# transmit site info selected request ID to tamper data dock widget
		QObject.connect(self.siteinfo, SIGNAL("siteInfoLoadRequestIDInTamperData"), self.tamperingData.setRequestResponse_Slot)
		# create a new HTTP request
		QObject.connect(self.tamperingData, SIGNAL('createHTTPRequest'), self.net.manager.createHTTPRequest)
		QObject.connect(self.net.manager, SIGNAL('browserMakeForgedRequest'), self.web.makeRequest)
		QObject.connect(self.net.manager, SIGNAL('networkManagerIntercept_Signal'), self.updateInterceptStatus_Slot)
		QObject.connect(self.sheepTesting.tamperUtility, SIGNAL("consoleLogMessage_Signal"), self.console.addConsole_Slot)
		QObject.connect(self.web, SIGNAL("newHTMLSource_Signal"), self.code.setText_Slot) # HTML code emission
		QObject.connect(self.web, SIGNAL("newDOM_Signal"), self.code.setDOM_Slot) # HTML code emission
		QObject.connect(self.web, SIGNAL("titleChanged(QString)"), self.setTitle_Slot)
		# Transfer info from request
		QObject.connect(self.net, SIGNAL("updateDocTamperView_Signal"), self.tamperingData.setRequestResponse_Slot)
		# QObject.connect(self.net, SIGNAL('sslErrors(const QList<QSslError> &errors)'), self.web.setSSLErrors_Slot) # Transfer info from request
		# propagate the Site map items
		QObject.connect(self.net.manager, SIGNAL("newUrl_Signal"), self.site.addTreeItem)

		QObject.connect(self.net, SIGNAL('addRequestIDtoFindings_Signal'), self.findings.addFromRequestID_Slot)
		QObject.connect(self.net, SIGNAL('addRequestIDtoTestCases_Signal'), self.testcases.addFromRequestID_Slot)
		QObject.connect(self.tamperingData, SIGNAL('addRequestIDtoFindings_Signal'), self.findings.addFromRequestID_Slot)
		QObject.connect(self.tamperingData, SIGNAL('addRequestIDtoTestCases_Signal'), self.testcases.addFromRequestID_Slot)

		self.tabWidget = QTabWidget(self)
		self.tabWidget.addTab(self.web, QIcon(core.management.configuration['path']['resources'] + 'images/icons/world.png'), "Web Browser")
		self.tabWidget.addTab(self.code, QIcon(core.management.configuration['path']['resources'] + 'images/icons/page_white_code.png'), "HTML Source Views")
		self.tabWidget.addTab(self.net , QIcon(core.management.configuration['path']['resources'] + 'images/icons/database_table.png'), "HTTP History")
		self.tabWidget.addTab(self.siteinfo, QIcon(core.management.configuration['path']['resources'] + 'images/icons/map.png'), "Application Flow Graph")
		self.tabWidget.addTab(self.findings, QIcon(core.management.configuration['path']['resources'] + 'images/icons/bug.png'), "Security Findings")
		self.tabWidget.addTab(self.testcases, QIcon(core.management.configuration['path']['resources'] + 'images/icons/cog.png'), "Test Cases Repository")
		self.tabWidget.addTab(self.site, QIcon(core.management.configuration['path']['resources'] + 'images/icons/sitemap_color.png'), "Site Structure")
		# self.tabWidget.addTab(self.appstackmap , "Application Stack Discovery")

		self.tabswitching_dict = {
			'findings' : self.findings,
			'browser' : self.web,
			'code' : self.code,
			'flowgraph' : self.siteinfo
		}
		QObject.connect(self.tabWidget, SIGNAL('currentChanged(int)'), self.checkChangedTextinCodeView_Slot)

		# configuration of the docks
		self.setDockOptions(QMainWindow.AnimatedDocks)#ForceTabbedDocks)

		# dockable JS evaluator
		self.dockJs = QDockWidget(self.tr("JavaScript Console"), self)
		self.dockJs.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
		self.dockJs.setWidget(self.jsEval)
		self.addDockWidget(Qt.BottomDockWidgetArea, self.dockJs, Qt.Horizontal)
		QObject.connect(self.jsEval, SIGNAL("evalJavaScript_Signal"), self.web.evaluateJS_Slot)
		QObject.connect(self.jsEval, SIGNAL("getJavaScript_Signal"), self.web.getJavaScriptValue_Slot)

		# dockable ToolKit
		self.dockTool = QDockWidget(self.tr("Encoding toolkit"), self)
		self.dockTool.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
		self.dockTool.setWidget(self.toolKit)
		self.tabifyDockWidget(self.dockJs, self.dockTool)

		# dockable Console
		self.dockConsole = QDockWidget(self.tr("Sheep Console"), self)
		self.dockConsole.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
		self.dockConsole.setWidget(self.console)
		self.tabifyDockWidget(self.dockTool, self.dockConsole)

		# dockable Sheep testing
		self.dockTesting = QDockWidget(self.tr("Sheep Testing"), self)
		self.dockTesting.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
		self.dockTesting.setWidget(self.sheepTesting)
		self.tabifyDockWidget(self.dockConsole, self.dockTesting)

		# dockable HTTP Request/Response
		self.dockTamper = QDockWidget(self.tr("Tampering Data"), self)
		self.dockTamper.setAllowedAreas(Qt.LeftDockWidgetArea | Qt.RightDockWidgetArea | Qt.BottomDockWidgetArea | Qt.TopDockWidgetArea)
		self.dockTamper.setWidget(self.tamperingData)
		self.tabifyDockWidget(self.dockTesting, self.dockTamper)

		self.setCentralWidget(self.tabWidget)
		self.setMinimumSize(520,480)
		self.resize(1200, 800)
		self.showMaximized()
		self.setWindowIcon(QIcon(core.management.configuration['path']['resources'] + 'images/sheep_head.png'))
		self.setTitle('Oops! I did it again...')

		# actions
		self.exitAction, self.toolboxAction, self.aboutAction, self.helpAction = None, None, None, None
		self.showDockAction, self.tamperAction, self.contextAction, self.parserAction = None, None, None, None
		self.inspectAction, self.interceptRequest, self.urlRewritingAction, self.pluginsAction = None, None, None, None
		self.proxyAction, self.newAction, self.saveFindings = None, None, None
		self.autoURLDiscovery = None

		# shortcut actions
		self.ctrlU_sourcecodeAction, self.ctrlL_urlAction = None, None

		self.uaActionGroup, self.uaDict = None, {}

		# menus
		self.menubar = None
		self.fileMenu, self.optionMenu, self.toolboxMenu, self.helpMenu, self.useragentMenu = None, None, None, None, None
		self.knowledgeMenu = None

		self.createActions()
		self.createMenus()

	def switchTabWidget(self, widgetname):
		if widgetname in self.tabswitching_dict:
			self.tabWidget.setCurrentWidget(self.tabswitching_dict[widgetname])

	def newWorkspace_Slot(self):
		core.management.logger.debug("MainWindow::newWorkspace_Slot- Not implemented yet")
		#for w in self.list_widgets:
		#	if hasattr(w, 'renew'):
		#		w.renew()


	def saveStateObject_Slot(self):
		self.findings.save()
		self.net.manager.save()

	def checkChangedTextinCodeView_Slot(self, index):
		if index == self.tabWidget.indexOf(self.web):
			# currenct tab active is the browser tab, check for changed text in the code view...
			if self.code.display.text_modified:
				# gather the text,
				self.web.setHTMLSource(self.code.display.scintilla.text())
				self.code.display.text_modified = False

	def setTitle_Slot(self, string):
		self.setTitle(string)

	def setTitle(self, string):
		self.setWindowTitle(core.management.__release__ + ' - ' + string)

	def createActions(self):
		self.newAction = QAction("&New Workspace", self)
		self.saveFindings = QAction("E&xport Findings", self)
		self.exitAction = QAction("&Exit", self)
		self.aboutAction = QAction("&About", self)
		self.helpAction = QAction("&Help", self)
		self.userAgent = QAction("&User-Agents", self)

		self.showDockAction = QAction("Show &Dock", self)
		self.showDockAction.setCheckable(True)
		self.showDockAction.setChecked(True)
		self.inspectAction = QAction("&Inspect", self)
		self.proxyAction = QAction("Configure &Proxy", self)
		self.urlRewritingAction = QAction("&URL Rewriting Specification...", self)
		self.interceptRequest = QAction("HTTP Requests Interception", self)
		self.interceptRequest.setCheckable(True)
		self.disableReferer = QAction("Disable Referer", self)
		self.disableReferer.setCheckable(True)
		self.screenshotAction = QAction("&Take Screenshot", self)

		self.autoURLDiscovery = QAction("Enable URL extractions", self)
		self.autoURLDiscovery.setCheckable(True)
		self.autoURLDiscovery.setChecked(False)

		self.pluginsAction = QAction('&Plugins...', self)
		self.contextAction = QAction('&Contexts Extractions', self)
		self.parserAction = QAction('&Languages Parsers', self)

		self.ctrlU_sourcecodeAction = QShortcut(QKeySequence("Ctrl+U"), self)
		self.ctrlL_urlAction = QShortcut(QKeySequence("Ctrl+L"), self)

		QObject.connect(self.autoURLDiscovery, SIGNAL('triggered()'), self.autoURLDiscovery_Slot)
		QObject.connect(self.newAction, SIGNAL("triggered()"), self.newWorkspace_Slot)
		QObject.connect(self.saveFindings, SIGNAL("triggered()"), self.saveFindings_Slot)
		QObject.connect(self.screenshotAction, SIGNAL("triggered()"), self.screenshot_Slot)
		QObject.connect(self.exitAction, SIGNAL("triggered()"), self.close)
		QObject.connect(self.aboutAction, SIGNAL("triggered()"), self.about_Slot)
		QObject.connect(self.helpAction, SIGNAL("triggered()"), self.help_Slot)
		QObject.connect(self.showDockAction, SIGNAL("triggered()"), self.showDock_Slot)
		QObject.connect(self.proxyAction, SIGNAL("triggered()"), self.proxy_Slot)
		QObject.connect(self.urlRewritingAction, SIGNAL("triggered()"), self.urlRewrite_Slot)
		QObject.connect(self.inspectAction, SIGNAL("triggered()"), self.inspect_Slot)
		QObject.connect(self.interceptRequest, SIGNAL("triggered()"), self.intercept_Slot)
		QObject.connect(self.disableReferer, SIGNAL("triggered()"), self.disableReferer_Slot)

		QObject.connect(self.pluginsAction, SIGNAL("triggered()"), self.plugins_Slot)
		QObject.connect(self.contextAction, SIGNAL("triggered()"), self.context_Slot)
		QObject.connect(self.parserAction, SIGNAL("triggered()"), self.parser_Slot)

		QObject.connect(self.ctrlU_sourcecodeAction, SIGNAL("activated()"), self.focusCode_Slot)
		QObject.connect(self.ctrlL_urlAction, SIGNAL("activated()"), self.focusUrl_Slot)


	def autoURLDiscovery_Slot(self):
		self.web.enableAutoDiscovery(self.autoURLDiscovery.isChecked())

	def focusUrl_Slot(self):
		self.switchTabWidget('browser')
		self.web.addressBar.url.setFocus(Qt.OtherFocusReason)

	def focusCode_Slot(self):
		self.switchTabWidget('code')

	def createMenus(self):
		# Create menubar
		self.menubar = self.menuBar()
		self.fileMenu = self.menubar.addMenu('&File')
		self.optionMenu = self.menubar.addMenu('&Options')
		self.toolboxMenu = self.menubar.addMenu('&Toolbox')
		#self.knowledgeMenu = self.menubar.addMenu('&Knowledge')
		self.helpMenu = self.menubar.addMenu('&Help')

		self.fileMenu.addAction(self.newAction)
		self.fileMenu.addAction(self.saveFindings)
		self.fileMenu.addAction(self.exitAction)

		self.optionMenu.addAction(self.showDockAction)
		self.optionMenu.addAction(self.disableReferer)
		self.optionMenu.addAction(self.proxyAction)
		self.optionMenu.addAction(self.urlRewritingAction)
		self.optionMenu.addAction(self.pluginsAction)
		self.optionMenu.addAction(self.autoURLDiscovery)

		self.toolboxMenu.addAction(self.interceptRequest)
		self.toolboxMenu.addAction(self.screenshotAction)

		self.useragentMenu = self.toolboxMenu.addMenu('&User-Agent')
		# loop in user agents
		self.uaActionGroup = QActionGroup(self.useragentMenu)
		for ua_key in ua.user_agent:
			self.uaDict[ua_key] = QAction(QString(ua_key), self)
			self.uaDict[ua_key].setCheckable(True)
			if 'Sheep' == ua_key:
				self.uaDict[ua_key].setChecked(True)
			self.uaActionGroup.addAction(self.uaDict[ua_key])
		self.useragentMenu.addActions(self.uaActionGroup.actions())
		QObject.connect(self.uaActionGroup, SIGNAL("triggered(QAction *)"), self.setUserAgent_Slot)

		#self.knowledgeMenu.addAction(self.contextAction)
		#self.knowledgeMenu.addAction(self.parserAction)

		self.helpMenu.addAction(self.aboutAction)
		self.helpMenu.addAction(self.helpAction)


	def saveFindings_Slot(self):
		orgFileName = core.management.configuration['path']['user'] + 'findings.xml'
		filename = QFileDialog.getSaveFileName(self, "Save file as...", orgFileName, "Findings format (*.xml, *.html)")
		if filename.isEmpty():
			filename = None
		self.findings.exportAs(filename)

	def screenshot_Slot(self):
		orgFileName = core.management.configuration['path']['user'] + 'screenshot.png'
		filename = QFileDialog.getSaveFileName(self, "Save file as...", orgFileName)
		if filename.isEmpty():
			filename = None
		self.web.screenShot(filename)

	def setUserAgent_Slot(self, action):
		core.management.set_useragent(action.text())

	def about_Slot(self):
		pass

	def help_Slot(self):
		pass

	def showDock_Slot(self):
		if self.showDockAction.isChecked():
			self.showDock()
		else:
			self.hideDock()

	def disableReferer_Slot(self):
		self.net.manager.toggleDisableReferer()

	def intercept_Slot(self):
		self.net.manager.toggleIntercept()

	def updateInterceptStatus_Slot(self, status):
		self.interceptRequest.setChecked(status)

	def urlRewrite_Slot(self):
		urlrewrite_dialog = core.dialog.urlrewriting.URLRewritingDialog(self.net.manager, self)
		if urlrewrite_dialog.exec_() == QDialog.Accepted:
			return

	def plugins_Slot(self):
		plugins_dialog = core.dialog.plugins.PluginManagement(self)
		plugins_dialog.exec_()
		# execute new plugins on current page...
		self.web.execute_plugins()

	def proxy_Slot(self):
		proxy_dialog = core.dialog.proxy.ProxyDialog(self.net.manager, self)
		if proxy_dialog.exec_() == QDialog.Accepted:
			return

	def context_Slot(self):
		pass

	def parser_Slot(self):
		pass

	def inspect_Slot(self):
		self.web.inspect()

	def closeEvent(self, event):
		pass

	def showDock(self):
		self.restoreDockWidget(self.dockJs)
		self.restoreDockWidget(self.dockTool)
		self.restoreDockWidget(self.dockTamper)
		self.restoreDockWidget(self.dockConsole)
		self.restoreDockWidget(self.dockTesting)

	def hideDock(self):
		# by default hide the dockwidget
		self.removeDockWidget(self.dockJs)
		self.removeDockWidget(self.dockTool)
		self.removeDockWidget(self.dockTamper)
		self.removeDockWidget(self.dockConsole)
		self.removeDockWidget(self.dockTesting)
