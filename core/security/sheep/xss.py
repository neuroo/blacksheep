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

def generate_probe(unique_token = 'SHEEPTOKEN'):
	return "B:<[{('\",.@-+=%%!;\\/)}]>:%s:E" % unique_token

def examine_probe(returned_probe, origin_probe):
	tokens = returned_probe.split(':')[1:3]
	chars = tokens[0]
	id = tokens[1]

