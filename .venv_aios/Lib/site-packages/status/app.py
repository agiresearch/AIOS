#!/usr/bin/env python
# encoding: utf-8

#------------------------------------------------------------------------------
# status
# Copyright 2015 Christopher Simpkins
# MIT license
#------------------------------------------------------------------------------


#------------------------------------------------------------------------------------
# c.cmd = Primary command (<executable> <primary command>)
# c.cmd2 = Secondary command (<executable> <primary command> <secondary command>)
#
# c.option(option_string, [bool argument_required]) = test for option with optional positional argument to option test
# c.option_with_arg(option_string) = test for option and mandatory positional argument to option
# c.flag(flag_string) = test for presence of a "option=argument" style flag
#
# c.arg(arg_string) = returns the next positional argument to the arg_string argument
# c.flag_arg(flag_string) = returns the flag assignment for a "--option=argument" style flag
#------------------------------------------------------------------------------------

# Application start
def main():
    import sys
    from Naked.commandline import Command
    #from Naked.toolshed.state import StateObject
    from Naked.toolshed.system import stderr, exit_success, exit_fail
    from status.commands.http_request import Get, Post

    #------------------------------------------------------------------------------------------
    # [ Instantiate command line object ]
    #   used for all subsequent conditional logic in the CLI application
    #------------------------------------------------------------------------------------------
    c = Command(sys.argv[0], sys.argv[1:])
    #------------------------------------------------------------------------------
    # [ Instantiate state object ]
    #------------------------------------------------------------------------------
    # state = StateObject()
    #------------------------------------------------------------------------------------------
    # [ Command Suite Validation ] - early validation of appropriate command syntax
    # Test that user entered a primary command, print usage if not
    #------------------------------------------------------------------------------------------
    if not c.command_suite_validates():
        from status.commands.usage import Usage
        Usage().print_usage()
        exit_fail()

    #------------------------------------------------------------------------------------------
    # [ NAKED FRAMEWORK COMMANDS ]
    # Naked framework provides default help, usage, and version commands for all applications
    #   --> settings for user messages are assigned in the lib/status/settings.py file
    #------------------------------------------------------------------------------------------
    if c.help():  # User requested naked help (help.py module in commands directory)
        from status.commands.help import Help
        Help().print_help()
    elif c.usage():  # user requested naked usage info (usage.py module in commands directory)
        from status.commands.usage import Usage
        Usage().print_usage()
    elif c.version(): # user requested naked version (version.py module in commands directory)
        from status.commands.version import Version
        Version().print_version()
    #------------------------------------------------------------------------------------------
    # [ PRIMARY COMMAND LOGIC ]
    #   Enter your command line parsing logic below
    #------------------------------------------------------------------------------------------

    # POST request
    elif c.option("-p") or c.option("--post"):
        if c.arg1:
            post = Post(c.arg1)
            post.post_response()
        else:
            stderr("Please enter a URL to test.", 1)

    # GET request
    elif len(c.arg0) > 0:
        get = Get(c.arg0)
        get.get_response()

    #------------------------------------------------------------------------------------------
    # [ DEFAULT MESSAGE FOR MATCH FAILURE ]
    # Message to provide to the user when all above conditional logic fails to meet a true condition
    #------------------------------------------------------------------------------------------
    else:
        stderr("Please enter a URL to test.", 1)

if __name__ == '__main__':
    main()
