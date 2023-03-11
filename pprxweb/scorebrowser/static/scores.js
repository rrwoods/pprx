$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	if (parseInt(data[parseInt($('#cabinet-select').find(':selected').val())]) === 2) {
		return false
	}

	var level_select = $('#level-select').find(':selected').val()
	if ((level_select != 0) && (level_select != data[7])) {
		return false
	}

	console.log(data)
	var hide_autospice = $('#hide-autospice').is(':checked')
	if (hide_autospice && (data[13] === "true")) {
		return false
	}

	var score = parseFloat(data[9])

	var min_score = $('#min-score').val()
	if ($.isNumeric(min_score) && (score < parseFloat(min_score))) {
		return false
	}

	var max_score = $('#max-score').val()
	if ($.isNumeric(max_score) && (score >= parseFloat(max_score))) {
		return false
	}

	var hide_met_goals = $('#hide-met-goals').is(':checked')
	var goal_met = score >= parseFloat(data[11])
	if (hide_met_goals && goal_met) {
		return false
	}

	return true
})

$(document).ready(function () {
	var scores = JSON.parse($('#jsonData').attr('data-json'))
	var scoresTable = $('#scores').DataTable({
		data: scores,
		responsive: true,
		columns: [
			{ data: '0', visible: false },
			{ data: '1', visible: false },
			{ data: '2', visible: false },
			{ data: '3', visible: false },
			// 4:
			{ data: 'game_version', title: 'Version', render: { display: 'name', sort: 'id', type: 'id' } },
			// 5:
			{ data: 'song_name', title: 'Song', className: 'border-right' },
			// 6:
			{
				data: 'difficulty',
				title: 'Difficulty',
				//render: { display: 'name', sort: 'rating', type: 'id' }
				render: function(data, type, row, meta) {
					if (type === 'display') {
						return data.name + ' ' + data.rating
					}
					return data.rating
				}
			},
			// 7:
			{ data: 'rating', visible: false },
			// 8:
			{
				data: 'spice',
				title: 'Spice',
				className: 'border-right',
				render: DataTable.render.number('', '.', 2),
				createdCell: function(td, cellData, rowData, row, col) {
					if (rowData.autospiced) {
						$(td).addClass('autospice')
					}
				}
			},
			// 9:
			{ data: 'score', title: 'Score', render: DataTable.render.number(',', '.', 0) },
			// 10:
			{ data: 'quality', title: 'Quality', className: 'border-right', render: DataTable.render.number('', '.', 2) },
			// 11:
			{
				data: 'goal',
				title: 'Goal',
				render: function(data, type, row, meta) {
					if (type == "sort" || type == "type" || type == "filter") {
						return data
					}

					styles = ""
					text = "None (Click to set)"
					if (data !== null) {
						text = data.toLocaleString('en-US')
						if (row.score >= data) {
							styles = ' class="met-goal"'
						}
					}
					return `<button${styles}>${text}</button>`
				},
			},
			// 12:
			{
				data: 'distance',
				title: 'Dist.',
				render: function(data, type, row, meta) {
					if (type == "sort" || type == "type" || type == "filter") {
						return data
					}

					if (data <= 0) {
						return ""
					}
					return "+" + data.toLocaleString('en-US')
				}
			},
			// 13:
			{ data: 'autospiced', visible: false },
			// 14:
			{ data: 'chart_id', visible: false},
		],
		createdRow: function(row, data, index) {
			if (parseInt(data[$('#cabinet-select').find(':selected').val()]) === 1) {
				$(row).addClass('extra-exclusive')
			}
		},
	})

	spiceHeader = scoresTable.column(8).header()
	$(spiceHeader).addClass('tooltip')
	$(spiceHeader).attr('title', 'How hard a chart is, relative to all other charts (not just of the same rating).')

	qualityHeader = scoresTable.column(10).header()
	$(qualityHeader).addClass('tooltip')
	$(qualityHeader).attr('title', 'How good your score is, relative to your other scores on other songs, normalized against how spicy the chart is.  Points beyond 999,000 do not contribute to quality rating, and goals will never be over 999,000.')

	function applyRowClasses(table) {
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			if (parseInt(this.data()[$('#cabinet-select').find(':selected').val()]) === 1) {
				$(this.node()).addClass('extra-exclusive')
			} else {
				$(this.node()).removeClass('extra-exclusive')
			}
		})
	}

	$('#scores').on('click', 'button', function() {
		row = scoresTable.row($(this).parents('tr')).data()
		newGoal = prompt(`Set goal for ${row.song_name} ${row.difficulty.name} -- this will recalibrate all other goal scores!`, row.goal || 0)
		if (!newGoal) {
			return
		}

		newGoal = parseInt(newGoal.replace(',', ''))
		if (isNaN(newGoal)) {
			return
		}
		newGoal = Math.min(999000, Math.max(1, newGoal)) - 1

		targetQuality = row.spice - Math.log2((1000001 - newGoal)/1000000)
		scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
			d = this.data()
			d.goal = 1000001 - 15625*Math.pow(2, 6 + d.spice - targetQuality)
			d.goal = Math.min(999000, Math.max(0, Math.ceil(d.goal/10) * 10))
			d.distance = d.goal - d.score
			this.invalidate()
		})
		scoresTable.draw()

		$.ajax({
			url: '/scorebrowser/set_goal',
			type: 'POST',
			data: JSON.stringify({'chart_id': row.chart_id, 'target_score': newGoal})
		})
	})

	$('#cabinet-select').change(function() {
		scoresTable.draw()
		applyRowClasses(scoresTable)
	})

	$('.select-filter').change(function() {
		scoresTable.draw()
	})

	$('.text-filter').keyup(function() {
		scoresTable.draw()
	})
})