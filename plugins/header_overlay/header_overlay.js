/*
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
*/

// Display the Headers in the page; this is pretty ugly code but anyway...
$(document).ready(function() {
	if (sheep_headers) {
		$("body").append("<div id='sheep_headers' />");
		$("#sheep_headers").append("<div id='sheep_header_top'>" + sheep_headers["method"] + "&nbsp;" + sheep_headers["request"]["url"] + "</div>");
		$("#sheep_headers").append("<div id='sheep_header_request' />").append("<div id='sheep_header_response' />");

		for (var i=0; i<sheep_headers["request"]["headers"].length; i++) {
			var div_elmt = "sheep_header_request_" + i;
			$("#sheep_header_request").append("<div id='" + div_elmt + "'>");
			$("#" + div_elmt + "").text(sheep_headers["request"]["headers"][i][0] + ": " + sheep_headers["request"]["headers"][i][1]).html();
		}
		if (0 < sheep_headers["request"]["content"].length) {
			$("#sheep_header_request").append("<div id='sheep_header_request_content'>");
			$("#sheep_header_request_content").text(sheep_headers["request"]["content"]);
			$("#sheep_header_request_content").css("border-top", "1px dashed #999").css("margin", "5px").css("padding", "2px");
		}
		$("#sheep_header_request").css("color", "#999").css("font", "12px verdana").css("padding", "11px").css("width", 770);
		$("#sheep_headers").css("background-color", "#efefef").css("color", "black").css("font", "14px verdana").css("padding", "10px").css("border", "2px solid black");
		$("#sheep_headers").dialog({ width: 800 });
	}
});
