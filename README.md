# BlackSheep

Security tool that enables security analysis and penetration testing, BlackSheep is a framework which focuses on augmenting manual pen-test by providing information to the tester. BlackSheep also keeps track of every testing steps employed by the pen-tester and facilitates the storage of the results and test cases. 

## Current features

- Support of common web technologies: web engine using WebKit (Qt port) to render JavaScript and CSS, support of netscape plugins for Flash, Silverlight, etc.
- HTTP requests tampering (GET, POST, Cookie and Headers) by interception or request replay
- Exploited XSS that trigger an alert/prompt will be automatically added to findings (based on JavaScript engine runtime events monitoring)
- Findings collection based on custom data structure, easy creation of findings based on HTTP history. Export in OFS (Open Finding Schema) later on
- History of HTTP requests and responses
- Web application informations for pen-testers: Site structure (simple tree sitemap), Application Flow Map with heuristics and view of all information for each node, Source code/DOM view with search, WebKit Inspector available for all pages, Record of user interactions (clicks, keyboard, etc.) on each web pages (Test case tab)
- Partial support of URL rewriting rules
- Direct JavaScript injection in DOM
- Different transcoders available for charsets, encodings (URL encoding, Base64, etc.)
- JavaScript and Python plugins support
