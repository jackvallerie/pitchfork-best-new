"""
pitch_scrape.py
Jack Vallerie

Retrieves the most recent posting of 'Best New Track' and 'Best New Album'
from Pitchfork Music's website and sends a text message to a specified
number with the track/album info and links to the track/album on Spotify

"""

import os, sys, regex, spotipy, requests
from lxml import html
from dotenv import load_dotenv
import spotipy.util as util
from twilio.rest import Client


#################
### CONSTANTS
load_dotenv()
SPOTIFY_USERNAME = os.environ['SPOTIFY_USERNAME']
RECIPIENT_PHONE_NUMBER = os.environ['RECIPIENT_PHONE_NUMBER']
SPOTIFY_CLIENT_ID = os.environ['SPOTIFY_CLIENT_ID']
SPOTIFY_CLIENT_SECRET = os.environ['SPOTIFY_CLIENT_SECRET']
TWILIO_ACCOUNT_SID = os.environ['TWILIO_ACCOUNT_SID']
TWILIO_AUTH_TOKEN = os.environ['TWILIO_AUTH_TOKEN']
TWILIO_PHONE_NUMBER = os.environ['TWILIO_PHONE_NUMBER']

#################


def main():

    # authenticate Spotify API keys
    token = util.prompt_for_user_token(SPOTIFY_USERNAME, scope='user-library-read',
                                       client_id=SPOTIFY_CLIENT_ID,
                                       client_secret=SPOTIFY_CLIENT_SECRET,
                                       redirect_uri='http://localhost:8000/')
    sp    = spotipy.Spotify(auth=token)


    # get info from HTML and clean it
    [album_artist, album_title,
     track_artist, track_title] = scrapeInfo()
    [album_title, track_title] = cleanStrings(album_title[0], track_title[0])
    album_artist = album_artist[0]
    track_artist = track_artist[0]


    # Find Spotify links, build SMS, send message
    [album_url, track_url] = getURLs(album_artist, album_title, track_artist, track_title, sp)
    message = buildMessage(album_title, album_artist, album_url, track_title, track_artist, track_url)
    sendSMS(message)
    print(message)





########################################
###  HELPER FUNCTIONS
########################################

# scrapes necessary info from Pitchfork 'Best New' webpage
def scrapeInfo():
    page = requests.get('http://pitchfork.com/best/')
    tree = html.fromstring(page.content)
    
    # retrieve text from HTML
    album_artist = tree.xpath('//*[@id="best-new-overview"]/div/div/div[1]' + \
                                    '/div/a/div[2]/h3[1]/ul/li/text()')
    album_title  = tree.xpath('//*[@id="best-new-overview"]/div/div/div[1]' + \
                                    '/div/a/div[2]/h3[2]/text()')
    track_artist = tree.xpath('//*[@id="best-new-overview"]/div/div/div[2]' + \
                                    '/div/a/div[2]/h3[1]/ul/li/text()')
    track_title  = tree.xpath('//*[@id="best-new-overview"]/div/div/div[2]' + \
                                    '/div/a/div[2]/h3[2]/text()')

    return [album_artist, album_title, track_artist, track_title]


# strip strings of newline chars and remove unicode on track title
def cleanStrings(album_title, track_title):
    album_title = album_title.rstrip()
    track_title = track_title.rstrip()
    track_title = regex.sub('\xe2\x80\x9c','', track_title)
    track_title = regex.sub('\xe2\x80\x9d','', track_title)
    return [album_title, track_title]


# get Spotify URLs for best new track and best new album 
def getURLs(album_artist, album_title, track_artist, track_title, sp):
    # run searches
    albumSearch = sp.search(album_artist + ' ' + album_title,
                            limit=1, offset=0, type='album', market=None)
    trackSearch = sp.search(track_artist + ' ' + track_title,
                            limit=1, offset=0, type='track', market=None)

    # check if search returned any results
    if not albumSearch['albums']['items']:
        album_url = []
    else:
        album_url = albumSearch['albums']['items'][0]['external_urls']['spotify']
    if not trackSearch['tracks']['items']:
        track_url = []
    else:
        track_url = trackSearch['tracks']['items'][0]['external_urls']['spotify']

    return [album_url, track_url]


# combines results of web scrape and search for URLs into one string
def buildMessage(album_title, album_artist, album_url, track_title, track_artist, track_url):
    message = 'Best New Album: ' + album_title + ' by ' + album_artist + '\n' + \
              'Spotify URL: ' + (album_url if album_url else 'No results') + '\n\n' +\
              'Best New Track: ' + track_title + ' by ' + track_artist + '\n' + \
              'Spotify URL: ' + (track_url if track_url else 'No results')

    return message


# send SMS with 'best new' info
def sendSMS(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    client.messages.create(
        to='+' + str(RECIPIENT_PHONE_NUMBER),
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )


if __name__ == "__main__":
    main()
