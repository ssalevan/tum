#!/usr/bin/python
#
# tumblr_client

import ConfigParser
import httplib2
import oauth2 as oauth
import os
import urllib
import urlparse

from tum import TumError

# Contains default URLs for authorizing to Tumblr's OAuth API.
REQUEST_TOKEN_URL = "http://www.tumblr.com/oauth/request_token?oauth_callback=http://localhost/tum"
AUTHORIZE_URL = "http://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "http://www.tumblr.com/oauth/access_token"

# Contains the default location for the cache of all Tumblr content.
DEFAULT_CACHE_LOC = ".tum_cache"

TUMBLR_API_URL = "https://%s/v2/%s"

def GenerateTumblrCredentials(credfile_loc):
  print("To enable communication with Tumblr, we must first register tum as")
  print("an OAuth app.  To do so, log into Tumblr and visit this URL:\n")
  print("http://www.tumblr.com/oauth/register\n")
  print("Enter anything you want into the fields then find the following info:")

  consumer_key = raw_input("OAuth Consumer Key> ")
  consumer_secret = raw_input("Secret Key> ")

  consumer = oauth.Consumer(consumer_key, consumer_secret)
  client = oauth.Client(consumer)

  resp, content = client.request(REQUEST_TOKEN_URL, "GET")
  if resp['status'] != '200':
    raise TumError("Invalid response %s: %s" % (resp['status'], content))

  request_token = dict(urlparse.parse_qsl(content))

  print("Next, we're going to use a somewhat odd method to get the last")
  print("piece of information we need, the oauth_verifier.  Go to the")
  print("following link in your browser and authorize me:\n")
  print("%s?oauth_token=%s\n" % (AUTHORIZE_URL, request_token['oauth_token']))
  print("This will redirect you to a page at your local host, and within the")
  print("URL bar you should see something that says oauth_verifier=<stuff>.\n")
  print("Copy this information down, as you'll need it in the next step.\n")

  oauth_verifier = raw_input("Enter the oauth_verifier from your URL bar> ")

  token = oauth.Token(request_token['oauth_token'],
      request_token['oauth_token_secret'])
  token.set_verifier(oauth_verifier)
  client = oauth.Client(consumer, token)

  resp, content = client.request(ACCESS_TOKEN_URL, "POST")
  access_token = dict(urlparse.parse_qsl(content))

  # Stores credentials into a config file at the supplied location
  config = ConfigParser.RawConfigParser()
  config.add_section("Credentials")
  config.set("Credentials", "api_key", consumer_key)
  config.set("Credentials", "oauth_token", access_token["oauth_token"])
  config.set("Credentials", "oauth_token_secret",
      access_token["oauth_token_secret"])
  with open(credfile_loc, "wb") as credfile:
    config.write(credfile)
  # Gives the credentials file some sane file permissions.
  os.chmod(credfile_loc, 0600)
  print("Huzzah!  Successfully stored Tumblr credentials at: %s" % credfile_loc)


class TumblrClient(object):
  """
  Handles all interaction with the Tumblr API.
  """

  def __init__(self, api_key, oauth_token, oauth_token_secret,
      api_server, cache_loc=None):
    self.api_key = api_key
    self.api_server = api_server
    self.oauth_token = oauth_token
    self.oauth_token_secret = oauth_token_secret
    if not cache_loc:
      cache_loc = "%s/%s" % (os.getenv("HOME"), DEFAULT_CACHE_LOC)
    self.http_client = oauth.Client(
        oauth.Consumer(self.api_key, self.oauth_token_secret),
        cache=cache_loc)

  def create_post(self, blog, params={}):
    resp, content = self.http_client.request(
        TUMBLR_API_URL % (api_server, "/blog/%s/post" % blog),
        method="POST", body=urlencode(params))
    if resp['status'] != '200':
      raise TumError(
          "Post creation failed (HTTP %s): %s" % (resp['status'], content))
