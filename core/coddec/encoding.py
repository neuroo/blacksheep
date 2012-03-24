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
import base64
import jspacker
from PyQt4.QtCore import *

import core.management

# HTML
def encodeHTMLEntities(s):
	return s.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"","&quot;").replace("'", "&#39;")

def decodeHTMLEntities(s):
	return s.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;","'").replace("&#39;","'").replace("&amp;", "&")

def encodeURLPercent(s):
	return QUrl.toPercentEncoding(s)

def decodeURLPercent(s):
	return QUrl.fromPercentEncoding(s.toAscii())

def encodeURLPercentDouble(s):
	return encodeURLPercent(encodeURLPercent(s))

def decodeURLPercentDouble(s):
	return decodeURLPercent(decodeURLPercent(s))

def packJavaScript(s):
	p = jspacker.JavaScriptPacker()
	return p.pack(s, compaction =True, encoding=62, fastDecode=False)

def unpackJavaScript(s):
	core.management.logger.warning("The JavaScript unpacker is not implemented yet!")
	return None

def encodeHex(plainStr):
	return base64.b16encode(plainStr)

def encodeHex_Generic(plainStr, char='', end=''):
	buff16 = ""
	for c in plainStr:
		buff16 += (char + base64.b16encode(c) + end)
	return buff16

def encodeHex_Shell(plainStr):
	return encodeHex_Generic(plainStr, '\\x')

def encodeHex_Html(plainStr):
	return encodeHex_Generic(plainStr, '&#', ';')

def decodeHex(hexStr):
	return base64.b16decode(hexStr)

def decodeHex_Generic(hexStr, char='', end=''):
	hexStr = hexStr.replace(char, '')
	if end != '':
		hexStr = hexStr.replace(end, '')
	return decodeHex(hexStr)

def decodeHex_Shell(hexStr):
	return decodeHex_Generic(hexStr, '\\x')

def decodeHex_Html(hexStr):
	return decodeHex_Generic(hexStr, '&#', ';')

def encodeBase64(s):
	return base64.b64encode(s)

def decodeBase64(s):
	return base64.b64decode(s)

def encodeBase32(s):
	return base64.b32encode(s)

def decodeBase32(s):
	return base64.b32decode(s)

def encodeCodecUTF7(s):
	return s.encode('utf7')

def decodeCodecUTF7(s):
	return unicode(s, 'utf7')

CUSTOM_CHARSET = {
	'UTF-7' : {'encode' : encodeCodecUTF7, 'decode' : decodeCodecUTF7},
	'JsPacker' : {'encode' : packJavaScript, 'decode' : unpackJavaScript},
	'Base64' : {'encode' : encodeBase64, 'decode' : decodeBase64},
	'Base32' : {'encode' : encodeBase32, 'decode' : decodeBase32},
	'Hexadecimal' : {'encode' : encodeHex, 'decode' : decodeHex},
	'HTML entities' : {'encode' : encodeHTMLEntities, 'decode' : decodeHTMLEntities},
	'URL encoding' : {'encode' : encodeURLPercent, 'decode' : decodeURLPercent},
	'Double URL encoding' : {'encode' : encodeURLPercentDouble, 'decode' : decodeURLPercentDouble},
	'Shell Hex encoding' : {'encode' : encodeHex_Shell, 'decode' : decodeHex_Shell},
	'HTML Hex encoding' : {'encode' : encodeHex_Html, 'decode' : decodeHex_Html}
}

class CharsetEncoding:
	__unique = None
	def __init__(self):
		if CharsetEncoding.__unique:
			raise CharsetEncoding.__unique
		CharsetEncoding.__unique = self
		self.qt_available_codecs = [str(scodec) for scodec in QTextCodec.availableCodecs()]
		self.custom_codecs = CUSTOM_CHARSET.keys()
		self.available_codecs = []
		# start with UTF *
		for codecs in self.qt_available_codecs:
			if 'utf' == codecs[:3].lower():
				self.available_codecs.append(codecs)
		# append custom charsets and encodings
		self.available_codecs += self.custom_codecs
		for codecs in self.qt_available_codecs:
			if codecs not in self.available_codecs:
				self.available_codecs.append(codecs)

	def getAvailableCodecs(self):
		return self.available_codecs

	@staticmethod
	def __unqtify(qstr):
		if not isinstance(qstr, unicode):
			qstr = unicode(qstr)
		return qstr

	# probe encoder or decoder
	def probe(self, entity, encoder=True):
		if entity in self.custom_codecs:
			return CUSTOM_CHARSET[entity]['encode'] if encoder else CUSTOM_CHARSET[entity]['decode']
		else:
			codec = QTextCodec.codecForName(entity)
			return codec.fromUnicode if encoder else codec.toUnicode

	def encode(self, qstr, entity_src, entity_dst):
		qstr = CharsetEncoding.__unqtify(qstr)
		decoder = self.probe(str(entity_src), encoder=False)
		encoder = self.probe(str(entity_dst), encoder=True)
		if decoder and encoder:
			return QString(encoder(CharsetEncoding.__unqtify(decoder(qstr))))
		core.management.logger.error("CharsetEncoding::encode- Cannot convert string %s from %s to %s" % (qstr, charset_from, charset_to))
		return None
