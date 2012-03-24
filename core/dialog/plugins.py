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
import os

from PySide.QtCore import *
from PySide.QtGui import *

import core.management

class PluginManagement(QDialog):
	def __init__(self, parent = None):
		QDialog.__init__(self, parent)

		self.pluginstore = core.management.plugins
		self.plugin_types = []

		self.plugin_enabled_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/plugin.png')
		self.plugin_disabled_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/plugin_disabled.png')
		self.folder_icon = QIcon(core.management.configuration['path']['resources'] + 'images/icons/folder.png')

		self.tree = QTreeWidget()
		self.tree.setColumnCount(4)
		self.tree.setRootIsDecorated(False)
		self.tree.setAlternatingRowColors(True)
		self.tree.setSortingEnabled(True)
		self.tree.setEditTriggers(QAbstractItemView.DoubleClicked)
		self.tree.setHeaderLabels(["Name", "Author", "Directory", "PUID"])
		self.tree.setUniformRowHeights(True)
		self.tree.setColumnHidden(3, True)
		for i in range(3):
			self.tree.resizeColumnToContents(i)
		self.tree.setWordWrap(True)
		self.updateTree()
		QObject.connect(self.tree, SIGNAL('itemClicked(QTreeWidgetItem *, int)'), self.selectedPlugin_Slot)

		self.plugin_info = QTextEdit()
		self.plugin_info.setTextInteractionFlags(Qt.LinksAccessibleByMouse | Qt.TextSelectableByMouse | Qt.TextSelectableByKeyboard)

		layout = QVBoxLayout()
		layout.addWidget(QLabel("List of plugins registered in BlackSheep.\nClick on the plugin icon to activate/deactivate the plugin"))
		layout.addWidget(self.tree)
		layout.addWidget(self.plugin_info)

		self.setModal(False)
		self.setLayout(layout)
		self.setMinimumSize(520,300)
		self.resize(600,400)

	@staticmethod
	def __createitem(plugin, icon_active, icon_inactive):
		item = QTreeWidgetItem()
		item.setText(0, QString(plugin['name']))
		item.setIcon(0, icon_active if plugin['active'] else icon_inactive)
		item.setText(1, QString(plugin['author']['name'] if 'name' in plugin['author'] else ""))
		item.setText(2, QString(os.path.dirname(plugin['script'])))
		item.setText(3, QString(plugin['puid']))
		return item

	@staticmethod
	def __create_treeseparator(name, icon = None):
		bgColor = QColor(0, 0, 255, 25)
		if not isinstance(name, QString):
			name = QString(name)
		item = QTreeWidgetItem()
		if icon:
			item.setIcon(0, icon)
		item.setText(0, name)
		for i in range(4):
			item.setBackgroundColor(i, bgColor)
		return item

	def updateTree(self):
		self.plugin_types = self.pluginstore.getPluginTypes()
		self.plugin_types.sort(reverse = True)

		self.tree.clear()
		self.tree.setUpdatesEnabled(False)

		for plugin_type in self.plugin_types:
			category_item = PluginManagement.__create_treeseparator(plugin_type, self.folder_icon)
			self.tree.invisibleRootItem().addChild(category_item)
			for puid in self.pluginstore.getPlugins(plugin_type):
				plugin = self.pluginstore.getPluginData(puid, plugin_type)
				category_item.addChild(PluginManagement.__createitem(plugin, self.plugin_enabled_icon, self.plugin_disabled_icon))

		self.tree.expandAll()
		for i in range(3):
			self.tree.resizeColumnToContents(i)
		self.tree.setUpdatesEnabled(True)

	def selectedPlugin_Slot(self, item, col):
		if item and item.text(3):
			puid = str(item.text(3))
			if 0 == col:
				status = self.pluginstore.togglePlugin(puid)
				item.setIcon(0, self.plugin_enabled_icon if status else self.plugin_disabled_icon)

			self.plugin_info.clear()
			self.plugin_info.setHtml(QString(self.pluginstore.prepareDescription(puid)))

	def accept_Slot(self):
		self.accept()

	def cancel_Slot(self):
		self.reject()
