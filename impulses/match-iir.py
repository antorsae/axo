import shlex
import subprocess

import matplotlib
matplotlib.use('Agg')
from lmfit import Parameters, minimize, fit_report
import numpy, pylab

def residual(params, filters, x_freq, fmin, fmax, delta_time, data=None):

    vals = params.valuesdict()

    command = ('ecasound -d:2 -f:f32,1,{sample_rate} -i:stdin '+filters+' -f:f32 -o:stdout').format(**vals)

    print command

    proc = subprocess.Popen(shlex.split(command), stdout=subprocess.PIPE, stdin=subprocess.PIPE, stderr=subprocess.PIPE)
    response = proc.communicate(delta_time[:].astype(numpy.float32).tostring())

    response_time = numpy.frombuffer(response[0], dtype = numpy.float32)
    response_freq = numpy.fft.rfft(response_time)

    model = 20 * numpy.log10(numpy.abs(response_freq))
    if data is None:
        return model

    fmin_idx = (numpy.abs(x_freq-fmin)).argmin()
    fmax_idx = (numpy.abs(x_freq-fmax)).argmin()

    residual = model - data
    residual[:fmin_idx] = 0.0
    residual[fmax_idx:] = 0.0

    return residual

sample_rate = 48000

# Pre1 -------------------------------------------------------------------------
impulse_time = numpy.memmap("orion331-TP2B-48000.raw", dtype="float32", mode='r')
impulse_freq = numpy.fft.rfft(impulse_time)
pre1_reference = 20 * numpy.log10(numpy.abs(impulse_freq))

samples = impulse_time.size

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



out = minimize(residual, pre1, args=(pre1_filters, x_freq, fmin, fmax, delta_time), kws={'data':pre1_reference}, method='nelder')
pre1 = out.params
print(fit_report(out))

pre1_matched = residual(pre1, pre1_filters, x_freq, fmin, fmax, delta_time)

pylab.semilogx(x_freq, pre1_reference)
pylab.semilogx(x_freq, pre1_matched)
pylab.savefig("pre1.png")

# Woofer -----------------------------------------------------------------------

impulse_time = numpy.memmap("orion331-W-48000.raw", dtype="float32", mode='r')
impulse_freq = numpy.fft.rfft(impulse_time)
woofer_reference = 20 * numpy.log10(numpy.abs(impulse_freq))

samples = impulse_time.size

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

out = minimize(residual, woofer, args=(woofer_filters, x_freq, fmin, fmax, delta_time), kws={'data':woofer_reference}, method='nelder')
woofer = out.params
print(fit_report(out))

woofer_matched = residual(woofer, woofer_filters, x_freq, fmin, fmax, delta_time)

pylab.semilogx(x_freq, woofer_reference)
pylab.semilogx(x_freq, woofer_matched)
pylab.savefig("woofer.png")

# Mid --------------------------------------------------------------------------

impulse_time = numpy.memmap("orion331-M-48000.raw", dtype="float32", mode='r')
impulse_freq = numpy.fft.rfft(impulse_time)
mid_reference = 20 * numpy.log10(numpy.abs(impulse_freq))

samples = impulse_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

mid_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:RTlr4lowpass,{RTlr4lowpass_f0} -eadb:{adb} -el:RTlowshelf,{RTlowshelf_A},{RTlowshelf_f0},{RTlowshelf_Q} -el:RTparaeq,-{RTparaeqX_A},{RTparaeqX_f0},{RTparaeqX_Q} -el:RTparaeq,-{RTparaeqY_A},{RTparaeqY_f0},{RTparaeqY_Q}'
fmin = 50
fmax = 1440

mid = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
mid.add_many(       ('adb',             3.73497436,     True,   0,      None,   None),
                    ('RTlr4lowpass_f0', 1440,           False,  None,   None,   None),
                    ('RTlowshelf_A',    16.2310419,     True,   0,      None,   None),
                    ('RTlowshelf_f0',   105.438700,     True,   50,     200,    None),
                    ('RTlowshelf_Q',    0.52339213,     True,   0.1,    3,      None),
                    ('RTparaeqX_A',     20,             False,  0,      None,   None),
                    ('RTparaeqX_f0',    4619,           False,  4000,   5000,   None),
                    ('RTparaeqX_Q',     0.5,            False,  0.1,    3,      None),
                    ('RTparaeqY_A',     7.73395202,     True,   0,      None,   None),
                    ('RTparaeqY_f0',    472.698768,     True,   300,    600,    None),
                    ('RTparaeqY_Q',     0.71477801,     True,   0.1,    3,      None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

out = minimize(residual, mid, args=(mid_filters, x_freq, fmin, fmax, delta_time), kws={'data':mid_reference}, method='nelder')
mid = out.params
print(fit_report(out))

mid_matched = residual(mid, mid_filters, x_freq, fmin, fmax, delta_time)

pylab.semilogx(x_freq, mid_reference)
pylab.semilogx(x_freq, mid_matched)
pylab.ylim(ymin=-30,ymax=20)
pylab.savefig("mid.png")

# Tweeter ----------------------------------------------------------------------

impulse_time = numpy.memmap("orion331-T-48000.raw", dtype="float32", mode='r')
impulse_freq = numpy.fft.rfft(impulse_time)
tweeter_reference = 20 * numpy.log10(numpy.abs(impulse_freq))

samples = impulse_time.size

delta_time   = numpy.zeros(samples)
delta_time [0] = 1.0
x_freq = numpy.linspace(0.0, sample_rate/2, (samples/2)+1)

tweeter_filters = pre1_filters.format(**pre1.valuesdict()) + ' -el:RTlr4hipass,92 -el:RTlr4hipass,{RTlr4hipass_f0} -eadb:{adb}'
fmin = 1440
fmax = 12000

tweeter = Parameters()

#               (Name,                  Value,          Vary,   Min,    Max,    Expr)
tweeter.add_many(   ('adb',             0.26889713,     True,   0,      None,   None),
                    ('RTlr4hipass_f0',  1440,           False,  None,   None,   None),
                    ('sample_rate',     sample_rate,    False,  None,   None,   None))

out = minimize(residual, tweeter, args=(tweeter_filters, x_freq, fmin, fmax, delta_time), kws={'data':tweeter_reference}, method='nelder')
tweeter = out.params
print(fit_report(out))

tweeter_matched = residual(tweeter, tweeter_filters, x_freq, fmin, fmax, delta_time)

pylab.semilogx(x_freq, tweeter_reference)
pylab.semilogx(x_freq, tweeter_matched)
pylab.ylim(ymin=-30,ymax=10)
pylab.savefig("tweeter.png")

