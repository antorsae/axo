sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install ecasound sox mpd cmake ladspa-sdk cmt mpc
sudo usermod -a -G video mpd

# install Rtaylor plugins
curl http://faculty.tru.ca/rtaylor/rt-plugins/rt-plugins-0.0.5.tar.gz | tar xf
cd rt-plugins-0.0.5
echo 'set(CMAKE_INSTALL_PREFIX "/usr")' >> CMakeLists.txt
cd build
cmake ..
make
sudo make install

# remove sine.so causing known issue *** Error in `ecasound': double free or corruption (!prev):
sudo rm /usr/lib/ladspa/sine.so

# hdmiplay dependencies
cd /opt/vc/src/hello_pi/
./rebuild

# hdmiplay
cd
git clone https://github.com/antorsae/hdmiplay
cd hdmiplay
make

# mpd with sacd support etc
git clone git://git.musicpd.org/manisiutkin/mpd.git
cd mpd/
./autogen.sh
sudo apt-get -y install libmad0-dev libmpg123-dev libid3tag0-dev \
  libflac-dev libvorbis-dev libopus-dev \
  libadplug-dev libaudiofile-dev libsndfile1-dev libfaad-dev \
  libfluidsynth-dev libgme-dev libmikmod2-dev libmodplug-dev \
  libmpcdec-dev libwavpack-dev libwildmidi-dev \
  libsidplay2-dev libsidutils-dev libresid-builder-dev \
  libavcodec-dev libavformat-dev \
  libmp3lame-dev \
  libsamplerate0-dev libsoxr-dev \
  libbz2-dev libcdio-paranoia-dev libiso9660-dev libmms-dev \
  libzzip-dev \
  libcurl4-gnutls-dev libyajl-dev libexpat-dev \
  libasound2-dev libao-dev libjack-jackd2-dev libopenal-dev \
  libpulse-dev libroar-dev libshout3-dev \
  libmpdclient-dev \
  libnfs-dev libsmbclient-dev \
  libupnp-dev \
  libavahi-client-dev \
  libsqlite3-dev \
  libsystemd-daemon-dev libwrap0-dev \
  libboost-dev \
  libicu-dev libssl-dev
./configure --enable-pipe-output --enable-sacdiso --enable-dvdaiso --enable-iso9660 --prefix=
make -j



# add output to mpd
sudo cat >> /etc/mpd.conf <<DELIM
audio_output {
        type            "pipe"
        name            "Orion 44k 24bit via HDMI"
        command         "/home/pi/axo/ecaplay.sh | /home/pi/hdmiplay/hdmiplay.bin 44100 24 01324567 2>/dev/null"
	format          "44100:32:2"
}
DELIM

# force 8 channel audio out on HDMI
sudo cat >> /boot/config.txt <<DELIM
hdmi_drive=2
hdmi_force_hotplug=1
hdmi_channel_map=0x13fac688
hdmi_force_edid_audio=1
DELIM
