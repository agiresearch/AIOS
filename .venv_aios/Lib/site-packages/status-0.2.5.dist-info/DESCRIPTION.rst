================
 status
================
----------------------------------------------
 HTTP status codes for GET and POST requests
----------------------------------------------

About
=============
status is a cross-platform command line application that returns the HTTP response status code for a GET or POST request to a user submitted URL.

It has been tested in cPython 2.7.x, 3.4.x and pypy 2.4.0 (Python v2.7.8)

Install
=============
You can install status with the Python package manager pip::

    pip install status

or download the source repository and run the following command in the top level source directory::

    python setup.py install

Upgrade
==============
You can upgrade status with pip. Use the following command::

    pip install --upgrade status

or download the source repository and use the above instructions for a new install from source.

Usage
=============
status will report the returned status code with a GET or POST request.  The general syntax is::

    status [option] <url>

It is not necessary to include the protocol (http://) in your URL. If you enter a URL without the protocol, status will prefix it with http://.  If you intend to test with the secure HTTP protocol (https://), then make this explicit in your URL.


GET Request Status Codes
------------------------------
GET is the default request type. Enter the URL as an argument to status without an option::

    status <url>



POST Request Status Codes
------------------------------
To use a POST request, add the ``-p`` or ``--post`` option::

    status -p <url>


Versions
=============

v0.2.5 - bug fix: connection error handling and new tests in cPython 2.7.9, 3.4.2 + pypy 2.4.0

v0.2.4 - updated application dependencies

v0.2.3 - updated application dependencies

v0.2.2 - minor bug fixes, documentation updates

v0.2.1 - exception handling for HTTP connection errors, help documentation updates

v0.2.0 - initial release



