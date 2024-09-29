from cir_model import CenteredIsotonicRegression
from django.core.management.base import BaseCommand, CommandError
from numpy import interp
from scorebrowser.models import *
import json
import math


class Command(BaseCommand):
	help = 'Give each spiced chart a set of quality benchmarks by pairwise comparison and centered isotonic regression.'

	def handle(self, *args, **options):
		# these values are hand-picked for quality range decompression (see step 5 below).
		anchor_chart_id = Chart.objects.get(song__title="ロールプレイングゲーム", difficulty_id=3).id
		anchor_zero = -math.log2(1000000 - 980000)
		anchor_one = -math.log2(1000000 - 990000)

		final_anchor_chart_id = Chart.objects.get(song__title="MAX 300", difficulty_id=3).id
		final_anchor_ten = -math.log2(1000000 - 990000)


		# STEP 0: DECIDE WHICH CHARTS TO COMPARE

		# Pairs of charts that are compared in this phase ideally match two characteristics:
		# Their spice is relatively close (within ???), and their level is relatively close (within 1).
		# As of this writing there are ~1,500 spiced charts.  Comparing each one with 66 other
		# charts gives 100,000 comparisons (counting each pair twice, because the comparison is
		# ultimately performed in both directions).

		print("Deciding on chart pairs...")
		spiced_charts = list(Chart.objects.exclude(spice=None).order_by('spice'))
		chart_pairs = []
		for i in range(len(spiced_charts)):
			i_compares = 0
			for j in range(i, len(spiced_charts)):
				if abs(spiced_charts[i].rating - spiced_charts[j].rating) > 1:
					continue
				if abs(spiced_charts[i].spice - spiced_charts[j].spice) > 0.5:
					continue
				chart_pairs.append((spiced_charts[i].id, spiced_charts[j].id))
				i_compares += 1
				if i_compares == 33:
					break
		n = len(chart_pairs)
		print("... got {} pairs.".format(n))



		# STEP 1: INITIAL QUALITY ASSIGNMENT

		# Make an initial assumption about the quality of each public score for any given
		# chart, basing this assumption on the normalized score and the chart's level.

		# Store these assumptions as references that can be updated as we go -- to do this
		# we use a one-element list, which is the closest thing python has to a pointer-
		# to-primitive.

		# assumed_quality = {chart_id: {normalized_score: [quality]}}
		print("Building initial quality assumptions...")
		initial_quality = {}
		public_scores = Score.objects.all().prefetch_related('chart')
		public_count = public_scores.count()
		batch_size = 1000
		print("Working with {} public scores.".format(public_count))

		# Additionally, to make step 2 easier, we pre-group all the public scores by player
		# id and chart id.
		player_scores = {}
		for i in range(0, public_count, batch_size):
			print(public_count - i)
			batch = public_scores[i:i+batch_size]
			for entry in batch:
				if not entry.chart.spice:
					continue

				if entry.player_id not in player_scores:
					player_scores[entry.player_id] = {}
				player_scores[entry.player_id][entry.chart_id] = entry.normalized

				if entry.chart_id not in initial_quality:
					initial_quality[entry.chart_id] = {}
				if entry.normalized not in initial_quality[entry.chart_id]:
					initial_quality[entry.chart_id][entry.normalized] = [entry.normalized + entry.chart.spice]
			del batch

		# re-sort each of the quality dictionaries by key, so that the lowest score is first.
		print("Constructing assumptions map...")
		assumed_quality = {}
		for chart_id, assumptions in initial_quality.items():
			assumed_quality[chart_id] = {k: v for k, v in sorted(assumptions.items())}
		del initial_quality



		# STEP 2: RAW DERIVATION, AND MAGIC DATA STRUCTURE

		# Make a second-order assumption about the quality of each score.  For each pair
		# of charts (x, y) we've decided to compare, for each player that has a score
		# on both charts, store a pointer to the quality for y based on the score of x.
		# This represents the assumption that a player will generally have same-quality
		# scores on all charts.

		# derived_quality = {chart_id: [(normalized_score, [quality], weight)]}

		# As an example, if rrwoods has 997400 on POSSESSION difficult, and 995670 on
		# MAX 300 expert, this derived quality dictionary will get the following two
		# entries:
		# {MAX 300: [(995670, [POSSESSION's assumed quality for 997400])]}
		# {POSSESSION: [(997400, [MAX 300's assumed quality for 995670])]}

		# This results in a data structure that *points at* quality values from the
		# assumed_quality dictionary, saving the need to rebuild it on each pass.
		print("Building derivation structure...")
		derived_quality = {chart_id: [] for chart_id in assumed_quality}

		# one perfect normalizes to -3.something, MFC normalizes to -2.something.
		# we don't make any derived assumptions _from_ an MFC.
		mfc_cutoff = -3

		for chart_pair in chart_pairs:
			for (player_id, chart_scores) in player_scores.items():
				if (chart_pair[0] in chart_scores) and (chart_pair[1] in chart_scores):
					xnormalized = chart_scores[chart_pair[0]]
					ynormalized = chart_scores[chart_pair[1]]
					weight = 2 - abs(xnormalized - ynormalized)
					if weight <= 0:
						continue

					if (xnormalized < mfc_cutoff):
						derived_quality[chart_pair[1]].append((ynormalized, assumed_quality[chart_pair[0]][xnormalized], weight))
					if (ynormalized < mfc_cutoff):
						derived_quality[chart_pair[0]].append((xnormalized, assumed_quality[chart_pair[1]][ynormalized], weight))
			n -= 1
			print(n)
		del player_scores  # this thing is massive
		del chart_pairs



		# ITERATION STARTS
		max_iterations = 3
		for iteration in range(max_iterations):
			print("Running regressions, {} iterations remaining".format(max_iterations - iteration))

			# STEP 3: RUN ALL THE REGRESSIONS

			# For each chart, run a centered isotonic regression, with _that chart's_
			# normalized scores on X and the derived quality values on Y.
			models = {}
			for chart_id, estimates in derived_quality.items():
				if (len(estimates) == 0):
					chart = Chart.objects.get(id=chart_id)
					print("No estimates for {} {}".format(chart.song.title, chart.difficulty.name))
				x = [e[0] for e in estimates]
				y = [e[1][0] for e in estimates]
				weights = [e[2] for e in estimates]
				models[chart_id] = CenteredIsotonicRegression().fit(x, y, sample_weight=weights)



			# STEP 4: UPDATE QUALITY ASSUMPTIONS

			# For each chart, use the computed regression model to update assumed_quality.
			# Because derived_quality's values are pointers into assumed_quality, this
			# automatically updates all of those values for the next pass.

			# IMPORTANT:
			# This MUST BE DONE SEPARATELY from step 3, _after_ all regressions have been
			# run... since updating assumed_quality automatically updates derived_quality!
			print("Updating quality assumptions")
			for chart_id, model in models.items():
				min_score = model.X_thresholds_[0]
				max_score = model.X_thresholds_[-1]
				for normalized_score, quality_pointer in assumed_quality[chart_id].items():
					target = None
					if normalized_score < min_score:
						target = model.transform([min_score])[0] - min_score + normalized_score
					elif normalized_score > max_score:
						target = model.transform([max_score])[0] + normalized_score - max_score
					else:
						target = model.transform([normalized_score])[0]
					# quality_pointer[0] = (target + quality_pointer[0]) / 2
					quality_pointer[0] = target



			# STEP 5: NORMALIZE QUALITY ASSUMPTIONS FOR ITERATION

			# The above process will always result in a very slight compression of the
			# entire range of quality values, because (necessarily) all resulting
			# derived quality values will fall between the minimum and maximum assumed
			# quality values.  Ultimately this will completely flatten every quality
			# value to the same number.  To counteract this, we pick a chart (RPG expert)
			# and two scores (980k and 990k), and perform a translation and a scaling
			# to ensure that these two scores on this chart are always 1.000 apart.
			print("Normalizing quality assumptions")
			estimate_zero = interp(anchor_zero, list(assumed_quality[anchor_chart_id].keys()), [y[0] for y in assumed_quality[anchor_chart_id].values()])
			estimate_one = interp(anchor_one, list(assumed_quality[anchor_chart_id].keys()), [y[0] for y in assumed_quality[anchor_chart_id].values()])
			translate_amt = -estimate_zero
			scale_factor = 1/(estimate_one - estimate_zero)

			for chart_id, assumptions in assumed_quality.items():
				for normalized_score, quality_pointer in assumptions.items():
					quality_pointer[0] = (quality_pointer[0] + translate_amt) * scale_factor

			### DEBUG STATEMENTS ###
			print("MAX 300 AAA =", interp(final_anchor_ten, list(assumed_quality[final_anchor_chart_id].keys()), [y[0] for y in assumed_quality[final_anchor_chart_id].values()]))



		# STEP 6: DATA TRANSFORM + FINAL QUALITY SHIFT FOR CONSUMPTION
		# Shift all the quality values so that a MAX 300 AAA is 10.0.
		# final_quality = {chart_id: ([normalized_scores], [qualities])}
		# The [xs], [ys] structure is preparation for final storage, as it's
		# the form numpy.interp will want when we use these values to compute
		# the quality of a score for the player.
		# We also round all these values to the nearest three decimals for storage,
		# since they are stored as strings and more fidelity than that is not
		# necessary.
		print("Final normalization for display")
		final_quality = {}
		for chart_id, estimates in assumed_quality.items():
			normalized_scores = list(sorted(estimates.keys()))
			qualities = [estimates[x][0] for x in normalized_scores]
			final_quality[chart_id] = ([int(1000*x)/1000 for x in normalized_scores], qualities)

		anchor_estimates = final_quality[final_anchor_chart_id]
		current_anchor = interp(final_anchor_ten, anchor_estimates[0], anchor_estimates[1])
		translate_amt = 10.0 - current_anchor
		for chart_id, estimates in final_quality.items():
			for i, quality in enumerate(estimates[1]):
				estimates[1][i] = int(1000*(quality + translate_amt))/1000
			highest_score = estimates[0][-1]
			if highest_score < -2.322:
				highest_quality = estimates[1][-1]
				boost = -2.322 - highest_score
				estimates[0].append(-2.322)
				estimates[1].append(int(1000*(highest_quality + boost))/1000)



		# STEP 7: WRITE ALL THIS CRAP TO THE DATABASE
		print("Clearing existing breakpoints")
		Chart.objects.all().update(normscore_breakpoints='', quality_breakpoints='')

		print("Writing breakpoints to database")
		spice_updates = []
		for chart in spiced_charts:
			estimates = final_quality[chart.id]
			chart.normscore_breakpoints = json.dumps(estimates[0])
			chart.quality_breakpoints = json.dumps(estimates[1])
			spice_updates.append(chart)
		Chart.objects.bulk_update(spice_updates, ['normscore_breakpoints', 'quality_breakpoints'])