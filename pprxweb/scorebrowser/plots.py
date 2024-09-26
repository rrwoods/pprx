from matplotlib.ticker import FuncFormatter
import json
import math
import matplotlib.pyplot as plot


def tickformat(normscore, tickpos):
	score = 1000000 - (2**(-normscore))
	if score < 999000:
		return str(int(score/1000)) + 'k'
	return str(int((1000000 - score)/10)) + 'p'


def breakpoints(chart):
	x = json.loads(chart.normscore_breakpoints)
	y = json.loads(chart.quality_breakpoints)

	fig, ax = plot.subplots()

	fmt = FuncFormatter(tickformat)
	ax.xaxis.set_major_formatter(fmt)

	ax.set_xticks([-math.log2(10000)], minor=True)
	ax.xaxis.grid(True, which='minor')

	ax.set_yticks([chart.spice], minor=True)
	ax.yaxis.grid(True, which='minor')

	plot.plot(x, y, '-o')
	plot.show()