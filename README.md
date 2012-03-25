# BlackSheep

Security tool that enables security analysis and penetration testing, BlackSheep is a framework which focuses on augmenting manual pen-test by providing information to the tester. BlackSheep also keeps track of every testing steps employed by the pen-tester and facilitates the storage of the results and test cases. 

## Screenshots

- [Application flow graph](https://github.com/neuroo/blacksheep/raw/master/screenshot/app_flow_graph.png)
- [Precise client-side actions recording](https://github.com/neuroo/blacksheep/raw/master/screenshot/client_side_selectors.png)
- [You can view stuff!](https://github.com/neuroo/blacksheep/raw/master/screenshot/content_viewer.png)
- [Adding findings with a click](https://github.com/neuroo/blacksheep/raw/master/screenshot/findings_management.png)
- [Full blown web browser (built on top of WebKit)](https://github.com/neuroo/blacksheep/raw/master/screenshot/web_browser.png)

## Current features

- Support of common web technologies: web engine using WebKit (Qt port) to render JavaScript and CSS, support of netscape plugins for Flash, Silverlight, etc.
- HTTP requests tampering (GET, POST, Cookie and Headers) by interception or request replay
- Exploited XSS that trigger an alert/prompt will be automatically added to findings (based on JavaScript engine runtime events monitoring), using the _sheep testing_ mode
- Findings collection based on custom data structure, easy creation of findings based on HTTP history.
- History of HTTP requests and responses
- Web application informations for pen-testers: Site structure (simple tree sitemap), Application Flow Map with heuristics and view of all information for each node, Source code/DOM view with search, WebKit Inspector available for all pages, Record of user interactions (clicks, keyboard, etc.) on each web pages (Test case tab)
- Partial support of URL rewriting rules
- Direct JavaScript injection in DOM
- Different transcoders available for charsets, encodings (URL encoding, Base64, etc.)
- JavaScript and Python plugins support

## Dependencies

- Python 2.6, or 2.7
- PyQt4 (version 4.7.0 or higher)
- python-graph (version 1.7 or higher)

On OSX, you can get PyQt4 using [macports](http://macports.org):

	sudo port install py27-pyqt4

And `python-graph` can be fetch using [easy_install](http://pypi.python.org/pypi/setuptools):
	
	easy_install python-graph-core

The windows version of PyQt4 can be downloaded at [riverbankcomputing](http://www.riverbankcomputing.co.uk/software/pyqt/download), and for Ubuntu's using `apt-get`.

## Running BlackSheep

To launch the GUI, you simply need to run `sheep.py`:

	python sheep.py

that should be it.