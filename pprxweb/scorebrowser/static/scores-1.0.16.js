var romanizeTitles = false

var userHidChartIds = []
var minTimestamp = 0

var songLevelStart = 0

var metGoals = 0
var totalGoals = 0

var allCharts = null

function escapeHtml(unsafe) {
    return unsafe
         .replace(/&/g, "&amp;")
         .replace(/</g, "&lt;")
         .replace(/>/g, "&gt;")
         .replace(/"/g, "&quot;")
         .replace(/'/g, "&#039;");
 }

$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	if (userHidChartIds.includes(parseInt(data[15]))) {
		return false
	}

	if (parseInt(data[11]) < minTimestamp) {
		return false
	}

	visibility = parseInt(data[parseInt($('#cabinet-select').find(':selected').val())])
	if (visibility === 3) {
		return false
	}
	if ((visibility === 2) && !($('#show-locked').is(':checked'))) {
		return false
	}

	var version_min = parseInt($('#version-min').find(':selected').val())
	if (version_min !== 0) {
		var version_max = parseInt($('#version-max').find(':selected').val())
		var version = parseInt(data[4])
		if ((version < version_min) || (version > version_max)) {
			return false
		}
	}

	var level_min = parseInt($('#level-min').find(':selected').val())
	var level_max = parseInt($('#level-max').find(':selected').val())
	var level = parseInt(data[7])
	if ((level < level_min) || (level > level_max)) {
		return false
	}

	var song_level_min = parseInt($('#song-level-min').find(':selected').val())
	var song_level_max = parseInt($('#song-level-max').find(':selected').val())
	song_level_met = false
	song_levels = allCharts[data[20]]
	for (var i = songLevelStart; i < song_levels.length; i++) {
		if ((song_levels[i] >= song_level_min) && (song_levels[i] <= song_level_max)) {
			song_level_met = true
			break
		}
	}
	if (!song_level_met) {
		return false
	}

	var hide_autospice = $('#hide-autospice').is(':checked')
	if (hide_autospice && (data[14] === "true")) {
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

	totalGoals++
	var hide_met_goals = $('#hide-met-goals').is(':checked')
	var goal_met = (score >= parseFloat(data[12])) && (score > 0)
	if (goal_met) {
		metGoals++
		if (hide_met_goals) {
			return false
		}
	}

	return true
})

$.fn.dataTableExt.oSort['nonzero-number-asc'] = function(a, b) {
	if (a === 0) {
		return 1
	}
	if (b === 0) {
		return -1
	}
	return Math.sign(a - b)
}

$.fn.dataTableExt.oSort['nonzero-number-desc'] = function(a, b) {
	if (a === 0) {
		return 1
	}
	if (b === 0) {
		return -1
	}
	return Math.sign(b - a)
}

$(document).ready(function () {
	romanizeTitles = $("#romanize-titles").data("x") === "True"

	function formatAge(timestamp) {
		if (timestamp === 0) {
			return ''
		}

		const ageFormatter = new Intl.RelativeTimeFormat(undefined, {numeric: 'auto', style: 'narrow'})
		const divisions = [
			{ maxAmt: 99, divAmt: 60, name: 'seconds' },
			{ maxAmt: 99, divAmt: 60, name: 'minutes' },
			{ maxAmt: 72, divAmt: 24, name: 'hours' },
			{ maxAmt: 30, divAmt: 7, name: 'days' },
			{ maxAmt: 8, divAmt: 4.34525, name: 'weeks' },
			{ maxAmt: 24, divAmt: 12, name: 'months' },
			{ maxAmt: Number.POSITIVE_INFINITY, divAmt: null, name: 'years' },
		]

		var duration = timestamp - loadTimestamp
		for (let i = 0; i < divisions.length; i++) {
			const division = divisions[i]
			if (Math.abs(duration) < division.maxAmt) {
				return ageFormatter.format(Math.round(duration), division.name)
			}
			duration /= division.divAmt
		}
	}

	const loadTimestamp = Math.floor(Date.now()/1000)

	allCharts = JSON.parse($('#all-charts').attr('data-json'))
	var scores = JSON.parse($('#jsonData').attr('data-json'))
	var scoresTable = $('#scores').DataTable({
		data: scores,
		responsive: true,
		columns: [
			{ data: '0', visible: false }, // white visibility
			{ data: '1', visible: false }, // gold visibility
			{ data: '2', visible: false }, // gold-only visibility
			// 3: (buttons)
			{
				data: null,
				title: '',
				orderable: false,
				searchable: false,
				className: 'buttons-cell',
				render: function(data, type, row, meta) {
					if (type !== "display") {
						return 0
					}
					notesIcon = row.notes ? '📋' : '✏️'
					return `<button class="hide-button">X</button> <button class="notes-button">${notesIcon}</button>`
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
						romanizeTitle = row.romanized_title && romanizeTitles
						displayTitle = romanizeTitle ? row.romanized_title : data.title
						displayClass = romanizeTitle ? 'class="romanized-title"' : ""
						return `<a target="_blank" ${displayClass} href=https://3icecream.com/ddr/song_details/${row.song_id}>${displayTitle}</a>`
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
						return `<a target="_blank" href="https://3icecream.com/ren/chart?songId=${row.song_id}&diff=${data.id}">${data.name} ${data.rating}</a>`
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
				data: 'timestamp',
				title: 'Age',
				className: 'border-right',
				type: 'nonzero-number',
				render: function(data, type, row, meta) {
					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}

					return formatAge(data)
				},
			},
			// 12:
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
			// 13:
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
			// 14:
			{ data: 'autospiced', visible: false },
			// 15:
			{ data: 'chart_id', visible: false },
			// 16:
			{ data: 'rank', visible: false },
			// 17:
			{ data: 'alternate_title', visible: false },
			// 18:
			{ data: 'romanized_title', visible: false },
			// 19:
			{ data: 'searchable_title', visible: false },
			// 20:
			{ data: 'song_id', visible: false },
			// 21:
			{ data: 'notes', visible: false },
		],
		createdRow: function(row, data, index) {
			visibility = parseInt(data[$('#cabinet-select').find(':selected').val()])
			if (visibility === 1) {
				$(row).addClass('extra-exclusive')
			} else if (visibility === 2) {
				$(row).addClass('locked-chart')
			}
		},
		order: [[16, 'asc']],
	})

	function setGoalSummary() {
		$("#goals-summary").text(`${metGoals} goals met, ${totalGoals - metGoals} remaining`)
	}

	setGoalSummary()

	function redrawTable(paging) {
		metGoals = 0
		totalGoals = 0
		scoresTable.draw(paging)
		setGoalSummary()
	}

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
		redrawTable(true)

		$.ajax({
			url: '/scorebrowser/set_goal',
			type: 'POST',
			data: JSON.stringify({'chart_id': row.chart_id, 'target_score': newGoal})
		})
	})

	$('#scores').on('click', 'button.hide-button', function() {
		row = scoresTable.row($(this).parents('tr')).data()
		userHidChartIds.push(row.chart_id)
		redrawTable(false)

		s = (userHidChartIds.length > 1) ? 's' : ''
		$('button.unhide-button').text(`Unhide ${userHidChartIds.length} manually-hidden chart${s}`)
		$('p.unhide-container').show()
	})

	$('#scores').on('click', 'button.notes-button', function() {
		notesButton = $(this)
		row = scoresTable.row(notesButton.parents('tr'))
		if (row.child.isShown()) {
			row.child.hide();
		} else {
			var notes = escapeHtml(row.data().notes)
			var chart_id = row.data().chart_id
			var notesBox = `Notes: <input type=text class="notes-field" id="notes-${chart_id}" data-chart=${chart_id} value="${notes}">`
			row.child(notesBox).show()
			
			notesElement = $(`#notes-${chart_id}`)
			notesElement.focus()
			notesElement.select()
			notesElement.focusout(function() {
				var newNotes = notesElement.val()
				if (notes === newNotes) {
					return
				}

				notes = newNotes
				row.data().notes = notes
				notesIcon = notes ? '📋' : '✏️'
				notesButton.text(notesIcon)

				$.ajax({
					type: "POST",
					url: "/scorebrowser/set_chart_notes",
					data: JSON.stringify({
						chart_id: chart_id,
						notes: notes,
					}),
				})
			})
		}
	})

	$('button.unhide-button').click(function () {
		$('p.unhide-container').hide()
		userHidChartIds = []
		redrawTable(false)
	})

	$('#cabinet-select').change(function() {
		redrawTable(true)
		applyRowClasses(scoresTable)
		updateAverages()
	})

	$('#level-select').change(function() {
		$(this).hide()
		level = $(this).find(':selected').val()
		$(`#level-min option[value="${level}"]`).prop('selected', true)
		$(`#level-max option[value="${level}"]`).prop('selected', true)
		$('#level-range').show()
		redrawTable(true)
	})

	$('#song-level-select').change(function() {
		$(this).hide()
		level = $(this).find(':selected').val()
		$(`#song-level-min option[value="${level}"]`).prop('selected', true)
		$(`#song-level-max option[value="${level}"]`).prop('selected', true)
		$('#song-level-range').show()
		redrawTable(true)
	})

	$('#version-select').change(function() {
		$(this).hide()
		versionId = $(this).find(':selected').val()
		$(`#version-min option[value="${versionId}"]`).prop('selected', true)
		$(`#version-max option[value="${versionId}"]`).prop('selected', true)
		$('#version-range').show()
		redrawTable(true)
	})

	function updateTimeRange() {
		timeText = $('#time-range').val()
		if (!$.isNumeric(timeText)) {
			minTimestamp = 0
			return
		}
		seconds = Math.floor(parseFloat(timeText) * 60 * 60)
		if ($('#time-type').val() !== 'hours') {
			seconds *= 24
		}

		minTimestamp = loadTimestamp - seconds
	}

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
		else if (elementId == 'song-level-min') {
			max = parseInt($('#song-level-max').find(':selected').val())
			if (max < selected) {
				$(`#song-level-max option[value="${selected}"]`).prop('selected', true)
			}
		} else if (elementId == 'song-level-max') {
			min = parseInt($('#song-level-min').find(':selected').val())
			if (min > selected) {
				$(`#song-level-min option[value="${selected}"]`).prop('selected', true)
			}
		} else if (elementId == 'song-beginner') {
			songLevelStart = $(`#song-beginner`).is(':checked') ? 0 : 1
		} else if (elementId == 'version-min') {
			max = parseInt($('#version-max').find(':selected').val())
			if (max < selected) {
				$(`#version-max option[value="${selected}"]`).prop('selected', true)
			}
		} else if (elementId == 'version-max') {
			min = parseInt($('#version-min').find(':selected').val())
			if (min > selected) {
				$(`#version-min option[value="${selected}"]`).prop('selected', true)
			}
		} else if (elementId == 'time-type') {
			updateTimeRange()
		}
		redrawTable(true)
	})

	$('.text-filter').keyup(function() {
		elementId = $(this).attr('id')
		if (elementId === 'time-range') {
			updateTimeRange()
		}
		redrawTable(true)
	})
})