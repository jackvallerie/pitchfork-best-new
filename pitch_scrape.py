"""
pitch_scrape.py
Jack Vallerie

Retrieves the most recent posting of 'Best New Track' and 'Best New Album'
from Pitchfork Music's website and sends a text message to a specified
number with the track/album info and links to the track/album on Spotify

"""

import os, sys, regex, spotipy, requests
from lxml import html
import spotipy.util as util
from twilio.rest import Client


#################
### CONSTANTS

spotify_client_id = os.environ['SPOTIFY_CLIENT_ID']
spotify_client_secret = os.environ['SPOTIFY_CLIENT_SECRET']
twilio_account_sid = os.environ['TWILIO_ACCOUNT_SID']
twilio_auth_token = os.environ['TWILIO_AUTH_TOKEN']
twilio_phone_number = os.environ['TWILIO_PHONE_NUMBER']

#################


def main():

    # read in username and phone number from command line or print usage message
    if len(sys.argv) > 2:
        username = sys.argv[1]
        phoneNumber = sys.argv[2]
    else:
        print "Usage: %s username phoneNumber" % (sys.argv[0],)
        sys.exit()


    # authenticate Spotify API keys
    token = util.prompt_for_user_token(username, scope='user-library-read',
                                       client_id=spotify_client_id,
                                       client_secret=spotify_client_secret,
                                       redirect_uri='http://localhost:8000/')
    sp    = spotipy.Spotify(auth=token)


    # get info from HTML and clean it
    [bestNewAlbumArtist, bestNewAlbumTitle,
     bestNewTrackArtist, bestNewTrackTitle] = scrapeInfo()
    [albumTitle, trackTitle] = cleanStrings(bestNewAlbumTitle[0], bestNewTrackTitle[0])
    albumArtist = bestNewAlbumArtist[0]
    trackArtist = bestNewTrackArtist[0]


    # Find Spotify links, build SMS, send message
    [albumURL, trackURL] = getURLs(albumArtist, albumTitle, trackArtist, trackTitle, sp)
    message = buildMessage(albumTitle, albumArtist, albumURL, trackTitle, trackArtist, trackURL)
    sendSMS(message, phoneNumber)
    print message





########################################
###  HELPER FUNCTIONS
########################################

# scrapes necessary info from Pitchfork 'Best New' webpage
def scrapeInfo():
    page = requests.get('http://pitchfork.com/best/')
    tree = html.fromstring(page.content)
    
    # retrieve text from HTML
    bestNewAlbumArtist = tree.xpath('//*[@id="best-new-overview"]/div/div/div[1]' + \
                                    '/div/a/div[2]/h3[1]/ul/li/text()')
    bestNewAlbumTitle  = tree.xpath('//*[@id="best-new-overview"]/div/div/div[1]' + \
                                    '/div/a/div[2]/h3[2]/text()')
    bestNewTrackArtist = tree.xpath('//*[@id="best-new-overview"]/div/div/div[2]' + \
                                    '/div/a/div[2]/h3[1]/ul/li/text()')
    bestNewTrackTitle  = tree.xpath('//*[@id="best-new-overview"]/div/div/div[2]' + \
                                    '/div/a/div[2]/h3[2]/text()')

    return [bestNewAlbumArtist, bestNewAlbumTitle, bestNewTrackArtist, bestNewTrackTitle]


# strip strings of newline chars and remove unicode on track title
def cleanStrings(albumTitle, trackTitle):
    albumTitle = albumTitle.rstrip()
    trackTitle = trackTitle.rstrip()
    trackTitle = regex.sub('\xe2\x80\x9c','', trackTitle)
    trackTitle = regex.sub('\xe2\x80\x9d','', trackTitle)
    return [albumTitle, trackTitle]


# get Spotify URLs for best new track and best new album 
def getURLs(albumArtist, albumTitle, trackArtist, trackTitle, sp):
    # run searches
    albumSearch = sp.search(albumArtist + ' ' + albumTitle,
                            limit=1, offset=0, type='album', market=None)
    trackSearch = sp.search(trackArtist + ' ' + trackTitle,
                            limit=1, offset=0, type='track', market=None)

    # check if search returned any results
    if not albumSearch['albums']['items']:
        albumURL = []
    else:
        albumURL = albumSearch['albums']['items'][0]['external_urls']['spotify']
    if not trackSearch['tracks']['items']:
        trackURL = []
    else:
        trackURL = trackSearch['tracks']['items'][0]['external_urls']['spotify']

    return [albumURL, trackURL]


# combines results of web scrape and search for URLs into one string
def buildMessage(albumTitle, albumArtist, albumURL, trackTitle, trackArtist, trackURL):
    message = 'Best New Album: ' + albumTitle + ' by ' + albumArtist + '\n' + \
              'Spotify URL: ' + (albumURL if albumURL else 'No results') + '\n\n' +\
              'Best New Track: ' + trackTitle + ' by ' + trackArtist + '\n' + \
              'Spotify URL: ' + (trackURL if trackURL else 'No results')

    return message


# send SMS with 'best new' info
def sendSMS(message, phoneNumber):
    client = Client(twilio_account_sid, twilio_auth_token)

    client.messages.create(
        to='+' + str(phoneNumber),
        from_=twilio_phone_number,
        body=message
    )


if __name__ == "__main__":
    main()
