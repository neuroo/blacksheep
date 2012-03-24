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
import math, sys
from random import random

from pygraph.classes.digraph import digraph
from pygraph.algorithms.cycles import find_cycle
from pygraph.algorithms.accessibility import mutual_accessibility

from PySide.QtCore import *
from PySide.QtGui import *
from PySide.QtOpenGL import *

from core.utils.layout import Layout
from core.widgets.component.graphics import *

import core.management

# TODO: implement different layouts
LIST_LAYOUT = ["Random"]

LIST_HEURISTICS = {
	"Highlight secure (HTTPS) paths" : 'SECURE_PATHS',
	"Highlight cycles" : 'CYCLES'
}

class GraphView(QGraphicsView):
	def __init__(self, appinfo, parent = None):
		QGraphicsView.__init__(self, parent)
		self.appinfo = appinfo

		# TODO: need to fix that sometimes
		self.areaSize = self.viewport().size()
		self.viewWidth = self.areaSize.width()
		self.viewHeight = self.areaSize.height()

		self.apply_selected_heuristic = False
		self.selected_heuristic = None

		self.contextmenu = QMenu()
		self.heuristicsMenu = self.contextmenu.addMenu("Heuristics...")
		self.heuristicsMenu.setIcon(QIcon(core.management.configuration['path']['resources'] + "images/icons/wand.png"))
		self.dictActions = {}
		self.heuristicsGroup = QActionGroup(self.heuristicsMenu)

		none_heuristics = "None"
		self.dictActions[none_heuristics] = QAction(none_heuristics, self)
		self.dictActions[none_heuristics].setCheckable(True)
		self.dictActions[none_heuristics].setChecked(True)
		self.heuristicsGroup.addAction(self.dictActions[none_heuristics])

		DK_LIST_HEURISTICS = LIST_HEURISTICS.keys()
		DK_LIST_HEURISTICS.sort()
		for list_heuristics in DK_LIST_HEURISTICS:
			self.dictActions[list_heuristics] = QAction(QString(list_heuristics), self)
			self.dictActions[list_heuristics].setCheckable(True)
			self.dictActions[list_heuristics].setChecked(False)
			self.heuristicsGroup.addAction(self.dictActions[list_heuristics])
		self.heuristicsMenu.addActions(self.heuristicsGroup.actions())
		QObject.connect(self.heuristicsGroup, SIGNAL("triggered(QAction *)"), self.setSelectedHeuristics_Slot)

		# makes use of OpenGL if on windows...
		if 'win32' == sys.platform:
			self.setViewport(QGLWidget())
		else:
			core.management.logger.debug("GraphView::__init__- No GL support for the platform: %s" % str(sys.platform))

		self.scene = GraphicsScene(self)
		self.scene.setItemIndexMethod(QGraphicsScene.NoIndex)
		self.scene.setSceneRect(-self.viewWidth // 2, - self.viewHeight // 2, self.viewWidth, self.viewHeight)
		self.setScene(self.scene)
		QObject.connect(self.scene, SIGNAL('selectionChanged()'), self.itemSelectionChanged_Slot)

		self.layout = Layout(self.scene)

		self.setCacheMode(QGraphicsView.CacheBackground)
		self.setViewportUpdateMode(QGraphicsView.BoundingRectViewportUpdate)
		self.setRenderHints(QPainter.Antialiasing  | QPainter.SmoothPixmapTransform)
		self.setTransformationAnchor(QGraphicsView.AnchorUnderMouse)
		self.setResizeAnchor(QGraphicsView.AnchorViewCenter)
		self.setDragMode(QGraphicsView.ScrollHandDrag)

		self.highlight_edges = []
		self.activedomain = None
		self.application_only = True
		self.scale_factor = 1
		# domain -> nodes
		self.nodes = {}
		self.nodes_rid = {} # fast lookup provider for request_id -> node
		self.uid_rid, self.rid_uid = {}, {}
		self.graphs = {}
		self.redir_edges = {} # holds the redirected_from uid for a domain (domain > uid > redirection_uid)
		self.scale(1., 1.)


	def setFilterTypes(self, filter):
		self.scene.filterElements(filter)

	def setSelectedHeuristics_Slot(self, action):
		checkedAction = str(self.heuristicsGroup.checkedAction().text())
		if "None" == checkedAction:
			self.selected_heuristic = None
		else:
			self.selected_heuristic = checkedAction
		self.executeHeuristic()

	def contextMenuEvent(self, event):
		self.contextmenu.exec_(event.globalPos())
		QGraphicsView.contextMenuEvent(self, event)

	def renew(self):
		self.nodes = {}
		self.nodes_rid = {}
		self.uid_rid, self.rid_uid = {}, {}
		self.graphs = {}
		self.scene.newScene()
		self.clear()

	def setActiveDomain(self, activedomain):
		self.activedomain = activedomain

	def setTypeDisplayed(self, application_only = True):
		self.application_only = application_only

	def itemMoved(self):
		pass

	# TODO: record previous position of the mouse and translate based on dx, dy
	def mouseMoveEvent(self, mouseEvent):
		self.translate(mouseEvent.pos().x(), mouseEvent.pos().y())
		QGraphicsView.mouseMoveEvent(self, mouseEvent)

	def wheelEvent(self, event):
		self.scaleView(math.pow(2.0, event.delta() / 750.0))

	def scaleView(self, scale_factor):
		self.scale_factor = scale_factor
		factor = self.matrix().scale(scale_factor, scale_factor).mapRect(QRectF(0, 0, 1, 1)).width()
		if factor < 0.1 or factor > 50:
			return
		self.scale(scale_factor, scale_factor)

	def resizeEvent(self, event):
		self.areaSize = self.viewport().size()
		self.viewWidth = self.areaSize.width()
		self.viewHeight = self.areaSize.height()
		self.scene.setSceneRect(-self.viewWidth // 2, - self.viewHeight // 2, self.viewWidth, self.viewHeight)
		QGraphicsView.resizeEvent(self, event)

	@staticmethod
	def __probe_type(info_node):
		# prioritize the type of node:
		# vulnerable type is updated a posteriori
		# tampered > original > spidered > default
		names = ('tampered', 'original', 'spidered')
		for property in names:
			if info_node[property]:
				return property
		return 'default'

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	@staticmethod
	def __display_url(url):
		if not isinstance(url, QUrl):
			url = QUrl(url)
		path = url.path()
		if 1 > len(path):
			return GraphView.__url_str(url)
		return path

	def itemSelectionChanged_Slot(self):
		if self.scene:
			try:
				selected_items = self.scene.selectedItems()
				
				# O2- Grabber
				sys.stdout.write("O2::CMD- %s\n" % (selected_items[0].info[1]))
				sys.stdout.flush()
				
				length_selection = len(selected_items)
				if 0 < length_selection:
					self.emit(SIGNAL('updateDetailsNodePan'), selected_items[length_selection - 1].info)
			except Exception, error:
				return

	@staticmethod
	def __randomPos(width, height):
		x = (.5 - random()) * float(width - 10)
		y = (.5 - random()) * float(height - 10)
		return int(x), int(y)

	def process(self, domain, qurlstr, request_id, node_info, follow_redirect=True):
		if domain not in self.nodes:
			self.nodes[domain] = {}
			self.nodes_rid[domain] = {}
			self.graphs[domain] = digraph()
		new_node = False
		uid = hash(qurlstr)
		node_type = 'vulnerable' if self.appinfo.hasFindingForURL(qurlstr) else GraphView.__probe_type(node_info)

		if follow_redirect and node_info['redirected_from']:
			# for each request_id in the redirected, add the node in the graph, but set it non
			# clickable, and we will need different types of edges
			for req_qurlstr in node_info['redirected_from']:
				req_uid = hash(req_qurlstr)
				if req_qurlstr not in self.nodes[domain]:
					self.nodes[domain][req_qurlstr] = NodeItem(self)
					self.nodes[domain][req_qurlstr].setText(GraphView.__display_url(req_qurlstr))
					self.nodes[domain][req_qurlstr].setUniqueID(req_uid)
					self.nodes[domain][req_qurlstr].setInfo((domain, req_qurlstr))
					self.nodes[domain][req_qurlstr].setType("redirection")
					self.nodes[domain][req_qurlstr].setMimeApplication('application')
					self.graphs[domain].add_node(req_uid)
					self.uid_rid[req_uid] = node_info['redirected_from'][req_qurlstr]
					self.nodes_rid[domain][node_info['redirected_from'][req_qurlstr]] = self.nodes[domain][req_qurlstr]
				# even if node already in the nodes[domain], we might have a 301/302
				if domain not in self.redir_edges:
					self.redir_edges[domain] = {}
				if uid not in self.redir_edges[domain]:
					self.redir_edges[domain][uid] = []
				if req_uid not in self.redir_edges[domain][uid]:
					self.redir_edges[domain][uid].append(req_uid)
				new_node = True

		if qurlstr not in self.nodes[domain]:
			# create node if not in repo already, assign properties and random location
			self.nodes[domain][qurlstr] = NodeItem(self)
			if 1 == len(self.nodes[domain]):
				self.nodes[domain][qurlstr].setPos(0, 0)
			else:
				self.nodes[domain][qurlstr].setPos(*GraphView.__randomPos(self.viewWidth, self.viewHeight))
			self.nodes[domain][qurlstr].setText(GraphView.__display_url(qurlstr))
			self.nodes[domain][qurlstr].setUniqueID(uid)
			self.nodes[domain][qurlstr].setInfo((domain, qurlstr))
			self.nodes[domain][qurlstr].setType(node_type)
			self.nodes[domain][qurlstr].setMimeApplication(True if 'application' in node_info['content-type'] else False)
			if uid not in self.uid_rid:
				self.uid_rid[uid] = request_id
		else:
			# update the node info
			# self.nodes[domain][qurlstr].oneMoreRequest()
			self.nodes[domain][qurlstr].setType(node_type)
			self.nodes[domain][qurlstr].setMimeApplication(True if 'application' in node_info['content-type'] else False)

		if self.nodes[domain][qurlstr].hasMimeApplication() and not self.graphs[domain].has_node(uid):
			self.graphs[domain].add_node(uid)
			new_node = True

		if request_id:
			if request_id not in self.nodes_rid[domain]:
				self.nodes_rid[domain][request_id] = self.nodes[domain][qurlstr]
			self.rid_uid[request_id] = uid

		if new_node:
			self.adjust()

	def add_edge(self, domain, node_1, node_2):
		edge = (node_1, node_2)
		if  self.graphs[domain].has_node(node_1) and self.graphs[domain].has_node(node_2) and not self.graphs[domain].has_edge(edge):
			self.graphs[domain].add_edge(edge)
		else:
			self.graphs[domain].set_edge_weight(edge, self.graphs[domain].edge_weight(edge) + 1)

	def hasNodeInRedirection(self, domain, current_node, processed_node):
		return domain in self.redir_edges and current_node in self.redir_edges[self.activedomain] and processed_node in self.redir_edges[self.activedomain][current_node]

	def update_internal_graph(self):
		if self.activedomain in self.nodes:
			if self.activedomain in self.appinfo.original_requests:
				links = self.appinfo.original_requests[self.activedomain]['originals']
				length_links = len(links)
				for i in range(length_links):
					req_id = links[i]
					node_uid = self.rid_uid[req_id]
					# print node_uid, self.redir_edges
					# is there any incident node that we need to add?
					if self.activedomain in self.redir_edges and node_uid in self.redir_edges[self.activedomain]:
						for req_uid in self.redir_edges[self.activedomain][node_uid]:
							self.add_edge(self.activedomain, req_uid, node_uid)
					if 1 < length_links and i < length_links - 1:
						subsequent_nodes = [self.rid_uid[j] for j in range(req_id+1, links[i+1]) if j in self.rid_uid and self.graphs[self.activedomain].has_node(self.rid_uid[j])]
						for sub_uid in subsequent_nodes:
							if sub_uid == node_uid or self.hasNodeInRedirection(self.activedomain, node_uid, sub_uid):
								continue
							self.add_edge(self.activedomain, node_uid, sub_uid)
					else:
						# node_uid -> all nodes
						for sub_uid in self.graphs[self.activedomain].nodes():
							if sub_uid == node_uid or self.hasNodeInRedirection(self.activedomain, node_uid, sub_uid):
								continue
							self.add_edge(self.activedomain, node_uid, sub_uid)

	def add_visual_components(self):
		if self.activedomain:
			for uid in self.graphs[self.activedomain].nodes():
				n = self.nodes_rid[self.activedomain][self.uid_rid[uid]]
				self.scene.addItem(n)

			for edge in self.graphs[self.activedomain].edges():
				n1 = self.nodes_rid[self.activedomain][self.uid_rid[edge[0]]]
				n2 = self.nodes_rid[self.activedomain][self.uid_rid[edge[1]]]
				highlighted = edge in self.highlight_edges
				self.scene.addItem(EdgeItem(n1, n2, self.graphs[self.activedomain].edge_weight(edge), highlighted))

			self.layout.updateNodesPositions(self.graphs[self.activedomain], self.nodes_rid[self.activedomain], self.uid_rid)

	@staticmethod
	def __build_edges(nodes):
		cycle_edges = zip(nodes, nodes[1:])
		cycle_edges.append((nodes[len(nodes) - 1], nodes[0]))
		return cycle_edges

	@staticmethod
	def __extract_cycles_acc(acc_matrix):
		edge_repo = []
		for node in acc_matrix:
			if 1 < len(acc_matrix[node]):
				edges = GraphView.__build_edges(acc_matrix[node])
				for e in edges:
					if e not in edge_repo:
						edge_repo.append(e)
		return edge_repo

	# compute positions of the nodes
	def adjust(self):
		self.update_internal_graph()
		if self.activedomain:
			self.highlight_edges = []
			if self.selected_heuristic and self.selected_heuristic in LIST_HEURISTICS:
				term_heuristic = LIST_HEURISTICS[self.selected_heuristic]
				if 'CYCLES' == term_heuristic:
					cycle = find_cycle(self.graphs[self.activedomain])
					if 1 < len(cycle):
						acc_matrix = mutual_accessibility(self.graphs[self.activedomain])
						self.highlight_edges = GraphView.__extract_cycles_acc(acc_matrix)
				elif 'SECURE_PATHS' == term_heuristic:
					# highlight edges to which the destination node is "secured" over HTTPS
					edge_repo = []
					for edge in self.graphs[self.activedomain].edges():
						dest = self.nodes_rid[self.activedomain][self.uid_rid[edge[1]]]
						if dest.hasSecureFlag() and edge not in edge_repo:
							edge_repo.append(edge)
					self.highlight_edges = edge_repo

		self.add_visual_components()

	def redrawScene(self):
		self.scene.newScene()
		self.adjust()

	def changeDomain(self):
		self.redrawScene()

	def executeHeuristic(self):
		self.redrawScene()
