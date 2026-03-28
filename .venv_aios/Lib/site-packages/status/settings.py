#!/usr/bin/env python
# encoding: utf-8

#------------------------------------------------------------------------------
# Application Name
#------------------------------------------------------------------------------
app_name = 'status'

#------------------------------------------------------------------------------
# Version Number
#------------------------------------------------------------------------------
major_version = "0"
minor_version = "2"
patch_version = "5"

#------------------------------------------------------------------------------
# Debug Flag (switch to False for production release code)
#------------------------------------------------------------------------------
debug = False

#------------------------------------------------------------------------------
# Usage String
#------------------------------------------------------------------------------
usage = """
Usage: status [option(s)] <url>
"""

#------------------------------------------------------------------------------
# Help String
#------------------------------------------------------------------------------
help = """
---------------------------------------
 status
 Copyright 2015 Christopher Simpkins
 MIT license
---------------------------------------

Status reports the HTTP response status code(s) for GET and POST requests.

USAGE
  status [-p --post] <url>

OPTIONS
  -p  --post    POST request

The default is a GET request.  You can modify this to use a POST request with the -p or --post option.

The URL argument can be entered with or without the protocol. If you do not enter a protocol (http:// or https://), then http:// is assumed.  If you intend to test with the secure HTTP protocol, then make this explicit in your URL.

EXAMPLES
  status http://google.com
  status https://www.google.com
  status google.com
  status -p httpbin.org/post

SOURCE REPOSITORY
  https://github.com/chrissimpkins/status

ISSUE TRACKING
  https://github.com/chrissimpkins/status/issues
  """

