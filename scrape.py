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

    # set these to nothing on first run
    latest_album_artist = latest_album_title = latest_track_artist = latest_track_title = ''

    # get info from HTML and clean it
    best_new_info = scrape_info()

    if best_new_info['album_artist'] + best_new_info['album_title'] == latest_album_artist + latest_album_title:
        new_album = False
    else:
        new_album = True
        best_new_info['album_url'] = get_spotify_url(best_new_info['album_artist'], best_new_info['album_title'], 'album', sp)
        latest_album_artist = best_new_info['album_artist']
        latest_album_title = best_new_info['album_title']
    if best_new_info['track_artist'] + best_new_info['track_title'] == latest_track_artist + latest_track_title:
        new_track = False
    else:
        new_track = True
        best_new_info['track_url'] = get_spotify_url(best_new_info['track_artist'], best_new_info['track_title'], 'track', sp)
        latest_track_artist = best_new_info['track_artist']
        latest_track_title = best_new_info['track_title']
    


    # Find Spotify links, build SMS, send message
    if new_album or new_track:
        message = build_message(best_new_info, new_album, new_track)
        send_sms(message)
        print(message)





########################################
###  HELPER FUNCTIONS
########################################

# scrapes necessary info from Pitchfork 'Best New' webpage
def scrape_info():
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

    [album_title, track_title] = clean_strings(album_title[0], track_title[0])

    best_new_info = {
        'album_artist': album_artist[0],
        'album_title': album_title,
        'track_artist': track_artist[0],
        'track_title': track_title
    }

    return best_new_info


# strip strings of newline chars and remove unicode on track title
def clean_strings(album_title, track_title):
    album_title = album_title.rstrip()
    track_title = track_title.rstrip()
    track_title = regex.sub('\xe2\x80\x9c','', track_title)
    track_title = regex.sub('\xe2\x80\x9d','', track_title)
    return [album_title, track_title]


# get Spotify URLs for best new track and best new album 
def get_spotify_url(artist, title, search_type, sp):
    # run searches
    search = sp.search(' '.join([artist, title]),
                            limit=1, offset=0, type=search_type, market=None)

    # check if search returned any results
    if search_type == 'album':
        if not search['albums']['items']:
            url = None
        else:
            url = search['albums']['items'][0]['external_urls']['spotify']
    elif search_type == 'track':
        if not search['tracks']['items']:
            url = None
        else:
            url = search['tracks']['items'][0]['external_urls']['spotify']

    return url


# combines results of web scrape and search for URLs into one string
def build_message(best_new_info, new_album, new_track):
    message = ''
    if new_album:
        message += "Best New Album: {} by {} \nSpotify URL: {}".format(
            best_new_info['album_title'], best_new_info['album_artist'],
            best_new_info.get('album_url', 'No results')
        )
        if new_track:
            message += '\n\n'
    if new_track:
        message += "Best New Track: {} by {} \nSpotify URL: {}".format(
            best_new_info['track_title'], best_new_info['track_artist'],
            best_new_info.get('track_url', 'No results')
        )

    return message


# send SMS with 'best new' info
def send_sms(message):
    client = Client(TWILIO_ACCOUNT_SID, TWILIO_AUTH_TOKEN)

    client.messages.create(
        to='+' + str(RECIPIENT_PHONE_NUMBER),
        from_=TWILIO_PHONE_NUMBER,
        body=message
    )


if __name__ == "__main__":
    main()
