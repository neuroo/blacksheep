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
import math

from PyQt4.QtCore import *
from PyQt4.QtGui import *

import core.management

NODE_TYPE_COLOR_MAP = {
	'default' : (QColor(Qt.green), QColor(Qt.darkGreen)),
	'vulnerable' :  (QColor(Qt.red), QColor(Qt.darkRed)),
	'spidered' : (QColor(Qt.lightGray), QColor(Qt.gray)),
	'tampered' :  (QColor(Qt.yellow), QColor(Qt.darkYellow)),
	'original' :  (QColor(Qt.blue), QColor(Qt.darkBlue)),
	'redirection' : (QColor(Qt.white), QColor(Qt.lightGray))
}

NODE_TYPE_COLOR_MAP_KEYS = NODE_TYPE_COLOR_MAP.keys()

class GraphicsScene(QGraphicsScene):
	def __init__(self, parent = None):
		QGraphicsScene.__init__(self, parent)
		self.filter = None
		# addons to do fast lookup for graphics items
		self.widgets_nodes = {}
		self.widgets_edges = {}

	def addItem(self, item):
		if isinstance(item, NodeItem) and item.info[1] not in self.widgets_nodes:
			self.widgets_nodes[item.info[1]] = item
			QGraphicsScene.addItem(self, item)
		elif isinstance(item, EdgeItem):
			src, dest = item.source.info[1], item.dest.info[1]
			if src not in self.widgets_edges:
				self.widgets_edges[src] = {}
			if dest not in self.widgets_edges[src]:
				self.widgets_edges[src][dest] = item
				QGraphicsScene.addItem(self, item)

	def filterElements(self, filter):
		if not filter:
			for i in self.widgets_nodes:
				self.widgets_nodes[i].active = True
		else:
			return


	def newScene(self):
		for w in self.widgets_nodes:
			QGraphicsScene.removeItem(self, self.widgets_nodes[w])
		for src in self.widgets_edges:
			for dest in self.widgets_edges[src]:
				QGraphicsScene.removeItem(self, self.widgets_edges[src][dest])
		self.widgets_nodes = {}
		self.widgets_edges = {}
		self.clear()


class NodeItem(QGraphicsItem):
	Type = QGraphicsItem.UserType + 1
	def __init__(self, graphWidget=None):
		QGraphicsItem.__init__(self)
		self.sslQimage = QImage(core.management.configuration['path']['resources'] + 'images/icons/lock.png')
		self.graph = graphWidget
		self.newPos = QPointF()
		self.edges = []
		self.f = QPointF()
		self.active = True
		self.type = 'default'
		self.secure = False
		self.text = ""
		self.info = ()
		self.mime_application = False
		self.uid = -1
		self.diameter = 20
		self.inner_diameter = 20
		self.size_font = 10
		self.font = QFont("monaco, monospace, sans-sherif", self.size_font, QFont.Light)
		self.metrics = QFontMetrics(self.font)
		self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setFlag(QGraphicsItem.ItemIsMovable)
		self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
		self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
		self.setZValue(-1)

	def setInfo(self, tpl):
		self.info = tpl
		self.secure = 'https' in self.info[1]

	def hasSecureFlag(self):
		return self.secure

	def setUniqueID(self, uid):
		self.uid = uid

	def hasMimeApplication(self):
		return self.mime_application

	def setMimeApplication(self, mime_application):
		self.mime_application = mime_application

	def setText(self, text):
		self.text = text

	def setType(self, type):
		if type not in NODE_TYPE_COLOR_MAP_KEYS:
			self.type = 'default'
		else:
			self.type = type

	def setDiameter(self, diameter):
		self.diameter = min(75, diameter)

	def oneMoreRequest(self):
		self.setDiameter(self.diameter + 5)

	def addEdge(self, edge):
		self.edges.append(edge)
		edge.adjust()

	def edges(self):
		return self.edges

	def type(self):
		return NodeItem.Type

	def shape(self):
		path = QPainterPath()
		path.addEllipse(-self.diameter // 2, -self.diameter // 2, self.diameter, self.diameter)
		return path

	def advance(self):
		if self.newPos == self.pos():
			return False
		self.setPos(self.newPos)
		return True

	def paint(self, painter, option, widget):
		if not self.active:
			return

		painter.setPen(Qt.NoPen)
		painter.setBrush(Qt.darkGray)

		if self.inner_diameter < self.diameter:
			painter.setBrush(Qt.NoBrush)
			painter.setPen(QPen(Qt.gray, 1, Qt.DashLine))
			painter.drawEllipse(-self.diameter // 2, -self.diameter // 2, self.diameter, self.diameter)
			painter.setPen(Qt.NoPen)
			painter.setBrush(Qt.darkGray)

		e1 = self.inner_diameter // 5
		e2 = 2 * e1  + 1
		e3 = self.inner_diameter // 2
		gradient = QRadialGradient(-e1, -e1, e3)
		if option.state & QStyle.State_Sunken:
			gradient.setCenter(e1, e1)
			gradient.setFocalPoint(e1, e1)
			gradient.setColorAt(1, QColor(NODE_TYPE_COLOR_MAP[self.type][0]).light(120))
			gradient.setColorAt(0, QColor(NODE_TYPE_COLOR_MAP[self.type][1]).light(120))
		else:
			gradient.setColorAt(0, NODE_TYPE_COLOR_MAP[self.type][0])
			gradient.setColorAt(1, NODE_TYPE_COLOR_MAP[self.type][1])

		painter.setBrush(gradient)
		painter.setPen(QPen(Qt.black, 0))
		painter.drawEllipse(-e3, -e3, self.inner_diameter, self.inner_diameter)

		if self.isSelected() and 'redirection' != self.type:
			# show that the item is selected
			painter.setBrush(QColor(0, 0, 255, 25))
			painter.setPen(QPen(QColor(0, 0, 255, 55), 1))
			painter.drawRect(-self.diameter // 2 - 10, -self.diameter // 2 - 10, self.diameter + 20, self.diameter + 20)
			painter.setPen(Qt.NoPen)
			painter.setBrush(Qt.NoBrush)

		if self.secure:
			painter.drawImage(QPoint(-self.diameter // 2 + 10, -self.diameter // 2 + 10), self.sslQimage)

		if self.text and 0 < len(self.text):
			painter.setBrush(Qt.NoBrush)
			text = self.text
			textW = self.metrics.width(self.text)
			if 150 < textW:
				# let's remove some chars there...
				text = self.metrics.elidedText(text, Qt.ElideMiddle, 150)
				textW = self.metrics.width(text)
			textRect = QRectF(- textW // 2, self.inner_diameter // 2 + 2, textW, self.metrics.height() + 2)
			painter.setFont(self.font)
			painter.setPen(Qt.black)
			painter.drawText(textRect, text)
			# painter.drawRect(textRect)

	def boundingRect(self):
		adjust = self.diameter // 10
		e3 = self.diameter // 2
		textW = max(4 * self.diameter, self.metrics.width(self.text))
		return QRectF(min(- textW // 2, -self.diameter // 2 - 10) - adjust, -self.diameter // 2 - 10 - adjust, max(textW, self.diameter + 20) + 2*adjust, self.diameter + adjust + self.metrics.height() + 20)

	def itemChange(self, change, value):
		if QGraphicsItem.ItemPositionChange == change:
			self.newPos = value.toPointF()
			for edge in self.edges:
				edge.adjust()
			self.graph.itemMoved()
			self.update()
		return QGraphicsItem.itemChange(self, change, value)

	def mousePressEvent(self, event):
		self.update()
		QGraphicsItem.mousePressEvent(self, event)

	def mouseReleaseEvent(self, event):
		self.update()
		QGraphicsItem.mouseReleaseEvent(self, event)


class EdgeItem(QGraphicsItem):
	Pi = math.pi
	TwoPi = 2.0 * Pi
	Type = QGraphicsItem.UserType + 2
	def __init__(self, sourceNode, destNode, edgeWeight=1, highlighted=False):
		QGraphicsItem.__init__(self)
		self.arrowSize = 5.0
		self.edgeWeight = edgeWeight
		self.lineWeight = EdgeItem.__line_height(self.edgeWeight)
		self.highlighted = highlighted
		#self.setFlag(QGraphicsItem.ItemIsSelectable)
		self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)
		self.setZValue(0)
		self.source = sourceNode
		self.dest = destNode
		self.type = 'solid'
		self.active = True
		if self.source.type == 'redirection' or self.dest.type == 'redirection':
			self.type = 'dashed'
		self.sourcePoint = self.source.pos()
		self.destPoint = self.dest.pos()
		self.source.addEdge(self)
		self.dest.addEdge(self)
		self.adjust()

	@staticmethod
	def __line_height(weight):
		if weight >= 50: return 3
		elif weight >= 25: return 2
		return 1

	def type(self):
		return EdgeItem.Type

	def setWeight(self, edgeWeight):
		self.edgeWeight = edgeWeight
		self.lineWeight = EdgeItem.__line_height(self.edgeWeight)

	def oneMoreRequest(self):
		self.setWeight(self.edgeWeight + 1)

	def sourceNode(self):
		return self.source

	def setSourceNode(self, node):
		self.source = node
		self.adjust()

	def destNode(self):
		return self.dest

	def setDestNode(self, node):
		self.dest = node
		self.adjust()

	def adjust(self):
		if not self.source or not self.dest:
			return
		line = QLineF(self.mapFromItem(self.source, 0, 0), self.mapFromItem(self.dest, 0, 0))
		length = line.length()
		if length == 0.:
			return
		edgeOffset = QPointF((line.dx() * 10) / length, (line.dy() * 10) / length)
		self.prepareGeometryChange()
		self.sourcePoint = line.p1() + edgeOffset
		self.destPoint = line.p2() - edgeOffset

	def boundingRect(self):
		if not self.source or not self.dest:
			return QRectF()
		extra = (self.lineWeight + self.arrowSize) // 2
		return QRectF(self.sourcePoint, QSizeF(self.destPoint.x() - self.sourcePoint.x(), self.destPoint.y() - self.sourcePoint.y())).normalized().adjusted(-extra, -extra, extra, extra)

	def paint(self, painter, option, widget):
		if not self.source or not self.dest or not self.source.active or not self.dest.active:
			return
		painter.setPen(Qt.NoPen)
		painter.setBrush(Qt.darkGray)
		line = QLineF(self.sourcePoint, self.destPoint)
		if line.length() == 0.0:
			return
		color = Qt.darkGray

		if option.state & QStyle.State_Sunken or self.isSelected() or self.highlighted:
			color = QColor(0, 0, 255)

		painter.setPen(QPen(color, self.lineWeight, Qt.SolidLine if 'solid' == self.type else Qt.DashLine, Qt.RoundCap, Qt.RoundJoin))
		painter.drawLine(line)

		# if the weight is small enough, draw a simple array
		angle = math.acos(line.dx() / line.length())
		if line.dy() > 0:
			angle = EdgeItem.TwoPi - angle
		destArrowP1 = self.destPoint + QPointF(math.sin(angle - EdgeItem.Pi / 3) * self.arrowSize, math.cos(angle - EdgeItem.Pi / 3) * self.arrowSize)
		destArrowP2 = self.destPoint + QPointF(math.sin(angle - EdgeItem.Pi + EdgeItem.Pi / 3) * self.arrowSize, math.cos(angle - EdgeItem.Pi + EdgeItem.Pi / 3) * self.arrowSize)
		painter.setPen(Qt.black)
		painter.setBrush(color)
		painter.drawPolygon(QPolygonF([line.p2(), destArrowP1, destArrowP2]))
