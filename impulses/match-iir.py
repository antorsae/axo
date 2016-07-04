import shlex
import subprocess
import os
import signal

import matplotlib
matplotlib.use('Agg')
from lmfit import Parameters, minimize, fit_report
import numpy, pylab
import scipy.io.wavfile

def zoi(fmin, fmax, x_freq, y):
    fmin_idx = (numpy.abs(x_freq-fmin)).argmin()
    fmax_idx = (numpy.abs(x_freq-fmax)).argmin()
    return y[fmin_idx:fmax_idx]

def plotFilter(filename, name, fmin, fmax, x_freq, reference, matched, keep=None, diffPhase = None):
    if keep is None:
        pylab.clf()
    pylab.title(name)
    pylab.subplot(2, 1, 1)
    pylab.semilogx(x_freq, mag(reference))
    pylab.semilogx(x_freq, mag(matched))
    pylab.xlim(xmin=fmin,xmax=fmax)
    pylab.ylim(ymin=max(-90,min(mag(numpy.concatenate([zoi(fmin,fmax,x_freq,reference),zoi(fmin,fmax,x_freq,matched)])))),ymax=max(mag(numpy.concatenate([reference,matched])))+2)
    pylab.ylabel("Magnitude response (db)")
    pylab.xlabel("Freq")
    pylab.subplot(2, 1, 2)
    pylab.semilogx(x_freq, phase(reference))
    pylab.semilogx(x_freq, phase(matched))
#    if diffPhase is not None:
#        pylab.semilogx(x_freq, numpy.abs(numpy.fmod(phase(diffPhase)-phase(matched), numpy.pi)))
#	pylab.semilogx(x_freq, phase(matched))
    pylab.xlim(xmin=fmin,xmax=fmax)
    pylab.ylim(ymin=-4,ymax=4)
    pylab.ylabel("Phase")
    pylab.xlabel("Freq")
    if keep is None:
        pylab.savefig(filename)


def mag(c):
    return 20 * numpy.log10(numpy.abs(c))

def phase(c): 
    return numpy.angle(c)

def residual(params, filters, x_freq, fmin, fmax, delta_time, data=None):

    vals = params.valuesdict()

    if "-i:stdin" not in filters:
        filters = "-i:stdin " + filters
 
    command = ('ecasound -z:mixmode,sum -d:2 -f:f32,1,{sample_rate} '+filters+' -f:f32 -o:stdout').format(**vals)

    print command

    proc = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE, shell=False, preexec_fn=os.setsid )
    response = proc.communicate(delta_time[:].astype(numpy.float32).tostring())
    try:
        os.killpg(os.getpgid(proc.pid), signal.SIGTERM)
        print "Killed"
    except OSError:
        pass

    response_time = numpy.frombuffer(response[0], dtype = numpy.float32)
    response_freq = numpy.fft.rfft(response_time)

    if data is None:
        return response_freq

    fmin_idx = (numpy.abs(x_freq-fmin)).argmin()
    fmax_idx = (numpy.abs(x_freq-fmax)).argmin()

    residual = mag(response_freq) - mag(data)
    residual[:fmin_idx] = 0.0
    residual[fmax_idx:] = 0.0

    return residual

def readwav(filename, scale=1.0):
    sample_rate, data = scipy.io.wavfile.read(filename)
    if data.dtype == 'int16':
	return sample_rate, scale * numpy.float64(data)/(2**15-1)
    else:
        return sample_rate, data

#sample_rate = 48000

# Pre1 -------------------------------------------------------------------------
#pre1_time2 = numpy.memmap("orion331-TP2B-48000.raw", dtype="float32", mode='r')
sample_rate, pre1_time = readwav('orion-tinasp-331-TP2B.wav')

pre1_freq = numpy.fft.rfft(pre1_time)
pre1_reference = pre1_freq

samples = pre1_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
delta_freq = numpy.fft.rfft(delta_time)
x_freq = numpy.linspace(0.0, sample_rate/2, pre1_freq.size)

pre1_filters = '-eadb:-{adb} -el:RThighshelf,{RThighshelf_A},{RThighshelf_f0},{RThighshelf_Q} -el:RTlowshelf,{RTlowshelf_A},{RTlowshelf_f0},{RTlowshelf_Q}'
fmin = 0
fmax = sample_rate

pre1 = Parameters()

#               (Name,              Value,      Vary,   Min,    Max,    Expr)
pre1.add_many(  ('adb',             8.89013052458,  True,   0,      None,   None),
                ('RThighshelf_A',   6,              False,  0,      None,   None),
                ('RThighshelf_f0',  125.336561422,  True,   100,    200,    None),
                ('RThighshelf_Q',   0.5,            False,  0.1,    3,      None),
                ('RTlowshelf_A',    3,              False,  0,      None,   None),
                ('RTlowshelf_f0',   1702.12940923,  True,   1600,   1800,   None),
                ('RTlowshelf_Q',    0.5,            False,  0.1,    3,      None),
                ('sample_rate',     sample_rate,    False,  None,   None,   None))



#out = minimize(residual, pre1, args=(pre1_filters, x_freq, fmin, fmax, delta_time), kws={'data':pre1_reference}, method='nelder')
#pre1 = out.params
#print(fit_report(out))

pre1_matched = residual(pre1, pre1_filters, x_freq, fmin, fmax, delta_time)

plotFilter("pre1.png", "Pre 1", fmin, fmax, x_freq, pre1_reference, pre1_matched, None, delta_freq)

# Woofer -----------------------------------------------------------------------

sample_rate, woofer_time = readwav('orion-tinasp-331-W.wav')
#woofer_time = numpy.memmap("orion331-W-48000.raw", dtype="float32", mode='r')
woofer_freq = numpy.fft.rfft(woofer_time)
woofer_reference = woofer_freq

samples = woofer_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
delta_freq = numpy.fft.rfft(delta_time)
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

woofer_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4lowpass,92 -eadb:-{adb} -el:RTlowshelf,{RTlowshelfX_A},{RTlowshelfX_f0},{RTlowshelfX_Q} -el:RTlowshelf,{RTlowshelfY_A},{RTlowshelfY_f0},{RTlowshelfY_Q}'
fmin = 0
fmax = 2000

woofer = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
woofer.add_many(    ('adb',             6.28866913,     True,   0,      None,   None),
                    ('RTlowshelfX_A',   15.1,           False,  0,      None,   None),
                    ('RTlowshelfX_f0',  41.4581433,     True,   14.9,   110,    None),
                    ('RTlowshelfX_Q',   0.35125432,     True,   0.1,    3,      None),
                    ('RTlowshelfY_A',   23.3,           False,  0,      None,   None),
                    ('RTlowshelfY_f0',  59.8758887,     True,   19.5,   286,    None),
                    ('RTlowshelfY_Q',   0.48764436,     True,   0.1,    3,      None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, woofer, args=(woofer_filters, x_freq, fmin, fmax, delta_time), kws={'data':woofer_reference}, method='nelder')
#woofer = out.params
#print(fit_report(out))

woofer_matched = residual(woofer, woofer_filters, x_freq, fmin, fmax, delta_time)

plotFilter("woofer.png", "Woofer", fmin, fmax, x_freq, woofer_reference, woofer_matched, None, delta_freq)

# Mid --------------------------------------------------------------------------

sample_rate,mid_time = readwav('orion-tinasp-331-M.wav')
#mid_time = numpy.memmap("orion331-M-48000.raw", dtype="float32", mode='r')
mid_freq = numpy.fft.rfft(mid_time)
mid_reference = mid_freq

samples = mid_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
delta_freq = numpy.fft.rfft(delta_time)
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

mid_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:delay_0.01s,{delay},1 -el:RTlr4lowpass,{RTlr4lowpass_f0} -eadb:{adb} -el:RTlowshelf,{RTlowshelf_A},{RTlowshelf_f0},{RTlowshelf_Q} -el:RTparaeq,-{RTparaeqX_A},{RTparaeqX_f0},{RTparaeqX_Q} -el:RTparaeq,-{RTparaeqY_A},{RTparaeqY_f0},{RTparaeqY_Q}'

fmin = 0
fmax = sample_rate/2

mid = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
mid.add_many(       ('delay',           0,              False,  0,      None,   None),
                    ('adb',             4.1,            False,  0,      None,   None),
                    ('RTlr4lowpass_f0', 1440,           False,  None,   None,   None),
                    ('RTlowshelf_A',    22.2,           False,  0,      None,   None),
                    ('RTlowshelf_f0',   71.83314,       True,   20,     258,    None), #63.3838956
                    ('RTlowshelf_Q',    0.58862461,     True,   0.1,    3,      None),
                    ('RTparaeqX_A',     68.6467580,     True,   0,      None,   None),
                    ('RTparaeqX_f0',    4751,           False,  4000,   5000,   None),
                    ('RTparaeqX_Q',     0.17970975,     True,   0,      5,      None),
                    ('RTparaeqY_A',     10.5709973,     True,   0,      None,   None),
                    ('RTparaeqY_f0',    400,            False,  300,    600,    None), #482.118853
                    ('RTparaeqY_Q',     0.53195141,     True,   0.1,    3,      None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, mid, args=(mid_filters, x_freq, fmin, fmax, delta_time), kws={'data':mid_reference}, method='nelder')
#mid = out.params
#print(fit_report(out))

mid_matched = residual(mid, mid_filters, x_freq, fmin, fmax, delta_time)

plotFilter("mid.png", "Midrange", fmin, fmax, x_freq, mid_reference, mid_matched, None, delta_freq)


# Tweeter ----------------------------------------------------------------------

sample_rate, tweeter_time = readwav('orion-tinasp-331-T.wav')
#tweeter_time = numpy.memmap("orion331-T-48000.raw", dtype="float32", mode='r')
tweeter_freq = numpy.fft.rfft(tweeter_time)
tweeter_reference = tweeter_freq

samples = tweeter_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
delta_freq = numpy.fft.rfft(delta_time)
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

tweeter_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:RTlr4hipass,{RTlr4hipass_f0} -el:delay_0.01s,{delay},1 -eadb:{adb} '
fmin = 0
fmax = sample_rate/2

tweeter = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
tweeter.add_many(   ('delay',           0,              False,  0,      None,   None),
                    ('adb',             0.29553190,     True,   0,      None,   None),
                    ('RTlr4hipass_f0',  1440,           False,  None,   None,   None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, tweeter, args=(tweeter_filters, x_freq, fmin, fmax, delta_time), kws={'data':tweeter_reference}, method='nelder')
#tweeter = out.params
#print(fit_report(out))

tweeter_matched = residual(tweeter, tweeter_filters, x_freq, fmin, fmax, delta_time)

plotFilter("tweeter.png", "Tweeter", fmin, fmax, x_freq, tweeter_reference, tweeter_matched, None, delta_freq)








