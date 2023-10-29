const clearTypeIcons = [
	'<img src="/static/fail.png" class="inline-image">',
	'<input type="checkbox" class="life4-clear">',
	'<input type="checkbox" class="life4-clear" checked>',
	'<img src="/static/fc.webp" class="inline-image">',
	'<img src="/static/gfc.webp" class="inline-image">',
	'<img src="/static/pfc.webp" class="inline-image">',
	'<img src="/static/mfc.webp" class="inline-image">',
]

const clearTypes = [
	'Fail',
	'Clear',
	'LIFE4 Clear',
	'Full Combo',
	'Great Full Combo',
	'PFC',
]

const lampTypes = [
	'Fail',
	'Clear',
	'Red',
	'Blue',
	'Green',
	'Gold',
]

const trialClears = [
	"",
	"Silver",
	"Gold",
	"Platinum",
	"Diamond",
	"Cobalt",
	"Pearl",
	"Amethyst",
	"Emerald",
	"Onyx",
]

const mfcPoints = [0, 0.1, 0.25, 0.25, 0.5, 0.5, 0.5, 1, 1, 1, 1.5, 2, 4, 6, 8, 15, 25, 25, 25, 25]

var romanizeTitles = false
var cabinetSelect = 0
var showLocked = false
var show_unspiced = true
var bookmarks_only = false
var hide_met_goals = false

var version_min = 0
var version_max = 100

var level_min = 0
var level_max = 21

var song_level_min = 0
var song_level_max = 21
var songLevelStart = 0

var min_score = 0
var max_score = 1000000

var min_clear_type = -2
var max_clear_type = 6

var userHidChartIds = []
var minTimestamp = 0

var metGoals = 0
var totalGoals = 0

var allCharts = null
var rankRequirements = null
var selectedRank = null
var averages = []
var clears = []
var scoresByLevel = []
var lachendyScores = []
var mfcPointsEarned = 0
var checkedRequirements = null

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

	visibility = parseInt(data[cabinetSelect])
	if (visibility === 3) {
		return false
	}
	if ((visibility === 2) && !showLocked) {
		return false
	}

	if (version_min !== 0) {
		var version = parseInt(data[4])
		if ((version < version_min) || (version > version_max)) {
			return false
		}
	}

	var level = parseInt(data[7])
	if ((level < level_min) || (level > level_max)) {
		return false
	}

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

	var is_spiced = (data[14] === "true")
	if (!show_unspiced && !is_spiced) {
		return false
	}

	if (bookmarks_only && (data[23] === "false")) {
		return false
	}

	var score = parseFloat(data[9])
	if (score < min_score) {
		return false
	}
	if (score > max_score) {
		return false
	}

	var clear_type = (score === 0) ? -1 : parseInt(data[22])
	if (clear_type < min_clear_type) {
		return false
	}
	if (clear_type > max_clear_type) {
		return false
	}


	if (is_spiced) {
		totalGoals++
		var goal_met = (score >= parseFloat(data[12])) && (score > 0)
		if (goal_met) {
			metGoals++
			if (hide_met_goals) {
				return false
			}
		}
	}

	return true
})

$.fn.dataTableExt.oSort['nonzero-number-asc'] = function(a, b) {
	if (a === 0 || a === null) {
		return 1
	}
	if (b === 0 || b === null) {
		return -1
	}
	return Math.sign(a - b)
}

$.fn.dataTableExt.oSort['nonzero-number-desc'] = function(a, b) {
	if (a === 0 || a === null) {
		return 1
	}
	if (b === 0 || b === null) {
		return -1
	}
	return Math.sign(b - a)
}

$(document).ready(function () {
	romanizeTitles = $("#romanize-titles").data("x") === "True"
	cabinetSelect = parseInt($('#cabinet-select').find(':selected').val())

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

	checkedRequirements = $('#life4-reqs').data('json')
	allCharts = $('#all-charts').data('json')
	var scores = $('#jsonData').data('json')
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
				width: '1px',
				render: function(data, type, row, meta) {
					if (type !== "display") {
						return 0
					}
					var hideButton = '<button class="hide-button">X</button>'
					var notesIcon = row.notes ? '📋' : '✏️'
					var notesButton = `<button class="notes-button">${notesIcon}</button>`
					var bookmarkFile = row.bookmarked ? 'saved.png' : 'save.png'
					var bookmarkButton = `<button class="bookmark-button"><img src="/static/${bookmarkFile}" class="inline-image"></button>`
					return `${hideButton} ${notesButton} ${bookmarkButton}`
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
				type: 'nonzero-number',
				className: 'border-right',
				render: DataTable.render.number('', '.', 2),
			},
			// 9:
			{
				data: 'score',
				title: 'Score',
				render: function(data, type, row, meta) {
					if (type !== 'display') {
						return data
					}
					var scoreText = data.toLocaleString()
					var clearType = row.clear_type
					return `${scoreText}${clearTypeIcons[clearType]}`
				}
			},
			// 10:
			{
				data: 'quality',
				title: 'Quality',
				type: 'nonzero-number',
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
				type: 'nonzero-number',
				render: function(data, type, row, meta) {
					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}
					if (!row.spiced) {
						return ''
					}

					styles = ' class="unmet goal"'
					text = "None (Click to set)"
					if (data !== null) {
						text = data.toLocaleString()
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
				type: 'nonzero-number',
				render: function(data, type, row, meta) {
					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}

					if (data <= 0) {
						return ""
					}
					return "+" + data.toLocaleString()
				}
			},
			// 14:
			{ data: 'spiced', visible: false },
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
			// 22:
			{ data: 'clear_type', visible: false },
			// 23:
			{ data: 'bookmarked', visible: false },
			// 24:
			{ data: 'default_chart', visible: false },
			// 25:
			{ data: 'amethyst_required', visible: false },
		],
		createdRow: function(row, data, index) {
			visibility = parseInt(data[cabinetSelect])
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

	$('#reset-filters').click(function() {
		showLocked = false
		$('#show-locked').prop('checked', false)

		show_unspiced = false
		$('#show-unspiced').prop('checked', true)

		bookmarks_only = false
		$('#bookmarks-only').prop('checked', false)

		hide_met_goals = false
		$('#hide-met-goals').prop('checked', false)

		version_min = 0
		version_max = 100
		$('#version-range').hide()
		$('#version-select').val(0)
		$('#version-select').show()

		level_min = 0
		level_max = 21
		$('#level-range').hide()
		$('#level-select').val(0)
		$('#level-select').show()

		song_level_min = 0
		song_level_max = 21
		songLevelStart = 0
		$('#song-level-range').hide()
		$('#song-level-select').val(0)
		$('#song-level-select').show()
		$('#song-beginner').prop('checked', true)

		min_score = 0
		$('#min-score').val('')

		max_score = 1000000
		$('#max-score').val('')

		min_clear_type = -2
		max_clear_type = 6
		$('#clear-type-range').hide()
		$('#clear-type').val(-2)
		$('#clear-type').show()

		minTimestamp = 0
		$('#time-range').val('')
		$('#time-type').val('hours')

		redrawTable()
	})

	spiceHeader = scoresTable.column(8).header()
	$(spiceHeader).addClass('tooltip')
	$(spiceHeader).attr('title', "How hard a chart is, relative to all other charts (not just of the same rating).  If there's not enough data to accurately spice a song yet, it gets automatically assigned the lowest spice for its level for sorting purposes, and your goal will be the lowest for that level.")

	qualityHeader = scoresTable.column(10).header()
	$(qualityHeader).addClass('tooltip')
	$(qualityHeader).attr('title', 'How good your score is, relative to your other scores on other songs, normalized against how spicy the chart is.  Points beyond 999,000 do not contribute to quality rating, and goals will never be over 999,000.')

	function applyRowClasses(table) {
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			visibility = parseInt(this.data()[cabinetSelect])
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
			if (!d.spiced) {
				return
			}

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
		var notesButton = $(this)
		var row = scoresTable.row(notesButton.parents('tr'))
		if (row.child.isShown()) {
			row.child.hide();
		} else {
			var notes = escapeHtml(row.data().notes)
			var chart_id = row.data().chart_id
			var notesBox = `Notes: <input type=text class="notes-field" id="notes-${chart_id}" data-chart=${chart_id} value="${notes}" maxLength="1000">`
			row.child(notesBox).show()
			
			var notesElement = $(`#notes-${chart_id}`)
			notesElement.focus()
			notesElement.select()
			notesElement.focusout(function() {
				var newNotes = notesElement.val()
				if (notes === newNotes) {
					return
				}

				notes = newNotes
				row.data().notes = notes
				var notesIcon = notes ? '📋' : '✏️'
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

	$('#scores').on('click', 'button.bookmark-button', function() {
		var bookmarkButton = $(this)
		var row = scoresTable.row(bookmarkButton.parents('tr'))
		var rowData = row.data()
		rowData.bookmarked = !(rowData.bookmarked)
		var bookmarkFile = rowData.bookmarked ? 'saved.png' : 'save.png'
		bookmarkButton.html(`<img src="/static/${bookmarkFile}" class="inline-image">`)
		row.invalidate()
		$.ajax({
			type: "POST",
			url: "/scorebrowser/set_chart_bookmark",
			data: JSON.stringify({
				chart_id: rowData.chart_id,
				bookmark: rowData.bookmarked,
			}),
		})
	})

	$('#scores').on('change', 'input.life4-clear', function() {
		var life4Box = $(this)
		var checked = life4Box.is(':checked')
		var row = scoresTable.row(life4Box.parents('tr'))
		var rowData = row.data()
		rowData.clear_type = checked ? 2 : 1
		row.invalidate()

		$.ajax({
			type: "POST",
			url: "/scorebrowser/set_chart_life4",
			data: JSON.stringify({
				chart_id: rowData.chart_id,
				life4: checked,
			}),
		})
		evaluateRanks()
	})

	$('button.unhide-button').click(function () {
		$('p.unhide-container').hide()
		userHidChartIds = []
		redrawTable(false)
	})

	$('#cabinet-select').change(function() {
		cabinetSelect = parseInt($('#cabinet-select').find(':selected').val())
		redrawTable(true)
		applyRowClasses(scoresTable)
	})

	$('#level-select').change(function() {
		$(this).hide()
		level = $(this).find(':selected').val()
		level_min = parseInt(level)
		level_max = parseInt(level)
		$(`#level-min option[value="${level}"]`).prop('selected', true)
		$(`#level-max option[value="${level}"]`).prop('selected', true)
		$('#level-range').show()
		redrawTable(true)
	})

	$('#song-level-select').change(function() {
		$(this).hide()
		level = $(this).find(':selected').val()
		song_level_min = parseInt(level)
		song_level_max = parseInt(level)
		$(`#song-level-min option[value="${level}"]`).prop('selected', true)
		$(`#song-level-max option[value="${level}"]`).prop('selected', true)
		$('#song-level-range').show()
		redrawTable(true)
	})

	$('#version-select').change(function() {
		$(this).hide()
		versionId = $(this).find(':selected').val()
		versionMin = parseInt(versionId)
		versionMax = parseInt(versionId)
		$(`#version-min option[value="${versionId}"]`).prop('selected', true)
		$(`#version-max option[value="${versionId}"]`).prop('selected', true)
		$('#version-range').show()
		redrawTable(true)
	})

	$('#clear-type').change(function() {
		$(this).hide()
		clearType = $(this).find(':selected').val()
		min_clear_type = parseInt(clearType)
		max_clear_type = parseInt(clearType)
		$(`#clear-type-min option[value="${clearType}"]`).prop('selected', true)
		$(`#clear-type-max option[value="${clearType}"]`).prop('selected', true)
		$('#clear-type-range').show()
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
			level_min = selected
			if (level_max < selected) {
				$(`#level-max option[value="${selected}"]`).prop('selected', true)
				level_max = selected
			}
		} else if (elementId == 'level-max') {
			level_max = selected
			if (level_min > selected) {
				$(`#level-min option[value="${selected}"]`).prop('selected', true)
				level_min = selected
			}
		}
		else if (elementId == 'song-level-min') {
			song_level_min = selected
			if (song_level_max < selected) {
				$(`#song-level-max option[value="${selected}"]`).prop('selected', true)
				song_level_max = selected
			}
		} else if (elementId == 'song-level-max') {
			song_level_max = selected
			if (song_level_min > selected) {
				$(`#song-level-min option[value="${selected}"]`).prop('selected', true)
				song_level_min = selected
			}
		} else if (elementId == 'song-beginner') {
			songLevelStart = $(`#song-beginner`).is(':checked') ? 0 : 1
		} else if (elementId == 'version-min') {
			versionMin = selected
			if (versionMax < selected) {
				$(`#version-max option[value="${selected}"]`).prop('selected', true)
				versionMax = selected
			}
		} else if (elementId == 'version-max') {
			versionMax = selected
			if (versionMin > selected) {
				$(`#version-min option[value="${selected}"]`).prop('selected', true)
				versionMin = selected
			}
		} else if (elementId == 'clear-type-min') {
			min_clear_type = selected
			if (max_clear_type < selected) {
				$(`#clear-type-max option[value="${selected}"]`).prop('selected', true)
				max_clear_type = selected
			}
		} else if (elementId == 'clear-type-max') {
			max_clear_type = selected
			if (min_clear_type > selected) {
				$(`#clear-type-min option[value="${selected}"]`).prop('selected', true)
				min_clear_type = selected
			}
	    } else if (elementId == 'time-type') {
			updateTimeRange()
		} else if (elementId == 'show-locked') {
			showLocked = $('#show-locked').is(':checked')
		} else if (elementId == 'show-unspiced') {
			show_unspiced = $('#show-unspiced').is(':checked')
		} else if (elementId == 'bookmarks-only') {
			bookmarks_only = $('#bookmarks-only').is(':checked')
		} else if (elementId == 'hide-met-goals') {
			hide_met_goals = $('#hide-met-goals').is(':checked')
		}

		redrawTable(true)
	})

	$('.text-filter').keyup(function() {
		elementId = $(this).attr('id')
		if (elementId === 'time-range') {
			updateTimeRange()
		} else if (elementId === 'min-score') {
			var entered = $('#min-score').val()
			min_score = $.isNumeric(entered) ? parseFloat(entered) : 0
		} else if (elementId === 'max-score') {
			var entered = $('#max-score').val()
			max_score = $.isNumeric(entered) ? parseFloat(entered) : 1000000
		}

		redrawTable(true)
	})

	var requirementId = 0
	function nextReqId() {
		return requirementId++
	}

	function requirementDiv(text, checkable = false) {
		var div = $('<div>')

		var reqId = `req-${nextReqId()}`
		var checkbox = $('<input>', {type: 'checkbox', id: reqId, disabled: !checkable})
		div.append(checkbox)

		var description = $('<label>', {class: 'req-description', for: reqId})
		description.text(text)
		div.append(description)

		var togo = $('<span>', {class: 'togo'})
		div.append(togo)

		return div
	}

	rankRequirements = $('#rank-requirements').data('json')
	for (var index in rankRequirements) {
		var rank = rankRequirements[index]
		rank.option = $('<option>', {
			value: index,
			text: rank.name,
		})
		$('#rank-select').append(rank.option)

		rank.div = $('<div>')
		rank.div.hide()

		for (let level = 1; level < 20; level++) {
			if (!(level in rank.requirements)) {
				continue
			}
			var p = $('<p>')
			aAn = (level == 8 || level == 11 || level == 18) ? 'an' : 'a'
			for (let requirement of rank.requirements[level]) {
				switch(requirement.kind) {
				case 'scores':
					if (requirement.qty > 0) {
						var scoreText = (requirement.threshold == 990000) ? 'AAA' : (requirement.threshold/1000 + 'k+')
						var qtyText = requirement.qty == 1 ? aAn : requirement.qty
						var plural = requirement.qty == 1 ? '' : 's'
						var orHigher = requirement.or_higher ? '+' : ''
						requirement.div = requirementDiv(`${scoreText} ${qtyText} ${level}${plural}${orHigher}`)
					} else {
						var exceptions = requirement.qty == 0 ? '' : ` (${-requirement.qty} exceptions)`
						var lachendy = level == 19 ? ' (ex. Lachryma《Re:Queen’M》 & ENDYMION)' : ''
						requirement.div = requirementDiv(`All ${level}s over ${requirement.threshold/1000}k${exceptions}${lachendy}`)
					}
					break;
				case 'clears':
					if (requirement.qty == 0) {
						requirement.div = requirementDiv(`${level} ${lampTypes[requirement.threshold]} Lamp`)
					} else {
						var mandatory = requirement.mandatory ? '[MANDATORY] ' : ''
						var qtyText = requirement.qty == 1 ? aAn : requirement.qty
						var plural = requirement.qty == 1 ? '' : 's'
						var orHigher = requirement.or_higher ? '+' : ''
						requirement.div = requirementDiv(`${mandatory}${clearTypes[requirement.threshold]} ${qtyText} ${level}${plural}${orHigher}`)
					}
					break;
				case 'consecutives':
					requirement.div = requirementDiv(`Clear ${requirement.qty} ${level}s in a row`, true)
					requirement.div.find('input').change(function() {
						var postData = JSON.stringify({'passed': this.checked, 'count': requirement.qty, 'level': level})
						$.ajax({
							url: '/scorebrowser/set_consecutives',
							type: 'POST',
							data: postData,
							success: function(response) {
								checkedRequirements.consecutives = response
								evaluateRanks()
							}
						})					
					})
					break;
				case 'averages':
					requirement.div = requirementDiv(`${requirement.threshold.toLocaleString()} ${level}s average`)
					break;
				default:
					requirement.div = requirementDiv(JSON.stringify(requirement))
				}
				p.append(requirement.div)
			}
			if (level == 19 && 'lachendy' in rank.requirements) {
				for (var requirement of rank.requirements.lachendy) {
					requirement.div = requirementDiv(`${requirement.threshold/1000}k+ on Lachryma《Re:Queen’M》 challenge and ENDYMION challenge`)
					p.append(requirement.div)
				}
			}
			rank.div.append(p)
		}

		if ('calories' in rank.requirements) {
			var p = $('<p>')
			for (let requirement of rank.requirements.calories) {
				requirement.div = requirementDiv(`Burn ${requirement.threshold} calories in one day`, true)

				requirement.div.find('input').change(function() {
					var postData = JSON.stringify({'passed': this.checked, 'calories': requirement.threshold})
					$.ajax({
						url: '/scorebrowser/set_calories',
						type: 'POST',
						data: postData,
						success: function(response) {
							checkedRequirements.calories = response.calories
							evaluateRanks()
						}
					})					
				})

				p.append(requirement.div)
			}
			rank.div.append(p)
		}

		if ('trials' in rank.requirements) {
			var p = $('<p>')
			for (let requirement of rank.requirements.trials) {
				var plural = requirement.qty == 1 ? '' : 's'
				requirement.div = requirementDiv(`Earn ${trialClears[requirement.threshold]} or above on ${requirement.qty} Trial${plural}`, true)

				requirement.div.find('input').change(function() {
					var postData = JSON.stringify({'passed': this.checked, 'count': requirement.qty, 'rank': requirement.threshold})
					$.ajax({
						url: '/scorebrowser/set_trials',
						type: 'POST',
						data: postData,
						success: function(response) {
							checkedRequirements.trials = response
							evaluateRanks()
						}
					})					
				})
				
				p.append(requirement.div)
			}
			rank.div.append(p)
		}

		if ('mfc_points' in rank.requirements) {
			var p = $('<p>')
			for (var requirement of rank.requirements.mfc_points) {
				requirement.div = requirementDiv('')
				
				var label = $('<a>', {target: '_blank', href: 'https://life4ddr.com/rank-requirements/#mfcpoints'})
				label.text('MFC Points')
				var description = requirement.div.find('.req-description')
				description.append(label)
				description.append(`: ${requirement.threshold}`)

				p.append(requirement.div)
			}
			rank.div.append(p)
		}

		$('#rank-details').append(rank.div)
	}
	selectedRank = rankRequirements[0]
	selectedRank.div.show()

	function selectRank() {
		selectedRank.div.hide()

		rankIndex = $('#rank-select').find(':selected').val()
		rank = rankRequirements[rankIndex]
		selectedRank = rank
		rank.div.show()
	}
	$('#rank-select').change(selectRank)

	function isLachEndy(d) {
		if (d.difficulty.rating != 19) {
			return false
		}
		return (d.song_name.title == "Lachryma《Re:Queen’M》" || d.song_name.title == "ENDYMION")
	}

	for (var level = 1; level < 20; level++) {
		scoresByLevel[level] = {
			'all': [],
			'default': [],
			'non_default': [],
			'amethyst_required': [],
			'hard_unlocks': [],
		}

		clears[level] = []
		for (var clearType = 1; clearType <= 6; clearType++) {
			clears[level][clearType] = {
				'total': 0,
				'totalIncludingHigher': 0,
				'distanceToLamp': 0,
			}
		}
	}

	scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
		d = this.data()

		if (isLachEndy(d)) {
			lachendyScores.push(d.score)
		} else {
			scoresByLevel[d.difficulty.rating].all.push(d.score)

			var segment = d.default_chart ? 'default' : 'non_default'
			scoresByLevel[d.difficulty.rating][segment].push(d.score)

			segment = d.amethyst_required ? 'amethyst_required' : 'hard_unlocks'
			scoresByLevel[d.difficulty.rating][segment].push(d.score)
		}

		for (var clearType = 1; clearType <= d.clear_type; clearType++) {
			clears[d.difficulty.rating][clearType].total++
			for (var level = 1; level <= d.difficulty.rating; level++) {
				clears[level][clearType].totalIncludingHigher++
			}
		}

		if (d.default_chart) {
			for (var clearType = d.clear_type + 1; clearType <= 6; clearType++) {
				clears[d.difficulty.rating][clearType].distanceToLamp++
			}
		}

		if (d.clear_type == 6) {
			mfcPointsEarned += mfcPoints[d.difficulty.rating]
		}
	})

	for (var level = 1; level < 20; level++) {
		scoresByLevel[level].all.sort()
		scoresByLevel[level].default.sort()
		scoresByLevel[level].non_default.sort()
		scoresByLevel[level].amethyst_required.sort()
		scoresByLevel[level].hard_unlocks.sort()

		var defaultTotal = scoresByLevel[level].default.reduce((acc, cur) => acc + cur)
		var defaultCount = scoresByLevel[level].default.length
		var defaultAverage = defaultTotal / defaultCount
		for (var i = scoresByLevel[level].non_default.length - 1; i >= 0; i--) {
			var score = scoresByLevel[level].non_default[i]
			if (score <= defaultAverage) {
				break
			}
			defaultTotal += score
			defaultCount++
			defaultAverage = defaultTotal / defaultCount
		}

		var amethystTotal = scoresByLevel[level].amethyst_required.reduce((acc, cur) => acc + cur)
		var amethystCount = scoresByLevel[level].amethyst_required.length
		var amethystAverage = amethystTotal / amethystCount
		for (var i = scoresByLevel[level].hard_unlocks.length - 1; i >= 0; i--) {
			var score = scoresByLevel[level].hard_unlocks[i]
			if (score <= amethystAverage) {
				break
			}
			amethystTotal += score
			amethystCount++
			amethystAverage = amethystTotal / amethystCount
		}

		averages[level] = {
			'default': defaultAverage,
			'amethyst': amethystAverage,
		}
	}
	lachendyScores.sort()

	function qtyAboveThreshold(scoresList, threshold) {
		var metIndex = scoresList.findIndex((score) => score >= threshold)
		if (metIndex == -1) {
			return 0
		}
		return scoresList.length - metIndex
	}

	function styleReq(requirement, distance, additional = "") {
		var togo = requirement.div.find('.togo')
		togo.empty()

		var checkbox = requirement.div.find('input')

		if (!additional && (distance <= 0) && (distance != null)) {
			requirement.div.removeClass('unmet')
			requirement.div.addClass('met')
			checkbox.prop('checked', true)
			requirement.met = true
			return
		}

		var needs = []
		if (distance > 0) {
			needs.push(`${distance.toLocaleString()} more`)
		}
		if (additional) {
			needs.push(additional)
		}
		if (needs.length) {
			togo.text(` (need ${needs.join(' and ')})`)
		}
		requirement.div.removeClass('met')
		requirement.div.addClass('unmet')
		checkbox.prop('checked', false)
		requirement.met = false
	}

	function evaluateRanks() {
		var amethyst = false
		for (var index in rankRequirements) {
			rank = rankRequirements[index]
			if (rank.name.startsWith("Amethyst")) {
				amethyst = true
			}

			for (var level = 1; level < 20; level++) {
				if (!(level in rank.requirements)) {
					continue
				}
				for (var requirement of rank.requirements[level]) {
					switch(requirement.kind) {
					case 'scores':
						if (requirement.or_higher) {
							var qtyMet = 0
							for (var chartLevel = level; chartLevel < 20; chartLevel++) {
								qtyMet += qtyAboveThreshold(scoresByLevel[chartLevel].all, requirement.threshold)
								if (qtyMet >= requirement.qty) {
									styleReq(requirement, 0)
									break
								}
							}
							if (qtyMet < requirement.qty) {
								styleReq(requirement, requirement.qty - qtyMet)
							}
						} else {
							if (requirement.qty <= 0) {
								var segment = amethyst ? 'amethyst_required' : 'default'
								var qtyMet = qtyAboveThreshold(scoresByLevel[level][segment], requirement.threshold)
								var clearLamp = clears[level][1].distanceToLamp == 0 ? "" : "clear lamp"
								var qtyUnmet = scoresByLevel[level][segment].length - qtyMet
								styleReq(requirement, qtyUnmet + requirement.qty, clearLamp)
							} else {
								var qtyMet = qtyAboveThreshold(scoresByLevel[level].all, requirement.threshold)
								styleReq(requirement, requirement.qty - qtyMet)
							}
						}
						break;
					case 'clears':
						if (requirement.qty == 0) {
							distanceToLamp = clears[level][requirement.threshold].distanceToLamp
							styleReq(requirement, distanceToLamp)
						} else {
							total = requirement.or_higher ? clears[level][requirement.threshold].totalIncludingHigher : clears[level][requirement.threshold].total
							styleReq(requirement, requirement.qty - total)
						}
						break
					case 'consecutives':
						var attained = checkedRequirements.consecutives[requirement.qty]
						var distance = (attained >= level) ? 0 : null
						styleReq(requirement, distance)
						break
					case 'averages':
						var segment = amethyst ? 'amethyst' : 'default'
						styleReq(requirement, Math.ceil(requirement.threshold - averages[level][segment]))
						break
					}
				}
			}

			if ('lachendy' in rank.requirements) {
				for (var requirement of rank.requirements.lachendy) {
					remaining = lachendyScores.findIndex((score) => score >= requirement.threshold)
					if (remaining == -1) {
						remaining = lachendyScores.length
					}
					styleReq(requirement, remaining)
				}
			}

			if ('calories' in rank.requirements) {
				for (var requirement of rank.requirements.calories) {
					var distance = (checkedRequirements.calories >= requirement.threshold) ? 0 : null
					styleReq(requirement, distance)
				}
			}

			if ('trials' in rank.requirements) {
				for (var requirement of rank.requirements.trials) {
					var attained = (requirement.qty == 1) ? checkedRequirements.trials.best : checkedRequirements.trials.second
					var distance = (attained >= requirement.threshold) ? 0 : null
					styleReq(requirement, distance)
				}
			}

			if ('mfc_points' in rank.requirements) {
				for (var requirement of rank.requirements.mfc_points) {
					styleReq(requirement, requirement.threshold - mfcPointsEarned)
				}
			}

			var flattened = Object.values(rank.requirements).reduce((acc, cur) => acc.concat(cur))
			var remainingMandatory = flattened.reduce((acc, r) => (r.mandatory && !r.met) ? (acc + 1) : acc, 0)
			var metOptional = flattened.reduce((acc, r) => (!r.mandatory && r.met) ? (acc + 1) : acc, 0)
			var remainingOptional = rank.min - metOptional

			var remainingText = "attained"
			if (remainingOptional > 0) {
				if (remainingMandatory > 0) {
					remainingText = `need ${remainingMandatory} mandatory, plus ${remainingOptional} more`
				} else {
					remainingText = `need ${remainingOptional} more`
				}
			} else if (remainingMandatory > 0) {
				remainingText = `need ${remainingMandatory} mandatory`
			}

			var rankOption = $(`#rank-select option[value=${index}]`)
			rankOption.text(`${rank.name} (${remainingText})`)
		}
	}
	evaluateRanks()
})