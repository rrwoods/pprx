from matplotlib.ticker import FuncFormatter
import json
import math
import matplotlib.pyplot as plt


def tickformat(normscore, tickpos):
	return str((int(-(2**(-normscore))/10)*10) + 1000000)


def breakpoints(chart):
	return json.loads(chart.normscore_breakpoints), json.loads(chart.quality_breakpoints)


def plot(x, y, spice):
	fig, ax = plt.subplots()

	fmt = FuncFormatter(tickformat)
	ax.xaxis.set_major_formatter(fmt)

	ax.set_xticks([-math.log2(10000)], minor=True)
	ax.xaxis.grid(True, which='minor')

	ax.set_yticks([spice], minor=True)
	ax.yaxis.grid(True, which='minor')

	plt.plot(x, y, '-o')
	plt.show()


def display(chart):
	x, y = breakpoints(chart)
	plot(x, y, chart.spice)