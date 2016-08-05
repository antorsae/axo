#!/usr/bin/env python
from subprocess import call
import gobject
from mpdor.client import Client
try:
    from termcolor import colored
except:
    colored = False

class TestClient(Client):
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
    		call("./denon.sh cmd PWON", shell=True)
    	elif state == "stop":
    		call("./denon.sh cmd PWSTANDBY", shell=True)

    def on_player_stopped(self, client): print "stopped"
    def on_player_paused(self, client): print "paused"
    def on_player_unpaused(self, client): print "unpaused"
    def on_mixer_change(self, client, vol): print "volume:", vol
    def on_player_seeked(self, client, pos): print "seeked:", pos
    def on_options_change(self, client, options): print options

if __name__ == "__main__":
    t = TestClient()
    gobject.MainLoop().run()