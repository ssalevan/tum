#!/usr/bin/python
#
# tumblr_client

import ConfigParser
import urlparse
import oauth2 as oauth


# Contains default URLs for authorizing to Tumblr's OAuth API.
REQUEST_TOKEN_URL = "http://www.tumblr.com/oauth/request_token?oauth_callback=http://localhost/tum"
AUTHORIZE_URL = "http://www.tumblr.com/oauth/authorize"
ACCESS_TOKEN_URL = "http://www.tumblr.com/oauth/access_token"


def generate_tumblr_credentials(credfile_loc):
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
    print content
    raise Exception("Invalid response %s." % resp['status'])

  request_token = dict(urlparse.parse_qsl(content))

  print("Next, we're going to use a somewhat odd method to get the last")
  print("piece of information we need, the oauth_verifier.  Go to the")
  print("following link in your browser and authorize me:\n")
  print("%s?oauth_token=%s\n" % (AUTHORIZE_URL, request_token['oauth_token']))
  print("This will redirect you to a page at your local host, and within the")
  print("URL bar you should see something that says oauth_verifier=<stuff>.\n")
  print("Copy this information down, as you'll need it in the next step.")

  accepted = "n"
  while accepted.lower() == "n":
    accepted = raw_input("Have you authorized me? (y/n)> ")

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
  config.set("Credentials", "oauth_token", access_token["oauth_token"])
  config.set("Credentials", "oauth_token_secret",
      access_token["oauth_token_secret"])
  with open(credfile_loc, "wb") as credfile:
    config.write(credfile)
  print("Hooray!  Successfully stored Tumblr credentials at: %s" % credfile_loc)


class TumblrClient(object):
  def __init__(self, oauth_token, oauth_token_secret):
    self.oauth_token = oauth_token
    self.oauth_token_secret = oauth_token_secret
