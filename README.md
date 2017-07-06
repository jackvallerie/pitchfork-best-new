# **Pitchfork Scrape**

Jack Vallerie

pitch_scrape.py is part of an idea I had to have alerts sent to my phone
when Pitchfork.com updated the 'Best New Album' or 'Best New Track' categories
on their website. The script uses 'requests' to get the 'Best New Music' page
of the website and 'lxml' to scrape the text from the HTML denoting what their
best new music selections are (specifically the name of the track/album and the
name of the artist).

It then uses the Spotify Web API (via spotipy) to search for the track or album, and finally
uses the Twilio API to send a text message to a specified phone number with the
best new music info and the Spotify URLs to the track/album if it could find it.


The script usage is

```
python pitch_scrape.py [spotifyUsername] [phoneNumber]
```
where a phone number includes the country and area codes and has no extra
characters or spaces. After running this a webpage will automatically open up
and you will be prompted to paste the URL of that page into the terminal.


This script does, however, require that a server be set up beforehand for the
Spotify Redirect URI.  I currently have the app redirecting to http://localhost:8000/
as seen on line 44, which is the sever that is automatically set up when you run

```
python -m SimpleHTTPServer
```