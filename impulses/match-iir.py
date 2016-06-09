import shlex
import subprocess
import os
import signal

import matplotlib
matplotlib.use('Agg')
from lmfit import Parameters, minimize, fit_report
import numpy, pylab

def zoi(fmin, fmax, x_freq, y):
    fmin_idx = (numpy.abs(x_freq-fmin)).argmin()
    fmax_idx = (numpy.abs(x_freq-fmax)).argmin()
    return y[fmin_idx:fmax_idx]

def plotFilter(filename, name, fmin, fmax, x_freq, reference, matched, keep=None, diffPhase=None):
    if keep is None:
        pylab.clf()
    pylab.title(name)
    pylab.subplot(2, 1, 1)
    pylab.semilogx(x_freq, mag(reference))
    pylab.semilogx(x_freq, mag(matched))
    pylab.xlim(xmin=fmin,xmax=fmax)
    pylab.ylim(ymin=max(-60,min(mag(numpy.concatenate([zoi(fmin,fmax,x_freq,reference),zoi(fmin,fmax,x_freq,matched)])))),ymax=max(mag(numpy.concatenate([reference,matched])))+2)
    pylab.ylabel("Magnitude response (db)")
    pylab.xlabel("Freq")
    pylab.subplot(2, 1, 2)
    pylab.semilogx(x_freq, phase(reference))
    pylab.semilogx(x_freq, phase(matched))
    if diffPhase is not None:
        pylab.semilogx(x_freq, numpy.abs(numpy.fmod(phase(reference)-phase(matched), numpy.pi)))
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

sample_rate = 48000

# Pre1 -------------------------------------------------------------------------
pre1_time = numpy.memmap("orion331-TP2B-48000.raw", dtype="float32", mode='r')
pre1_freq = numpy.fft.rfft(pre1_time)
pre1_reference = pre1_freq

samples = pre1_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

pre1_filters = '-eadb:-{adb} -el:RThighshelf,{RThighshelf_A},{RThighshelf_f0},{RThighshelf_Q} -el:RTlowshelf,{RTlowshelf_A},{RTlowshelf_f0},{RTlowshelf_Q}'
fmin = 20
fmax = 22000

pre1 = Parameters()

#               (Name,              Value,      Vary,   Min,    Max,    Expr)
pre1.add_many(  ('adb',             9.28136887,     True,   0,      None,   None),
                ('RThighshelf_A',   4.38211718,     True,   0,      None,   None),
                ('RThighshelf_f0',  134.645409,     True,   100,    200,    None),
                ('RThighshelf_Q',   0.48178881,     True,   0.1,    3,      None),
                ('RTlowshelf_A',    3.42318251,     True,   0,      None,   None),
                ('RTlowshelf_f0',   1747.22195,     True,   1600,   1800,   None),
                ('RTlowshelf_Q',    0.48331721,     True,   0.1,    3,      None),
                ('sample_rate',     sample_rate,    False,  None,   None,   None))



#out = minimize(residual, pre1, args=(pre1_filters, x_freq, fmin, fmax, delta_time), kws={'data':pre1_reference}, method='nelder')
#pre1 = out.params
#print(fit_report(out))

pre1_matched = residual(pre1, pre1_filters, x_freq, fmin, fmax, delta_time)

plotFilter("pre1.png", "Pre 1", fmin, fmax, x_freq, pre1_reference, pre1_matched)


# Woofer -----------------------------------------------------------------------

woofer_time = numpy.memmap("orion331-W-48000.raw", dtype="float32", mode='r')
woofer_freq = numpy.fft.rfft(woofer_time)
woofer_reference = woofer_freq

samples = woofer_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

woofer_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4lowpass,92 -eadb:-{adb} -el:RTlowshelf,{RTlowshelfX_A},{RTlowshelfX_f0},{RTlowshelfX_Q} -el:RTlowshelf,{RTlowshelfY_A},{RTlowshelfY_f0},{RTlowshelfY_Q}'
fmin = 20
fmax = 150

woofer = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
woofer.add_many(    ('adb',             6.61097690,     True,   0,      None,   None),
                    ('RTlowshelfX_A',   19.1030081,     True,   0,      None,   None),
                    ('RTlowshelfX_f0',  43.7227200,     True,   20,     100,    None),
                    ('RTlowshelfX_Q',   0.43044260,     True,   0.1,    3,      None),
                    ('RTlowshelfY_A',   19.1020033,     True,   0,      None,   None),
                    ('RTlowshelfY_f0',  74.0782641,     True,   50,     125,    None),
                    ('RTlowshelfY_Q',   0.43461278,     True,   0.1,    3,      None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, woofer, args=(woofer_filters, x_freq, fmin, fmax, delta_time), kws={'data':woofer_reference}, method='nelder')
#woofer = out.params
#print(fit_report(out))

woofer_matched = residual(woofer, woofer_filters, x_freq, fmin, fmax, delta_time)

plotFilter("woofer.png", "Woofer", fmin, fmax, x_freq, woofer_reference, woofer_matched)

# Mid --------------------------------------------------------------------------

mid_time = numpy.memmap("orion331-M-48000.raw", dtype="float32", mode='r')
mid_freq = numpy.fft.rfft(mid_time)
mid_reference = mid_freq

samples = mid_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

mid_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:delay_0.01s,{delay},1 -el:RTlr4lowpass,{RTlr4lowpass_f0} -eadb:{adb} -el:RTlowshelf,{RTlowshelf_A},{RTlowshelf_f0},{RTlowshelf_Q} -el:RTparaeq,-{RTparaeqX_A},{RTparaeqX_f0},{RTparaeqX_Q} -el:RTparaeq,-{RTparaeqY_A},{RTparaeqY_f0},{RTparaeqY_Q}'

fmin = 30
fmax = 3000

mid = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
mid.add_many(       ('delay',           0,              False,  0,      None,   None),
                    ('adb',             7.91612286,     True,   0,      None,   None),
                    ('RTlr4lowpass_f0', 1470,           False,  None,   None,   None),
                    ('RTlowshelf_A',    14.0043440,     True,   0,      None,   None),
                    ('RTlowshelf_f0',   71.83314,       False,  50,     200,    None), #63.3838956
                    ('RTlowshelf_Q',    0.58862461,     True,   0.1,    3,      None),
                    ('RTparaeqX_A',     68.6467580,     True,   0,      None,   None),
                    ('RTparaeqX_f0',    4751,           False,  4000,   5000,   None),
                    ('RTparaeqX_Q',     0.17970975,     True,   0,      5,      None),
                    ('RTparaeqY_A',     10.5709973,     True,   0,      None,   None),
                    ('RTparaeqY_f0',    462.200124,     True,   300,    600,    None), #482.118853
                    ('RTparaeqY_Q',     0.53195141,     True,   0.1,    None,    None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, mid, args=(mid_filters, x_freq, fmin, fmax, delta_time), kws={'data':mid_reference}, method='nelder')
#mid = out.params
#print(fit_report(out))

mid_matched = residual(mid, mid_filters, x_freq, fmin, fmax, delta_time)

plotFilter("mid.png", "Midrange", fmin, fmax, x_freq, mid_reference, mid_matched)


# Tweeter ----------------------------------------------------------------------

tweeter_time = numpy.memmap("orion331-T-48000.raw", dtype="float32", mode='r')
tweeter_freq = numpy.fft.rfft(tweeter_time)
tweeter_reference = tweeter_freq

samples = tweeter_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

tweeter_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:RTlr4hipass,{RTlr4hipass_f0} -el:delay_0.01s,{delay},1 -eadb:{adb} '
fmin = 1000
fmax = 12000

tweeter = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
tweeter.add_many(   ('delay',           0,              False,  0,      None,   None),
                    ('adb',             0.29553190,     True,   0,      None,   None),
                    ('RTlr4hipass_f0',  1470,           False,  None,   None,   None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

#out = minimize(residual, tweeter, args=(tweeter_filters, x_freq, fmin, fmax, delta_time), kws={'data':tweeter_reference}, method='nelder')
#tweeter = out.params
#print(fit_report(out))

tweeter_matched = residual(tweeter, tweeter_filters, x_freq, fmin, fmax, delta_time)

plotFilter("tweeter.png", "Tweeter", fmin, fmax, x_freq, tweeter_reference, tweeter_matched)


# Mid + Tweeter ----------------------------------------------------------------


fmin = 500
fmax = 4000
pylab.clf()

mid['delay'].value =0
tweeter_delay_at_seat = ( (numpy.sqrt(3.0**2+0.1905**2)-3) / 343)

delays ={}
best_fit = -1.0e100
best_delay = 0
for delay in numpy.linspace(0, 1/(8*1470.0),1):
    tweeter['delay'].value = delay + tweeter_delay_at_seat # 0.0009576 # i * 0.00005
    mid_tweeter_xo_filters = '-a:mid,tweeter -i:stdin ' + '-a tweeter ' + tweeter_filters.format(**tweeter.valuesdict()) + ' -a mid ' + mid_filters.format(**mid.valuesdict()) + ' -a:tweeter,mid '
    mid_tweeter_xo_matched = residual(tweeter, mid_tweeter_xo_filters, x_freq, fmin, fmax, delta_time)
    plotFilter("", "XO M-T", fmin, fmax, x_freq, mid_tweeter_xo_matched, mid_tweeter_xo_matched, True)
    this_fit = sum(zoi(800, 1200, x_freq, mag(mid_tweeter_xo_matched)))
    print this_fit
    print "vs"
    print best_fit
    if (this_fit > best_fit):
        best_fit = this_fit
        best_delay = delay
        print "BEST: " + str(best_delay)

plotFilter("", "", fmin, fmax, x_freq, mid_matched, tweeter_matched, True)
pylab.savefig("mid_tweeter_xo.png")
plotFilter("mid_vs_tweeter", "M-T XO", fmin, fmax, x_freq, mid_matched, tweeter_matched, None, True)
print best_delay

best_delay = 0
tweeter['delay'].value = 0 #best_delay  + tweeter_delay_at_seat # 0.0009576 # i * 0.00005
mid_tweeter_xo_filters = '-a:mid,tweeter -i:stdin ' + '-a tweeter ' + tweeter_filters.format(**tweeter.valuesdict()) + ' -a mid ' + mid_filters.format(**mid.valuesdict()) + ' -a:tweeter,mid '
mid_tweeter_xo_matched = residual(tweeter, mid_tweeter_xo_filters, x_freq, fmin, fmax, delta_time)
plotFilter("best_mid_tweeter_xo.png", "XO M-T", fmin, fmax, x_freq, mid_tweeter_xo_matched, tweeter_matched)
  

# Woofer + Mid -----------------------------------------------------------------


fmin = 10
fmax = 300
pylab.clf()
delays =[]

mid_delay_at_seat = ( (numpy.sqrt(3.0**2+0.5**2)-3) / 343)
for delay in numpy.linspace(0, 1/92.,1):
    mid['delay'].value = delay + mid_delay_at_seat # 0.0009576 # i * 0.00005
    woofer_mid_xo_filters = '-a:mid,woofer -i:stdin ' + '-a woofer ' + woofer_filters.format(**woofer.valuesdict()) + ' -a mid ' + mid_filters.format(**mid.valuesdict()) + ' -a:woofer,mid '
    woofer_mid_xo_matched = residual(mid, woofer_mid_xo_filters, x_freq, fmin, fmax, delta_time)
    plotFilter("", "XO W-M", fmin, fmax, x_freq, woofer_mid_xo_matched, woofer_mid_xo_matched, True)
    this_fit = sum(zoi(800, 1200, x_freq, mag(mid_tweeter_xo_matched)))
    if (this_fit > best_fit):
        best_fit = this_fit
        best_delay = delay
        print "BEST: " + str(best_delay)
   
plotFilter("", "", fmin, fmax, x_freq, mid_matched, woofer_matched, True)
pylab.savefig("woofer_mid_xo.png")
print delays # 7.24637681159e-05

best_delay = 0
# All system  ------------------------------------------------------------------



fmin = 10
fmax = 22000
pylab.clf()
best_delay = 0
best_fit = -1.0e100

for delay in numpy.linspace(1.76366843e-04, 2.09960527e-04,10):
    mid['delay'].value = 7.24637681159e-05 + mid_delay_at_seat # best_delay  + mid_delay_at_seat # 0.0009576 # i * 0.00005
    tweeter['delay'].value = delay + mid['delay'].value - mid_delay_at_seat + tweeter_delay_at_seat
    all_filters = '-a:woofer,mid,tweeter -i:stdin ' + '-a woofer ' + woofer_filters.format(**woofer.valuesdict()) + ' -a mid ' + mid_filters.format(**mid.valuesdict()) + ' -a tweeter ' + tweeter_filters.format(**tweeter.valuesdict()) + ' -a:woofer,mid,tweeter '
    all_matched = residual(mid, all_filters, x_freq, fmin, fmax, delta_time)
    plotFilter("", "Orion", fmin, fmax, x_freq, all_matched, all_matched, True)
    this_fit = sum(zoi(600, 3000, x_freq, mag(all_matched)))
    if (this_fit > best_fit):
            best_fit = this_fit
            best_delay = delay

pylab.savefig("orion.png")
print "BEST DELAY: " + str(best_delay) # 0.000183832106111









