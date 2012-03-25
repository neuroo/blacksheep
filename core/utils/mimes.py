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

# text considered as application
TYPES_MIME = ('image', 'application', 'audio', 'video')

def probe_mime(mime):
	if not isinstance(mime, str):
		mime = str(mime)
	mime = mime.lower()
	if '/' not in mime:
		return 'application'
	mime = mime[:mime.find('/')]
	if mime not in TYPES_MIME:
		return 'application'
	return mime

LIST_MIMES = """application/java
application/java-archive
application/mac-binhex40
application/msexcel
application/mspowerpoint
application/msproject
application/msword
application/octet-stream
application/octet-stream
application/oda
application/pdf
application/postscript
application/postscript
application/postscript
application/rtf
application/vnd.rn-realmedia
application/vnd.wap.wmlc
application/vnd.wap.wmlscriptc
application/x-aim
application/x-bcpio
application/x-cdf
application/x-compress
application/x-cpio
application/x-csh
application/x-dvi
application/x-gtar
application/x-gzip
application/x-hdf
application/x-java-jnlp-file
application/x-latex
application/x-mif
application/x-netcdf
application/x-sh
application/x-shar
application/x-shockwave-flash
application/x-sv4cpio
application/x-sv4crc
application/x-tar
application/x-tcl
application/x-tex
application/x-texinfo
application/x-texinfo
application/x-troff
application/x-troff
application/x-troff
application/x-troff-man
application/x-troff-me
application/x-ustar
application/x-wais-source
application/x-wais-source
application/x-x509-ca-cert
application/zip
audio/basic
audio/basic
audio/basic
audio/x-aiff
audio/x-aiff
audio/x-aiff
audio/x-midi
audio/x-midi
audio/x-midi
audio/x-midi
audio/x-mpeg
audio/x-mpeg
audio/x-mpeg
audio/x-mpeg
audio/x-mpeg
audio/x-mpeg
audio/x-mpegurl
audio/x-scpls
audio/x-wav
image/bmp
image/bmp
image/gif
image/ief
image/jpeg
image/jpeg
image/jpeg
image/pict
image/pict
image/pict
image/png
image/svg+xml
image/svg+xml
image/tiff
image/tiff
image/vnd.wap.wbmp
image/x-cmu-raster
image/x-jg
image/x-macpaint
image/x-macpaint
image/x-photoshop
image/x-portable-anymap
image/x-portable-bitmap
image/x-portable-graymap
image/x-portable-pixmap
image/x-quicktime
image/x-quicktime
image/x-rgb
image/x-xbitmap
image/x-xpixmap
image/x-xwindowdump
text/css
text/html
text/html
text/html
text/javascript
text/plain
text/plain
text/plain
text/plain
text/plain
text/richtext
text/tab-separated-values
text/vnd.sun.j2me.app-descriptor
text/vnd.wap.wml
text/vnd.wap.wmlscript
text/x-component
text/xml
text/xml
text/x-setext
video/mpeg
video/mpeg
video/mpeg
video/mpeg2
video/quicktime
video/quicktime
video/x-dv
video/x-ms-asf
video/x-ms-asf
video/x-msvideo
video/x-rad-screenplay
video/x-sgi-movie
x-world/x-vrml""".split('\n')
