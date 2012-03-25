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

user_agent = {
	"Chrome" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) Chrome/0.2.153.1 Safari/525.19",
	"Firefox": "Mozilla/5.0 (Windows; U; Windows NT 6.0; en-US; rv:1.9b5) Gecko/2008032620 Firefox/3.0b5 ",
	"IE6" : "Mozilla/4.0 (compatible; MSIE 6.0; Windows NT 5.0; T312461; .NET CLR 1.1.4322)",
	"IE7" : "Mozilla/4.0 (compatible; MSIE 7.0; Windows NT 5.1; .NET CLR 1.1.4322; .NET CLR 2.0.50727)",
	"IE8" : "Mozilla/4.0 (compatible; MSIE 8.0; Windows NT 5.1; Trident/4.0; .NET CLR 1.1.4322; .NET CLR 2.0.50727; .NET CLR 3.0.04506.30; .NET CLR 3.0.04506.648; InfoPath.1)",
	"Safari" : "Mozilla/5.0 (Macintosh; U; PPC Mac OS X; en-us) AppleWebKit/412 (KHTML, like Gecko) Safari/412",
	"Safari-iPhone" : "Mozilla/5.0 (iPod; U; CPU iPhone OS 2_2 like Mac OS X; en-us) AppleWebKit/525.18.1 (KHTML, like Gecko) Version/3.1.1 Mobile/5G77a Safari/525.20",
	"Safari-iPad" : "Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) Version/4.0.4 Mobile/7B334b Safari/531.21.10",
	"Blackberry" : "BlackBerry9530/4.7.0.65_Profile/MIDP-2.0_Configuration/CLDC-1.1_VendorID/105",
	"Opera" : "Opera/9.63 (Windows NT 5.1; U; en) Presto/2.1.1",
	"Opera-Mini" : "Opera/9.50 (J2ME/MIDP; Opera Mini/4.1.11355/574; U; en)",
	"Konqueror" : "Mozilla/5.0 (compatible; Konqueror/3.2; Linux) (KHTML, like Gecko)",
	"BlackSheep" : "Mozilla/5.0 (Windows; U; Windows NT 5.1; en-US) AppleWebKit/525.19 (KHTML, like Gecko) BlackSheep <http://neuroo.net>",
}
