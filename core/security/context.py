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

import os, re, sys
import lxml, lxml.html as lhtml

CONTEXT = [
	"html", "html-tag", "html-attribute", "html-uri",
	"script", "script-inline",
	"style", "style-inline"
]

CONTEXT_INCODE = [
	"comment", "string", "default", "flash-construct", "attribute"
]

# sequences that qualifies for the flash variable context (html/flash-construct)
FLASH_VAR_SEQUENCES = [('object', 'param', 'value'), ('object', 'embed', 'flashvars')]

# html javascript locations
JS_HTML_TAG_ATTRIBUTE = re.compile(r"(on[a-z_]+|script)", re.I)
CSS_HTML_TAG_ATTRIBUTE = re.compile(r"style", re.I)

isiterable = lambda obj: isinstance(obj, basestring) or getattr(obj, '__iter__', False)
__string = lambda obj: isinstance(obj, str) or isinstance(obj, unicode)

# dict object to store the entire XML
class ObjectDict(dict):
	def __init__(self, initd = None):
		if initd is None:
			initd = {}
		dict.__init__(self, initd)
	def __getattr__(self, item):
		d = self.__getitem__(item)
		# if value is the only key in object, you can omit it
		if isinstance(d, dict) and '@value' in d and len(d) == 1:
			return d['@value']
		else:
			return d
	def __setattr__(self, item, value):
		self.__setitem__(item, value)

def html_encode(rts):
	return rts.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace("\"","&quot;").replace("'", "&#39;")

def html_decode(rts):
	return rts.replace("&lt;", "<").replace("&gt;", ">").replace("&quot;", "\"").replace("&apos;","'").replace("&#39;","'").replace("&amp;", "&")

def parse_node(node):
	tmp = ObjectDict()
	if node.text:
		tmp['@value'] = node.text
	for (k, v) in node.attrib.items():
		tmp[k] = v
	for ch in node.getchildren():
		cht = ch.tag
		chp = parse_node(ch)
		if cht not in tmp: # the first time, so store it in dict
			tmp[cht] = chp
			continue
		old = tmp[cht]
		if not isinstance(old, list):
			tmp.pop(cht)
			tmp[cht] = [old] # multi times, so change old dict to a list
		tmp[cht].append(chp) # add the new one
	return	tmp

def valid_search_elmt(elmt, search):
	for s in search:
		if s.match(elmt):
			return True
	return False

"""
# debugging decorator
class Tracing(object):
	def __init__(self, func):
		self.func = func
	def _showargs(self, *fargs, **kw):
		print "call function '%s' - args = %s, kw = %s" % (self.func.__name__, str(fargs), str(kw))
	def _aftercall(self, status):
		print "exit function '%s' - status = %s" % (self.func.__name__, str(status))
	def __call__(self, *fargs, **kw):
		self._showargs(*fargs, **kw)
		ret = self.func(*fargs, **kw)
		return ret
	def __repr__(self):
		return self.func.func_name
"""

def iterate_dict_value(d, elmt, blocks, tokenizer):
	if isinstance(d, list):
		for content in d:
			iterate_dict_value(content, elmt, blocks, tokenizer)
	else:
		if elmt not in blocks:
			blocks[elmt] = []
		if __string(d):
			blocks[elmt].append({'@value' : d, '@tokens' : tokenizer(d) if tokenizer else None})
		else:
			if '@value' in d:
				blocks[elmt].append({'@value' : d['@value'], '@tokens' : tokenizer(d['@value']) if tokenizer else None})

def iterate_dict(d, search, blocks, tokenizer = None):
	if not isinstance(d, dict):
		return
	for elmt in d:
		if __string(elmt) and valid_search_elmt(elmt, search):
			iterate_dict_value(d[elmt], elmt, blocks, tokenizer)
		if isinstance(d[elmt], list):
			for e in d[elmt]:
				iterate_dict(e, search, blocks, tokenizer)
		else:
			iterate_dict(d[elmt], search, blocks, tokenizer)

# return paths to 'needle' in all contexts
def find_needle_paths(dct, search, path = ()):
	for k in dct:
		if search(dct[k]) or search(k):
			yield path + (k,), dct[k]
		elif isinstance(dct[k], dict):
			for p in find_needle_paths(dct[k], search, path + (k,)):
				yield p
		elif isinstance(dct[k], list):
			for sdct in dct[k]:
				for p, v in find_needle_paths(sdct, search, path + (k,)):
					yield p, v

CACHED_NEEDLE = {}
def contains_needle(elmt, needle):
	global CACHED_NEEDLE
	if needle not in CACHED_NEEDLE:
		CACHED_NEEDLE[needle] = re.compile(needle, re.I)
	return __string(elmt) and CACHED_NEEDLE[needle].search(elmt) != None

# search for a subsequence (ordered) using strings
def contained_sequence(path, sequences, reverse = True):
	path = ''.join([p for p in path])
	if reverse:
		path = path[::-1]
	for elmt in sequences:
		elmt = ''.join(elmt)
		if reverse:
			elmt = elmt[::-1]
		if elmt in path:
			return True
	return False

def extract_css_incode(code, needle):
	return "default"

def tokens_js_search(tokens, search):
	a = list((i, v) for i, v in enumerate(tokens))
	print len(a)

def extract_js_incode(code, needle):
	tokens = js_parse(code)
	if tokens:
		tokens_js_search(tokens, lambda x: contains_needle(x, needle))
		print "#INCODE#"
	return ["default"]


# associate a context to a given path
def extract_html_context(dct, path, value, needle = None):
	context, context_incode = "html", "default"
	for node in path:
		s_node = str(node)
		if s_node == "<built-in function Comment>":
			context, context_incode = "html", "comment"
		elif CSS_HTML_TAG_ATTRIBUTE.match(s_node):
			context = "style"
		elif JS_HTML_TAG_ATTRIBUTE.match(s_node):
			context = "script"
		elif s_node in ("href", "src"):
			context = "html-uri"

	# adjust context or context_incode based on the last element (cf. @value for tag content)
	last_node = path[len(path) - 1]
	if not "@value" == last_node:
		if context in ("style", "script"):
			context = context + "-inline"
		elif needle and contains_needle(str(last_node), needle):
			context = "html-tag"
			context_incode = "attribute"
		elif "html" == context:
			context = "html-attribute"
			if contained_sequence(path, FLASH_VAR_SEQUENCES):
				context_incode = "flash-construct"
	"""
	# use parsers to extract the in code context for JavaScript and CSS
	if "style" in context:
		context_incode = extract_css_incode(value, needle)
	elif "script" in context:
		context_incode = extract_js_incode(value, needle)
	print path, context, context_incode
	"""

	return context, context_incode

# generate findings associated with the contexts
def html_path_findings(d, needle, html_findings):
	for p, value in find_needle_paths(d, lambda x: contains_needle(x, needle)):
		print value

		context, context_incode = extract_html_context(d, p, value, needle)
		if context not in html_findings:
			html_findings[context] = {}
		if not isinstance(context_incode, list):
			context_incode = [context_incode]
		for c_incode in context_incode:
			if c_incode not in html_findings[context]:
				html_findings[context][c_incode] = []
			html_findings[context][c_incode].append({'@path' : p, '@value' : value})


def extract_context(needle, doc):
	d = ObjectDict({doc.tag: parse_node(doc)})
	# find occurences of the needle in the different
	html_findings = {}
	html_path_findings(d, needle, html_findings)
	return html_findings


def context_generation(buf, needle = 'INJECTION_POINT'):
	doc = lhtml.fromstring(buf)
	return extract_context(needle, doc)

"""
encodings = ['latin-1', 'utf8', 'utf7', 'utf16']
def probe(unique = 'SHEEPTOKEN', encoding = 'ascii'):
	return (u"<[{('\",.#@-+=*%&!;\\/)}]>__ABCDabcd0987:%s" % unique).encode(encoding)
"""
"""
def main(argc, argv):
	if 2 == argc and os.path.isfile(argv[1]):
		context_generation(open(argv[1]).read())

if __name__ == "__main__":
	main(len(sys.argv), sys.argv)
"""
