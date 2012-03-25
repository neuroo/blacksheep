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

HTTP_MESSAGES = {
  100: ("Continue"," Only a part of the request has been received by the server, but as long as it has not been rejected, the client should continue with the request")
, 101: ("Switching Protocols","The server switches protocol")
, 200: ("OK","The request is OK")
, 201: ("Created","The request is complete, and a new resource is created")
, 202: ("Accepted","The request is accepted for processing, but the processing is not complete")
, 203: ("Non-authoritative Information","")
, 204: ("No Content","")
, 205: ("Reset Content","")
, 206: ("Partial Content","")
, 300: ("Multiple Choices","A link list. The user can select a link and go to that location. Maximum five addresses")
, 301: ("Moved Permanently","The requested page has moved to a new url")
, 302: ("Found","The requested page has moved temporarily to a new url")
, 303: ("See Other","The requested page can be found under a different url")
, 304: ("Not Modified","")
, 305: ("Use Proxy","")
, 306: ("Unused","This code was used in a previous version. It is no longer used, but the code is reserved")
, 307: ("Temporary Redirect","The requested page has moved temporarily to a new url")
, 400: ("Bad Request","The server did not understand the request")
, 401: ("Unauthorized","The requested page needs a username and a password")
, 402: ("Payment Required","You can not use this code yet")
, 403: ("Forbidden","Access is forbidden to the requested page")
, 404: ("Not Found","The server can not find the requested page")
, 405: ("Method Not Allowed","The method specified in the request is not allowed")
, 406: ("Not Acceptable","The server can only generate a response that is not accepted by the client")
, 407: ("Proxy Authentication Required","You must authenticate with a proxy server before this request can be served")
, 408: ("Request Timeout","The request took longer than the server was prepared to wait")
, 409: ("Conflict","The request could not be completed because of a conflict")
, 410: ("Gone","The requested page is no longer available")
, 411: ("Length Required","The \"Content-Length\" is not defined. The server will not accept the request without it")
, 412: ("Precondition Failed","The precondition given in the request evaluated to false by the server")
, 413: ("Request Entity Too Large","The server will not accept the request, because the request entity is too large")
, 414: ("Request-url Too Long","The server will not accept the request, because the url is too long. Occurs when you convert a POST request to a GET request with a long query information")
, 415: ("Unsupported Media Type","The server will not accept the request, because the media type is not supported")
, 416: ("","")
, 417: ("Expectation Failed","")
, 500: ("Internal Server Error","The request was not completed. The server met an unexpected condition")
, 501: ("Not Implemented","The request was not completed. The server did not support the functionality required")
, 502: ("Bad Gateway","The request was not completed. The server received an invalid response from the upstream server")
, 503: ("Service Unavailable","The request was not completed. The server is temporarily overloading or down")
, 504: ("Gateway Timeout","The gateway has timed out")
, 505: ("HTTP Version Not Supported","The server does not support the \"http protocol\" version")
}
