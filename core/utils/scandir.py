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
import os, sys

# look for the good extension
def good_ext(fext, l = None):
	if not l:
		return True
	fext = fext.lower()
	for e in l:
		if fext == e:
			return True
	return False


regIgnoreListCompiled_cache = None
# scan a directory for ext_list and not matching the regexp provided in regIgnoreList
# return the result in 'files'
def scandir(directory, files, ext_list = None, regIgnoreList = None, onlyFolders = False):
	global regIgnoreListCompiled_cache
	names = os.listdir(directory)
	for name in names:
		srcname = os.path.join(directory, name)
		try:
			if os.path.isdir(srcname):
				if onlyFolders and srcname not in files:
					files.append(srcname)
				else:
					scandir(srcname, files, ext_list, regIgnoreList, onlyFolders)
			elif not onlyFolders and os.path.isfile(srcname) and good_ext(srcname[srcname.rfind('.')+1:], ext_list):
				if regIgnoreList:
					if not regIgnoreListCompiled_cache:
						# create the cache of compiled regexp
						regIgnoreListCompiled_cache = []
						for r in regIgnoreList:
							regIgnoreListCompiled_cache.append(re.compile(r))
					bypass = False
					for r in regIgnoreListCompiled_cache:
						if r.match(srcname):
							bypass = True
							break
					if bypass:
						continue
				if srcname not in files:
					files.append(srcname)
		except IOError, error:
			# silent failing...
			continue
