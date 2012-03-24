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
import random, math

from PyQt4.QtCore import *
from PyQt4.QtGui import *

from pygraph.algorithms.accessibility import accessibility, connected_components
from pygraph.algorithms.cycles import find_cycle
from pygraph.algorithms.critical import critical_path

class Layout:
	def __init__(self, scene):
		self.scene = scene
		self.graph = {}
		self.nodes = {}
		self.layer = {}
		self.iterate = 1000
		self.k, self.m, self.w, self.d, self.r = 2, .1, 15, 10, 50
		self.update()

	def update(self):
		self.width = self.scene.width()
		self.height = self.scene.height()

	def dist(self, a, b):
		dx = b.x() - a.x()
		dy = b.y() - a.y()
		return dx, dy, math.sqrt(dx**2 + dy**2), dx**2 + dy**2

	def updateNodesPositions(self, graph, nodes_rid, uid_rid):
		# n1 = self.nodes_rid[self.uid_rid[edge[0]]]
		self.graph = graph
		self.nodes = nodes_rid
		self.layer = uid_rid
		self.update()

		self.iterate = 1000
		list_nodes = self.graph.nodes()
		list_edges = self.graph.edges()

		# TODO: implement few graph layout heuristics
