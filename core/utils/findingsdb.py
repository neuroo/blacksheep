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
import sys, csv, os
import hashlib, random, time

from PySide.QtCore import *
from PySide.QtGui import *

import core.management

from core.utils.domain import extract_domain

class FindingsCategory:
	def __init__(self):
		# ID -> {name, reference, description, CWE-IDs, CAPEC-IDs, }
		self.categories = {}
		self.name_uid = {}
		self.user_classification_fname = core.management.configuration['path']['user'] + "bsheep-classification.csv"
		# load pre-existing
		if os.path.isfile(self.user_classification_fname):
			self.fname = self.user_classification_fname
		else:
			self.fname = core.management.configuration['path']['resources'] + 'WASC-MITRE.csv'
		self.load()

	@staticmethod
	def __prepare_list(lst):
		if not isinstance(lst, list):
			lst = lst.split(',')
		return [int(tni) for tni in lst if 0 < len(tni)]

	@staticmethod
	def __stringify_list(lst):
		return ", ".join([str(i) for i in lst])

	@staticmethod
	def __uniqueid(name, reference):
		return hashlib.md5(name + reference + str(time.time())).hexdigest()

	def hasCategory(self, name):
		return self.name_uid[name] if name in self.name_uid else None

	def getCategory(self, uid):
		return self.categories[uid] if uid in self.categories else None

	def add(self, name, unique_id, cwe_list, capec_list, description, references):
		if not name or 1 > len(name):
			return False

		if name in self.name_uid:
			core.management.logger.error("FindingsCategory::add- The category name '%s' is already in the database" % name)
			return False

		if not unique_id or 1 > len(unique_id):
			unique_id = FindingsCategory.__uniqueid(name, references)
			if unique_id in self.categories:
				unique_id = FindingsCategory.__uniqueid(name, references + str(random.randint()))

		if unique_id not in self.categories:
			cwe_list = FindingsCategory.__prepare_list(cwe_list)
			capec_list = FindingsCategory.__prepare_list(capec_list)
			self.name_uid[name] = unique_id
			self.categories[unique_id] = {'name' : name, 'reference' : references,
										'description' : description, 'cwe-list' : [x for x in cwe_list],
										'capec-list' : [x for x in capec_list]}
			return True
		return False

	def getCategoryNames(self):
		return self.name_uid.keys()

	def getCategories(self):
		return self.categories

	def load(self):
		self.categories = {}
		cat = csv.DictReader(open(self.fname), delimiter=',', quotechar='"')
		for c in cat:
			# name, id, cwe_ids, capec_links,
			self.add(c['Name'], c['Unique_ID'], c['CWE ID'].split(','), c['CAPEC ID'].split(','), c['Description'], c['References'])

	# save custom classification
	def save(self):
		writer = csv.writer(open(self.user_classification_fname, 'w'), delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
		writer.writerow(["Unique_ID","Name","CWE ID","CAPEC ID","Description","References"])
		for uid in self.categories:
			cwe_list = FindingsCategory.__stringify_list(self.categories[uid]['cwe-list'])
			capec_list = FindingsCategory.__stringify_list(self.categories[uid]['capec-list'])
			writer.writerow([uid, self.categories[uid]['name'], cwe_list, capec_list, self.categories[uid]['description'],self.categories[uid]['reference']])


class FindingsDatabase(QObject):
	def __init__(self, netmanager):
		QObject.__init__(self)

		self.netmanager = netmanager
		self.cat = FindingsCategory()

		# Findings:
		#  finding id {
		#   'qurlstr' : main URL
		#   'uid' : general type of vuln
		#   'trace' : [{
		#      req_id, uid, parameter, payload, description, user
		#   }]
		#   'severity' : 0-> 5
		#   'impact' :  Don't care, Low, Medium, High, Critical
		#   'description' : ""
		#   'reference' : ""
		#   'domain' : ""
		#   'type' : "Manual/Automated/Plugin/Other"
		self.db = {}

		# finding id -> uid
		self.uid_findingid = {}
		self.qurlstr_findingid = {}

	def addCategory(self, category_name, cwe_list, capec_list, description, reference):
		self.cat.add(category_name, None, cwe_list, capec_list, description, reference)

	def propagateChangeFindingID_UID(self, findingid, olduid, uid):
		if findingid in self.uid_findingid[olduid]:
			self.uid_findingid[olduid].remove(findingid)
			if 1 > len(self.uid_findingid[olduid]):
				del self.uid_findingid[olduid]
		if uid not in self.uid_findingid:
			self.uid_findingid[uid] = []
		if findingid not in self.uid_findingid[uid]:
			self.uid_findingid[uid].append(findingid)

	def propagateChangeFindingID_URL(self, findingid, oldqurlstr, qurlstr):
		if findingid in self.qurlstr_findingid[oldqurlstr]:
			self.qurlstr_findingid[oldqurlstr].remove(findingid)
			if 1 > len(self.qurlstr_findingid[oldqurlstr]):
				del self.qurlstr_findingid[oldqurlstr]

		if qurlstr not in self.qurlstr_findingid:
			self.qurlstr_findingid[qurlstr] = []
		if findingid not in self.qurlstr_findingid[qurlstr]:
			self.qurlstr_findingid[qurlstr].append(findingid)

	def updateFindingParameter(self, findingid, key, value):
		if findingid in self.db and key in self.db[findingid]:
			self.db[findingid][key] = value
			return True
		return False

	def updateFindingTraceParameter(self, findingid, req_id, key, value):
		if findingid in self.db and 'trace' in self.db[findingid]:
			for elmt in self.db[findingid]['trace']:
				if req_id == elmt['req_id']:
					if key not in elmt:
						return False
					elmt[key] = value
					return True
		return False

	def hasFindingForURL(self, qurlstr):
		return qurlstr in self.qurlstr_findingid

	def renew(self):
		self.db = {}
		self.uid_findingid = {}
		self.qurlstr_findingid = {}

	def delete(self, findingid):
		if findingid in self.db:
			uid = self.db[findingid]['uid']
			qurlstr = self.db[findingid]['qurlstr']
			# remove the findingid and all its occurences...
			if uid in self.uid_findingid and findingid in self.uid_findingid[uid]:
				self.uid_findingid[uid].remove(findingid)
				if 1 > len(self.uid_findingid[uid]):
					del self.uid_findingid[uid]
			if qurlstr in self.qurlstr_findingid and findingid in self.qurlstr_findingid[qurlstr]:
				self.qurlstr_findingid[qurlstr].remove(findingid)
				if 1 > len(self.qurlstr_findingid[qurlstr]):
					del self.qurlstr_findingid[qurlstr]
			del self.db[findingid]

	@staticmethod
	def __url_str(qurl):
		if not isinstance(qurl, QUrl):
			qurl = QUrl(qurl)
		return qurl.toString(QUrl.StripTrailingSlash | QUrl.RemoveFragment | QUrl.RemoveQuery | QUrl.RemoveUserInfo)

	@staticmethod
	def __findingid(data):
		if not isinstance(data, unicode):
			data = unicode(data)
		return hashlib.sha1(data + str(time.time())).hexdigest()

	def insert(self, uid, qurlstr, data):
		try:
			qurlstr = FindingsDatabase.__url_str(qurlstr)
			domain = extract_domain(qurlstr)
			findingid = FindingsDatabase.__findingid(unicode(qurlstr) + unicode(data))
			if findingid not in self.db:
				if uid not in self.uid_findingid:
					self.uid_findingid[uid] = []
				self.uid_findingid[uid].append(findingid)

				if qurlstr not in self.qurlstr_findingid:
					self.qurlstr_findingid[qurlstr] = []
				self.qurlstr_findingid[qurlstr].append(findingid)

				# store information in the DB
				self.db[findingid] = {
					'uid' : uid,
					'qurlstr' : qurlstr,
					'severity' : data['severity'],
					'impact' : data['impact'],
					'description' : data['description'],
					'reference' : data['reference'],
					'domain' : domain,
					'trace' : data['trace'],
					'type' : data['type']
				}
				self.emit(SIGNAL('newFindingForURL'), qurlstr)
				self.emit(SIGNAL('refreshFindingsView'))
				return findingid
		except Exception, error:
			core.management.logger.exception("FindingsDatabase::insert- Error while inserting a finding (Exception: %s)" % error)
		return None

	def insertFindingHelper_CategoryAttackIDs(self, category, attackdata):
		# make sure that the category exist
		uid = self.cat.hasCategory(category)
		if not uid:
			core.management.logger.error("FindingsDatabase::insertFindingHelper_CategoryAttackIDs- The category name '%s' cannot be found in the category database" % category)
			return
		# attackdata has the structure of: {'location' : location, 'parameter' : parameter, 'value' : value, 'req_id' : req_id, 'type' : method}
		num_trace_steps = len(attackdata)
		qurlstr = FindingsDatabase.__url_str(attackdata[num_trace_steps - 1]['location'])
		# 'trace' : [{
		#      req_id, uid, parameter, payload, description, user
		#   }]
		traces = []
		for step in attackdata:
			traces.append({'req_id' : step['req_id'], 'uid' : uid, 'parameter' : step['parameter'], 'payload' : step['value'], 'description' : None, 'user' : None})
		cat_info = self.cat.getCategory(uid)
		data = {
			'type' : "Automated detection by Sheep",
			'impact' : 0,
			'severity' : 0,
			'description' : cat_info['description'],
			'reference' : cat_info['reference'],
			'trace' : traces
		}
		return self.insert(uid, qurlstr, data)

	def insertFinding_RequestID(self, request_id):
		if not isinstance(request_id, list):
			request_id = [request_id]

		# qurlstr is the last URL (sink of the test case)
		num_requests = len(request_id)
		req_info = self.netmanager.history.getHistory(request_id[num_requests - 1])
		qurlstr = FindingsDatabase.__url_str(req_info['request']['url'])

		trace = []
		for req_id in request_id:
			trace.append({'req_id' : req_id, 'uid' : None, 'parameter' : None, 'payload' : None, 'description' : None, 'user' : None})

		data = {
			'type' : "Manually added",
			'impact' : 0,
			'severity' : 0,
			'description' : "",
			'reference' : "",
			'trace' : trace
		}
		return self.insert(self.getCategoryUID("Unclassified"), qurlstr, data)

	def duplicateFinding(self, findingid):
		if findingid in self.db:
			uid = self.db[findingid]['uid']
			qurlstr = self.db[findingid]['qurlstr']
			return self.insert(uid, qurlstr, self.db[findingid])

	def numFindings_URL(self, qurlstr):
		return len(self.qurlstr_findingid[qurlstr]) if qurlstr in self.qurlstr_findingid else 0

	def numFindings_UID(self, uid):
		return len(self.uid_findingid[uid]) if uid in self.uid_findingid else 0

	def hasFinding(self, uid):
		return True if uid in self.uid_findingid else False

	def getFindingRepresentative(self, findingid):
		if findingid not in self.db:
			return None, None
		trace = self.db[findingid]['trace']
		last_trace_elmt = trace[len(trace) - 1]
		req_info = self.netmanager.history.getHistory(last_trace_elmt['req_id'])
		return req_info['type'], req_info['request']['url'], last_trace_elmt['parameter'] if last_trace_elmt['parameter'] else "", last_trace_elmt['payload'] if last_trace_elmt['payload'] else ""

	def getTraceRepresentative(self, req_id):
		req_info = self.netmanager.history.getHistory(req_id)
		return req_info['type'], req_info['request']['url']

	def getcategoryName(self, uid):
		c = self.cat.getCategory(uid)
		if c:
			return c['name']
		return None

	def getCategoryUID(self, name):
		return self.cat.name_uid[name] if name in self.cat.name_uid else None

	def getFindingsPerUID(self, uid):
		return self.uid_findingid[uid] if uid in self.uid_findingid else []

	def getFindingInfo(self, findingid):
		return self.db[findingid]

	def getCategories(self):
		return self.cat.getCategories()

	def getCategoryNames(self):
		cats = self.cat.getCategoryNames()
		cats.sort()
		return cats

	def save(self):
		self.cat.save()
		# TODO: need to save the current findings

	def exportAs(self, filename):
		core.management.logger.debug("FindingsDatabase:exportAs- Not implemented yet... yah! but here is the content: %s" % unicode(self.db))
