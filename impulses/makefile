all: orion331-T-44100.wav orion331-T-44100.raw orion331-M-44100.wav orion331-M-44100.raw orion331-W-44100.wav orion331-W-44100.raw

%-48000.raw : %.pir
	dd bs=80 skip=1 if=$< of=$@

%-44100.raw : %-48000.raw
	sox -c 1 -r 48000 -t .f32 $< -r 44100 $@

%-44100.wav : %-44100.raw
	sox -c 1 -r 44100 -t .f32 $< -t wav $@ 

%-48000.wav : %-48000.raw
	sox -c 1 -r 48000 -t .f32 $< -t wav $@ 