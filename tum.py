#!/usr/bin/python
#
# tum - a command-line client for Tumblr
# 
# Author: Steve Salevan <steve.salevan@gmail.com>
#
# Tumblr is a great site, but I thought that it'd be more awesome if you could
# use its power a bit more like a mutant hybrid of git and mutt.  If you feel
# similarly, tum may just be right up your alley.
#
# Special thanks go to dgoodwin@redhat.com, as much of the command-line handling
# was based off of patterns found in Tito (https://github.com/dgoodwin/tito).
# RHN fo'lyfe, yall.


import ConfigParser
import httplib2
import os
import sys
import urllib

from optparse import OptionParser

# Various defaults for
DEFAULT_TUMBLR_API_CREDFILE = ".tum_creds"
DEFAULT_TUMBLR_API_SERVER = "api.tumblr.com"
DEFAULT_TUMBLR_API_URL = "https://%s/v2/%s"


# Modules supported by tum
CLI_MODULES = {
  "dash": (DashModule, "open your dashboard"),
  "post": (PostModule, "make a post"),
  "pull": (PullModule, "download content from a post"),
}


class CLIHandler(object):
  """
  """
  
  def main(self, argv):
    if len(argv) < 1 or not argv[0] in CLI_MODULES.keys():
      self._usage()
      sys.exit(1)
    module_class = CLI_MODULES[argv[0]]
    module = module_class()
    return module.main(argv)
    
  def _usage(self):
    print("Usage: tum ACTION --help")
    print("Actions:")
    for module in CLI_MODULES:
      print("  %s - %s" % (module, CLI_MODULES[module][1]))  


class BaseModule(object):
  """
  Contains code used by all CLI-handing modules.
  """
  
  def __init__(self, usage):
    self.parser = OptionParser(usage)
    self._add_common_options()
    
  def _add_common_options(self):
    self.parser.add_option("-s", "--server", dest="server",
        help="use this Tumblr server", metavar="SERVER",
        default=DEFAULT_TUMBLR_API_SERVER)
    parser.add_option("-x", "--credentials", dest="credentials",
        help="use this Tumblr credentials file", metavar="CREDFILE")
    parser.add_option("-a", "--authenticate", dest="authenticate",
        action="store_true", default=False, help="authenticate to Tumblr")
    parser.add_option("-i", "--stdin", dest="stdin",
        action="store_true", default=False, help="read input from STDIN")
    parser.add_option("-q", "--quiet", dest="quiet",
        action="store_true", default=False, help="enable quiet mode")


class PostModule(BaseModule):
  """
  Contains Tumblr post functionality
  """
  
  POST_TYPES = set([
    "answer",
    "audio",
    "chat",
    "code",
    "link",
    "text",
    "photo",
    "video",
  ])


  def __init__(self):
    BaseModule.__init__(self, "usage: %prog post <type> [content] [options]")
  
  def main(self, argv):
    
    
