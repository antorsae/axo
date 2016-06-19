sudo apt-get update
sudo apt-get -y upgrade
sudo apt-get -y install ecasound sox mpd cmake ladspa-sdk cmt mpc
sudo usermod -a -G video mpd

# install Rtaylor plugins
wget http://faculty.tru.ca/rtaylor/rt-plugins/rt-plugins-0.0.5.tar.gz
tar xf rt-plugins-0.0.5.tar.gz
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
