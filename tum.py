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
import tempfile
import urllib

from optparse import OptionParser

# Contains various defaults for
DEFAULT_TUMBLR_API_CREDFILE = ".tum_creds"
DEFAULT_TUMBLR_API_SERVER = "api.tumblr.com"
DEFAULT_TUMBLR_API_URL = "https://%s/v2/%s"

# 
EDITOR = os.environ.get("EDITOR", "vim")


# Contains the Tumblr interaction modules supported by tum.
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
    for module in CLI_MODULES.keys():
      print("  %s - %s" % (module, CLI_MODULES[module][1]))  


class BaseModule(object):
  """
  Contains code used by all CLI-handing modules.
  """
  
  def __init__(self, usage, description):
    self.parser = OptionParser(usage, description=description)
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
  Contains handlers for posting content via the Tumblr API.
  """

  def audio_options(parser):
    group = OptionGroup(parser, "Audio Post Options")
    group.add_option("-c", "--caption", dest="caption", help="post caption",
        metavar="CAPTION")
    parser.add_option_group(group)

  def chat_options(parser):
    group = OptionGroup(parser, "Chat Post Options")
    group.add_option("-t", "--title", dest="title", help="post title",
        metavar="TITLE")
    parser.add_option_group(group)

  def code_options(parser):
    group = OptionGroup(parser, "Code Post Options")
    group.add_option("-t", "--title", dest="title", help="post title",
        metavar="TITLE")
    group.add_option("-d", "--disable-autocolor", dest="autocolor",
        action="store_true", default=False,
        help="disable the auto-colorization of code")
    parser.add_option_group(group)

  def link_options(parser):
    group = OptionGroup(parser, "Link Post Options")
    group.add_option("-d", "--description", dest="description",
        help="post description", metavar="DESCRIPTION")
    group.add_option("-t", "--title", dest="title", help="post title",
        metavar="TITLE")
    parser.add_option_group(group)

  def photo_options(parser):
    group = OptionGroup(parser, "Photo Post Options",
        "One or more photos can be posted
    group.add_option("-c", "--caption", dest="caption", help="post caption",
        metavar="CAPTION")
    group.add_option("-l", "--link", dest="link",
        help="the click-through URL for the photo", metavar="LINK")
    parser.add_option_group(group)

  def text_options(parser):
    group = OptionGroup(parser, "Text Post Options")
    group.add_option("-t", "--title", dest="title", help="post title",
        metavar="TITLE")
    parser.add_option_group(group)

  def video_options(parser):
    group = OptionGroup(parser, "Video Post Options")
    group.add_option("-c", "--caption", dest="caption", help="post caption",
        metavar="CAPTION")
    parser.add_option_group(group)
  
  # Contains all valid Tumblr post types.
  POST_TYPES = {
    "audio": audio_options,
    "chat": chat_options,
    "code": code_options,
    "link": link_options,
    "photo": photo_options,
    "quote": lambda f: (),
    "text": text_options,
    "video": video_options,
  }

  def __init__(self):
    BaseModule.__init__(self, "usage: %prog post <type> [options] <content>",
      "The post module allows you to post many different types of content to "
      "Tumblr from the command line.  In cases where you're posting content "
      "which must be uploaded, files on the local system and URLs are "
      "interchangeable, and depending upon the type of post, multiple files "
      "may be posted.  For instance:\n\n"
      " # tum post photo tony_banks.jpg http://genesis.com/philcollins.jpg\n\n"
      "For more information per post type, run a tum post <type> --help.")
       
    if argv[1] not in POST_TYPES:
      self.parser.print_usage()
      print("Error: Post type not recognized, available post types are: "
            "%s" % ", ".join(POST_TYPES.keys()))
      sys.exit(1)
    # Adds post-specific option parsing to parser.
    POST_TYPES[argv[1]](self.parser)

  def main(self, argv):
    
