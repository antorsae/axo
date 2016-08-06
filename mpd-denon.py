#!/usr/bin/env python
import serial
from subprocess import call
import gobject
from mpdor.client import Client
try:
    from termcolor import colored
except:
    colored = False

class MPDClient(Client):

    denon = serial.Serial('/dev/ttyUSB0')

    def on_player_song_start(self, client, songdata):
        if "artist" in songdata.__dict__:
            if colored:
                print colored(songdata.title, "white", attrs=("bold",)) + \
                        " by " + colored(songdata.artist, "yellow", attrs=("bold",))
            else:
                print songdata.title + " by " + songdata.artist
        else:
            if colored:
                print colored(songdata.title, "white", attrs=("bold",))
            else:
                print songdata.title

    def on_idle_change(self, client, event): print "mpd event: @" + event
    def on_player_change(self, client, state): 
    	print "changed", state
    	if state == "play":
            MPDClient.denon.write(b'PWON\r')
    	elif state == "stop":
            MPDClient.denon.write(b'PWSTANDBY\r')

    def on_player_stopped(self, client): print "stopped"
    def on_player_paused(self, client): print "paused"
    def on_player_unpaused(self, client): print "unpaused"
    def on_mixer_change(self, client, vol): print "volume:", vol
    def on_player_seeked(self, client, pos): print "seeked:", pos
    def on_options_change(self, client, options): print options

if __name__ == "__main__":
    t = MPDClient()
    gobject.MainLoop().run()
