#!/usr/bin/python
#
# tum - a command-line client for Tumblr
# 
# Author: Steve Salevan <steve.salevan@gmail.com>
#
# Tumblr is a great site, but I thought that it'd be more awesome if you could
# use its power a bit more like a mutant hybrid of git and mutt.  If you feel
# similarly, tum might just be right up your alley.
#
# Special thanks go to dgoodwin@redhat.com, as much of the command-line handling
# was based off of patterns found in Tito (https://github.com/dgoodwin/tito).
# RHN fo'lyfe, yall.

import ConfigParser
import os
import sys
import tempfile
import urllib

from optparse import OptionGroup
from optparse import OptionParser

# tum module-specific imports
import tumblr_client

# Contains various defaults for interacting with the Tumblr API.
DEFAULT_TUM_CREDFILE = ".tum_creds"
DEFAULT_TUMRC = ".tumrc"

# Contains the default Tumblr API server to point tum at.
DEFAULT_TUMBLR_API_SERVER = "api.tumblr.com"

# Contains the default editor used by this environment.
EDITOR = os.environ.get("EDITOR", "vim")

# What can I say, I'm a sucker for ASCII art.
TUM_LOGO = """    .                                     
  .o8                                     
.o888oo oooo  oooo  ooo. .oo.  .oo.       
  888   `888  `888  `888P"Y88bP"Y88b      
  888    888   888   888   888   888      
  888 .  888   888   888   888   888  
  "888"  `V88V"V8P' o888o o888o o888o #"""


def AudioOptions(parser):
  """
  Stores CLI options specific to Audio posts.
  """
  group = OptionGroup(parser, "Audio Post Options")
  group.add_option("-c", "--caption", dest="caption", help="post caption",
      metavar="CAPTION")
  parser.add_option_group(group)


def ChatOptions(parser):
  """
  Stores CLI options specific to Chat posts.
  """
  group = OptionGroup(parser, "Chat Post Options")
  group.add_option("-t", "--title", dest="title", help="post title",
      metavar="TITLE")
  parser.add_option_group(group)


def CodeOptions(parser):
  """
  Stores CLI options specific to Code posts.
  """
  group = OptionGroup(parser, "Code Post Options")
  group.add_option("-t", "--title", dest="title", help="post title",
      metavar="TITLE")
  group.add_option("-d", "--disable-autocolor", dest="autocolor",
      action="store_true", default=False,
      help="disable the auto-colorization of code")
  parser.add_option_group(group)


def LinkOptions(parser):
  """
  Stores CLI options specific to Link posts.
  """
  group = OptionGroup(parser, "Link Post Options")
  group.add_option("-d", "--description", dest="description",
      help="post description", metavar="DESCRIPTION")
  group.add_option("-t", "--title", dest="title", help="post title",
      metavar="TITLE")
  parser.add_option_group(group)


def PhotoOptions(parser):
  """
  Stores CLI options specific to Photo posts.
  """
  group = OptionGroup(parser, "Photo Post Options")
  group.add_option("-c", "--caption", dest="caption", help="post caption",
      metavar="CAPTION")
  group.add_option("-l", "--link", dest="link",
      help="the click-through URL for the photo", metavar="LINK")
  parser.add_option_group(group)


def TextOptions(parser):
  """
  Stores CLI options specific to Text posts.
  """
  group = OptionGroup(parser, "Text Post Options")
  group.add_option("-t", "--title", dest="title", help="post title",
      metavar="TITLE")
  parser.add_option_group(group)


def VideoOptions(parser):
  """
  Stores CLI options specific to Video posts.
  """
  group = OptionGroup(parser, "Video Post Options")
  group.add_option("-c", "--caption", dest="caption", help="post caption",
      metavar="CAPTION")
  parser.add_option_group(group)


# Contains a mapping of all valid Tumblr post types to the functions which
# specify CLI options specific to each use case.
POST_TYPES = {
  "audio": AudioOptions,
  "chat": ChatOptions,
  "code": CodeOptions,
  "link": LinkOptions,
  "photo": PhotoOptions,
  "quote": lambda f: (),
  "text": TextOptions,
  "video": VideoOptions,
}


class TumError(Exception):
  """
  Catch-all for exceptions thrown during tum execution.
  """
  pass


class CLIHandler(object):
  """
  Handles basic error checking and initializes the requested tum module.
  """

  def main(self, argv):
    if len(argv) < 1 or not argv[0] in CLI_MODULES.keys():
      self._usage()
      sys.exit(1)
    module_class = CLI_MODULES[argv[0]][0]
    module = module_class()
    return module.main(argv)

  def _usage(self):
    print(TUM_LOGO + "\n")
    print("Usage: tum ACTION --help\n")
    print("Actions:")
    for module in CLI_MODULES.keys():
      print("  %s - %s" % (module, CLI_MODULES[module][1]))  


class BaseModule(object):
  """
  Contains code used by all CLI-handing modules.
  """

  def __init__(self, usage, description):
    self.args = None
    self.options = None
    self.tum_creds = None
    self.tumblr_client = None
    self.parser = OptionParser(usage, description=description)
    self._add_common_options()

  def _add_common_options(self):
    self.parser.add_option("-s", "--server", dest="server",
        help="specifies a custom Tumblr API server", metavar="SERVER",
        default=DEFAULT_TUMBLR_API_SERVER)
    self.parser.add_option("-x", "--credentials", dest="credentials",
        help="specifies a custom location for the credentials file",
        metavar="CREDFILE")
    self.parser.add_option("-q", "--quiet", dest="quiet",
        action="store_true", default=False, help="enable quiet mode")

  def _read_credentials(self, credfile_loc):
    self.tum_creds = ConfigParser.RawConfigParser()
    self.tum_creds.read(credfile_loc)

  def main(self, argv):
    # Parses command-line arguments.
    (self.options, self.args) = self.parser.parse_args(argv)

    # Figures out where the OAuth credentials file should land
    credfile_loc = "%s/%s" % (os.getenv("HOME"), DEFAULT_TUM_CREDFILE)
    if self.options.credentials:
      credfile_loc = self.options.credentials
    # Authenticates to Tumblr OAuth API if no credential file exists.
    if not os.path.exists(credfile_loc):
      print("ERROR: no Tumblr credentials file found at %s." % credfile_loc)
      try:
        tumblr_client.GenerateTumblrCredentials(credfile_loc)
      except TumError, e:
        print("An error occurred while reading your credentials file:")
        print(e.message)
        sys.exit(-1)
    try:
      self._read_credentials(credfile_loc)
    except Exception, e:
      print("An error occurred while reading your credentials file:")
      print(e.message)
      sys.exit(-1)

    # Initializes the Tumblr client.
    self.tumblr_client = tumblr_client.TumblrClient(
        self.tum_creds.get("Credentials", "api_key"),
        self.tum_creds.get("Credentials", "oauth_token"),
        self.tum_creds.get("Credentials", "oauth_token_secret"),
        self.options.server)


class AuthModule(BaseModule):
  """
  Contains CLI handlers for authenticating via OAuth to the Tumblr API.
  """

  def __init__(self):
    BaseModule.__init__(self, "usage: %prog auth [options]",
        "The authorization module authenticates to Tumblr via OAuth and stores "
        "the credentials in either a default location in your home directory "
        "or a location of your choosing.")

  def main(self, argv):
    # Parses command-line arguments.
    (self.options, self.args) = self.parser.parse_args(argv)
    # Figures out where the OAuth credentials file should land
    credfile_loc = "%s/%s" % (os.getenv("HOME"), DEFAULT_TUM_CREDFILE)
    if self.options.credentials:
      credfile_loc = self.options.credentials
    # Prompts the user if the file already exists.
    if os.path.exists(credfile_loc):
      print("Warning: a credentials file already exists at %s." % credfile_loc)
      overwrite = ""
      while not (overwrite.lower() == "y") or (overwrite.lower() == "n"):
        overwrite = raw_input("Overwrite? (y/n)> ")
      if overwrite == "n":
        sys.exit(0)
    try:
      tumblr_client.GenerateTumblrCredentials(credfile_loc)
    except TumError, e:
      print("ERROR: Tumblr OAuth authentication failed:")
      print(e.message)
      sys.exit(-1)
    sys.exit(0)


class PostModule(BaseModule):
  """
  Contains CLI handlers for posting content via the Tumblr API.
  """

  def __init__(self):
    BaseModule.__init__(self, "usage: %prog post [options] <type> <content>",
        "The post module allows you to post many different types of content to "
        "Tumblr from the command line.  In cases where you're posting content "
        "which must be uploaded, files on the local system and URLs are "
        "interchangeable, and depending upon the type of post, multiple files "
        "may be posted.  For instance:\n\n"
        " # tum post photo tony_banks.jpg http://genesis.com/philcollins.jpg")
    self.parser.add_option("-b", "--blog", dest="blog",
        metavar="BLOG", help="specifies a blog")
    self.parser.add_option("-i", "--stdin", dest="stdin",
        action="store_true", default=False, help="read input from STDIN")
    self.parser.add_option("-S", "--state", dest="state",
        default="published", metavar="STATE",
        help="the state of the post: published, draft, queue")
    self.parser.add_option("-T", "--tags", dest="tags",
        metavar="TAGS", help="comma-separated tags for this post")

  def _get_file(self, argv):
    return open(argv[2], 'r').read()

  def main(self, argv):
    if len(argv) < 2 or argv[1] not in POST_TYPES:
      self.parser.print_usage()
      print("ERROR: Post type not recognized, available post types are:")
      print("%s" % ", ".join(POST_TYPES.keys()))
      sys.exit(1)
    # Adds post-specific option parsing to parser.
    POST_TYPES[argv[1]](self.parser)
    BaseModule.main(self, argv)
    # Populates a request to the API and sends it.
    post_params = {}
    post_params["type"] = argv[1]
    if self.parser.state:
      post_params["state"] = self.parser.state
    if self.parser.tags:
      post_params["tags"] = self.parser.tags
    if "text" in post_params["type"]:
      if self.parser.title:
        post_params["title"] = self.parser.title
      if self.parser.stdin:
        post_params["body"] = sys.stdin.read()
      else:
        post_params["body"] = self._get_file(argv[2])
    self.tumblr_client.create_post(self.parser.blog, post_params)


# Contains the Tumblr interaction modules supported by tum.
CLI_MODULES = {
  "auth": (AuthModule, "authenticate to Tumblr"),
#  "dash": (DashModule, "open your dashboard"),
  "post": (PostModule, "make a post"),
#  "pull": (PullModule, "download content from a post"),
}


if __name__ in "__main__":
  ch = CLIHandler()
  ch.main(sys.argv[1:])
