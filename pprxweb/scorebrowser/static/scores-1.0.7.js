var userHidChartIds = []

$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	if (userHidChartIds.includes(parseInt(data[14]))) {
		return false
	}

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
	var level = parseInt(data[7])
	if ((level < level_min) || (level > level_max)) {
		return false
	}

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
	var goal_met = (score >= parseFloat(data[11])) && (score > 0)
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
			{ data: '0', visible: false }, // white visibility
			{ data: '1', visible: false }, // gold visibility
			{ data: '2', visible: false }, // gold-only visibility
			// 3: (hide button)
			{
				data: null,
				title: '',
				orderable: false,
				searchable: false,
				render: function(data, type, row, meta) {
					if (type !== "display") {
						return 0
					}
					return '<button class="hide-button">X</button>'
				}
			},
			// 4:
			{ data: 'game_version', title: 'Version', render: { display: 'name', sort: 'id', type: 'id', filter: 'id' } },
			// 5:
			{ 
				data: 'song_name',
				title: 'Song',
				className: 'border-right',
				render: function(data, type, row, meta) {
					if (type === "display") {
						return `<a target="_blank" href=https://3icecream.com/ddr/song_details/${data.id}>${data.title}</a>`
					}
					if (type === "sort") {
						return data.sort_key
					}
					return data.title
				}
			},
			// 6:
			{
				data: 'difficulty',
				title: 'Difficulty',
				searchable: false,
				render: function(data, type, row, meta) {
					if (type === 'display') {
						return `<a target="_blank" href="https://3icecream.com/ren/chart?songId=${row.song_name.id}&diff=${data.id}">${data.name} ${data.rating}</a>`
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
			{
				data: 'quality',
				title: 'Quality',
				className: 'border-right',
				render: function(data, type, row, meta) {
					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}

					if (!data) {
						return ''
					}
					quality = data.toFixed(2)
					return `${quality} (#${row.rank})`					
				}
			},
			// 11:
			{
				data: 'goal',
				title: 'Goal',
				render: function(data, type, row, meta) {
					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}

					styles = ' class="unmet goal"'
					text = "None (Click to set)"
					if (data !== null) {
						text = data.toLocaleString('en-US')
						if ((row.score >= data) && (row.score > 0)) {
							styles = ' class="met goal"'
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
					if (type === "sort" || type === "type" || type === "filter") {
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
			{ data: 'chart_id', visible: false },
			// 15:
			{ data: 'rank', visible: false },
			// 16:
			{ data: 'alternate_title', visible: false },
			// 17:
			{ data: 'romanized_title', visible: false },
			// 18:
			{ data: 'searchable_title', visible: false },
		],
		createdRow: function(row, data, index) {
			visibility = parseInt(data[$('#cabinet-select').find(':selected').val()])
			if (visibility === 1) {
				$(row).addClass('extra-exclusive')
			} else if (visibility === 2) {
				$(row).addClass('locked-chart')
			}
		},
		order: [[15, 'asc']],
	})

	spiceHeader = scoresTable.column(8).header()
	$(spiceHeader).addClass('tooltip')
	$(spiceHeader).attr('title', "How hard a chart is, relative to all other charts (not just of the same rating).  If there's not enough data to accurately spice a song yet, it gets automatically assigned the lowest spice for its level for sorting purposes, and your goal will be the lowest for that level.")

	qualityHeader = scoresTable.column(10).header()
	$(qualityHeader).addClass('tooltip')
	$(qualityHeader).attr('title', 'How good your score is, relative to your other scores on other songs, normalized against how spicy the chart is.  Points beyond 999,000 do not contribute to quality rating, and goals will never be over 999,000.')

	updateAverages()

	function applyRowClasses(table) {
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			visibility = parseInt(this.data()[$('#cabinet-select').find(':selected').val()])
			if (visibility === 1) {
				$(this.node()).addClass('extra-exclusive')
				$(this.node()).removeClass('locked-chart')				
			} else if (visibility === 2) {
				$(this.node()).removeClass('extra-exclusive')
				$(this.node()).addClass('locked-chart')				
			} else {
				$(this.node()).removeClass('extra-exclusive')				
				$(this.node()).removeClass('locked-chart')				
			}
		})
	}

	function updateAverages() {
		$('.averages').hide()
		cab = $('#cabinet-select').find(':selected').val()
		$(`#${cab}-averages`).show()
	}

	$('#scores').on('click', 'button.goal', function() {
		row = scoresTable.row($(this).parents('tr')).data()
		newGoal = prompt(`Set goal for ${row.song_name.title} ${row.difficulty.name} -- this will recalibrate all other goal scores!`, row.goal || 0)
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

	$('#scores').on('click', 'button.hide-button', function() {
		row = scoresTable.row($(this).parents('tr')).data()
		userHidChartIds.push(row.chart_id)
		scoresTable.draw(false)

		s = (userHidChartIds.length > 1) ? 's' : ''
		$('button.unhide-button').text(`Unhide ${userHidChartIds.length} manually-hidden chart${s}`)
		$('p.unhide-container').show()
	})

	$('button.unhide-button').click(function () {
		$('p.unhide-container').hide()
		userHidChartIds = []
		scoresTable.draw(false)
	})

	$('#cabinet-select').change(function() {
		scoresTable.draw()
		applyRowClasses(scoresTable)
		updateAverages()
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