$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	visibility = parseInt(data[parseInt($('#cabinet-select').find(':selected').val())])
	if (visibility === 3) {
		return false
	}
	if ((visibility === 2) && !($('#show-locked').is(':checked'))) {
		return false
	}

	var selected_version = $('#version-select').find(':selected').val()
	if ((selected_version !== "0") && (selected_version !== data[3])) {
		return false
	}

	var level_min = parseInt($('#level-min').find(':selected').val())
	var level_max = parseInt($('#level-max').find(':selected').val())
	var level = parseInt(data[6])
	if ((level < level_min) || (level > level_max)) {
		return false
	}

	var hide_autospice = $('#hide-autospice').is(':checked')
	if (hide_autospice && (data[12] === "true")) {
		return false
	}

	var score = parseFloat(data[8])

	var min_score = $('#min-score').val()
	if ($.isNumeric(min_score) && (score < parseFloat(min_score))) {
		return false
	}

	var max_score = $('#max-score').val()
	if ($.isNumeric(max_score) && (score >= parseFloat(max_score))) {
		return false
	}

	var hide_met_goals = $('#hide-met-goals').is(':checked')
	var goal_met = (score >= parseFloat(data[10])) && (score > 0)
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
			// 3:
			{ data: 'game_version', title: 'Version', render: { display: 'name', sort: 'id', type: 'id', filter: 'id' } },
			// 4:
			{ 
				data: 'song_name',
				title: 'Song',
				className: 'border-right',
				render: function(data, type, row, meta) {
					if (type === "display") {
						return `<a target="_blank" href=https://3icecream.com/ddr/song_details/${data.id}>${data.title}</a>`
					}
					return data.title
				}
			},
			// 5:
			{
				data: 'difficulty',
				title: 'Difficulty',
				//render: { display: 'name', sort: 'rating', type: 'id' }
				render: function(data, type, row, meta) {
					if (type === 'display') {
						return `<a target="_blank" href="https://3icecream.com/ren/chart?songId=${row.song_name.id}&diff=${data.id}">${data.name} ${data.rating}</a>`
					}
					return data.rating
				}
			},
			// 6:
			{ data: 'rating', visible: false },
			// 7:
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
			// 8:
			{ data: 'score', title: 'Score', render: DataTable.render.number(',', '.', 0) },
			// 9:
			{ data: 'quality', title: 'Quality', className: 'border-right', render: DataTable.render.number('', '.', 2) },
			// 10:
			{
				data: 'goal',
				title: 'Goal',
				render: function(data, type, row, meta) {
					if (type == "sort" || type == "type" || type == "filter") {
						return data
					}

					styles = ' class="unmet-goal"'
					text = "None (Click to set)"
					if (data !== null) {
						text = data.toLocaleString('en-US')
						if ((row.score >= data) && (row.score > 0)) {
							styles = ' class="met-goal"'
						}
					}
					return `<button${styles}>${text}</button>`
				},
			},
			// 11:
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
			// 12:
			{ data: 'autospiced', visible: false },
			// 13:
			{ data: 'chart_id', visible: false},
		],
		createdRow: function(row, data, index) {
			visibility = parseInt(data[$('#cabinet-select').find(':selected').val()])
			if (visibility === 1) {
				$(row).addClass('extra-exclusive')
			} else if (visibility === 2) {
				$(row).addClass('locked-chart')
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

	$('#level-select').change(function() {
		$(this).hide()
		level = $(this).find(':selected').val()
		$(`#level-min option[value="${level}"]`).prop('selected', true)
		$(`#level-max option[value="${level}"]`).prop('selected', true)
		$('#level-range').show()
		scoresTable.draw()
	})

	$('.select-filter').change(function() {
		elementId = $(this).attr('id')
		selected = parseInt($(this).find(':selected').val())
		if (elementId == 'level-min') {
			max = parseInt($('#level-max').find(':selected').val())
			if (max < selected) {
				$(`#level-max option[value="${selected}"]`).prop('selected', true)
			}
		} else if (elementId == 'level-max') {
			min = parseInt($('#level-min').find(':selected').val())
			if (min > selected) {
				$(`#level-min option[value="${selected}"]`).prop('selected', true)
			}
		}
		scoresTable.draw()
	})

	$('.text-filter').keyup(function() {
		scoresTable.draw()
	})
})