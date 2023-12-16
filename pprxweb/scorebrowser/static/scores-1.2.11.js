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

var currentFilters = {}
var baseFilters = {}
var defaultFilters = {}
var userHidChartIds = []
var minTimestamp = 0

var metGoals = 0
var totalGoals = 0

var allCharts = null
var rankRequirements = null
var selectedRank = null
var requirementTargets = null
var averages = []
var clears = []
var scoresByLevel = []
var lachendyScores = []
var mfcPointsEarned = 0
var checkedRequirements = null
var whiteVersion = 0

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

	// if ((data[26] === "true") && !currentFilters["show-removed"]) {
	// 	return false
	// }

	visibility = parseInt(data[currentFilters["cabinet-select"]])
	if (visibility === 3) {
		if (data[26] === "true") {
			if (!currentFilters["show-removed"]) {
				return false
			}
		} else {
			return false
		}
	}
	if ((visibility === 2) && !currentFilters["show-locked"]) {
		return false
	}

	var version = parseInt(data[4])
	if ((version < currentFilters["version-min"]) || (version > currentFilters["version-max"])) {
		return false
	}

	var level = parseInt(data[7])
	if ((level < currentFilters["level-min"]) || (level > currentFilters["level-max"])) {
		return false
	}

	song_level_met = false
	song_levels = allCharts[data[20]]
	for (var i = (currentFilters["song-beginner"] ? 0 : 1); i < song_levels.length; i++) {
		if ((song_levels[i] >= currentFilters["song-level-min"]) && (song_levels[i] <= currentFilters["song-level-max"])) {
			song_level_met = true
			break
		}
	}
	if (!song_level_met) {
		return false
	}

	if (currentFilters["hide-optional"]) {
		var optional = selectedRank.amethyst ? (data[25] === "false") : (data[24] === "false")
		if (optional) {
			return false
		}
	}

	var is_spiced = (data[14] === "true")
	if (!currentFilters["show-unspiced"] && !is_spiced) {
		return false
	}

	if (currentFilters["bookmarks-only"] && (data[23] === "false")) {
		return false
	}

	var score = parseFloat(data[9])
	if (score < currentFilters["min-score"]) {
		return false
	}
	if (score > currentFilters["max-score"]) {
		return false
	}

	var clear_type = (score === 0) ? -1 : parseInt(data[22])
	if (clear_type < currentFilters["clear-type-min"]) {
		return false
	}
	if (clear_type > currentFilters["clear-type-max"]) {
		return false
	}


	if (is_spiced) {
		totalGoals++
		var goal_met = (score >= parseFloat(data[12])) && (score > 0)
		if (goal_met) {
			metGoals++
			if (currentFilters["hide-met-goals"]) {
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

	$('#version-min').val(1)
	$('#version-max').val($("#version-max option").length)

	$("[type='checkbox'].filter").each(function() {
		currentFilters[this.id] = this.checked
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = this.checked
		}
	})
	$("[type='number'].filter").each(function() {
		currentFilters[this.id] = parseInt(this.value)
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = parseInt(this.value)
		}
	})
	$("select.filter").each(function() {
		currentFilters[this.id] = parseInt(this.value)
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = parseInt(this.value)
		}
	})
	Object.assign(baseFilters, currentFilters)
	baseFilters["show-locked"] = true
	baseFilters["hide-optional"] = true

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
			// 26:
			{ data: 'removed', visible: false },
		],
		createdRow: function(row, data, index) {
			visibility = parseInt(data[currentFilters["cabinet-select"]])
			if (visibility === 1) {
				$(row).addClass('extra-exclusive')
			} else if (visibility === 2) {
				$(row).addClass('locked-chart')
			}
			if (data.removed) {
				$(row).addClass('removed-song')
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

	function setFilters(newFilters) {
		for (var name in newFilters) {
			var newValue = newFilters[name]
			currentFilters[name] = newValue
			var element = $(`#${name}.filter`)
			if (element.is("select") || element.attr("type") === "number") {
				element.val(newValue)
			} else {
				element.prop('checked', newValue)
			}
		}
		updateTimeRange()
		redrawTable()
	}

	$('#reset-filters').click(function() {
		setFilters(defaultFilters)
	})

	var spiceHeader = scoresTable.column(8).header()
	$(spiceHeader).addClass('tooltip')
	$(spiceHeader).attr('title', "How hard a chart is, relative to all other charts (not just of the same rating).  If there's not enough data to accurately spice a song yet, it gets automatically assigned the lowest spice for its level for sorting purposes, and your goal will be the lowest for that level.")

	var qualityHeader = scoresTable.column(10).header()
	$(qualityHeader).addClass('tooltip')
	$(qualityHeader).attr('title', 'How good your score is, relative to your other scores on other songs, normalized against how spicy the chart is.  Points beyond 999,000 do not contribute to quality rating, and goals will never be over 999,000.')

	function applyRowClasses(table) {
		var cab = currentFilters["cabinet-select"]
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			visibility = parseInt(this.data()[cab])
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

		var level = rowData.difficulty.rating
		if (checked) {
			clears[level][2].total++
			for (var l = 1; l <= level; l++) {
				clears[l][2].totalIncludingHigher++
			}
			if (rowData.default_chart) {
				clears[level][2].distanceToLamp--
			}
			if (rowData.amethyst_required) {
				clears[level][2].distanceToAmethystLamp--
			}
		} else {
			clears[level][2].total--
			for (var l = 1; l <= level; l++) {
				clears[l][2].totalIncludingHigher--
			}
			if (rowData.default_chart) {
				clears[level][2].distanceToLamp++
			}
			if (rowData.amethyst_required) {
				clears[level][2].distanceToAmethystLamp++
			}
		}

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

	function updateTimeRange() {
		var rangeVal = currentFilters["time-range"]
		if (isNaN(rangeVal)) {
			minTimestamp = 0
			return
		}
		minTimestamp = loadTimestamp - (rangeVal * currentFilters["time-type"])
	}

	$('select.filter').change(function() {
		var value = parseInt($(this).val())
		currentFilters[this.id] = value

		if ($(this).hasClass("min")) {
			var maxId = $(this).data("max")
			if (currentFilters[maxId] < value) {
				currentFilters[maxId] = value
				$(`#${maxId}`).val(value)
			}
		} else if ($(this).hasClass("max")) {
			var minId = $(this).data("min")
			if (currentFilters[minId] > value) {
				currentFilters[minId] = value
				$(`#${minId}`).val(value)
			}
		}

		if (this.id === "time-type") {
			updateTimeRange()
		}

		redrawTable(true)
	})

	$("[type='checkbox'].filter").change(function() {
		currentFilters[this.id] = this.checked
		redrawTable(true)
	})

	$("[type='number'].filter").keyup(function() {
		currentFilters[this.id] = parseInt($(this).val())
		if (this.id === "time-range") {
			updateTimeRange()
		}
		redrawTable(true)
	})

	var requirementId = 0
	function nextReqId() {
		return requirementId++
	}

	function requirementTable() {
		var table = $('<table>', {class: 'requirements'})
		var colgroup = $('<colgroup>')
		colgroup.append($('<col>', {class: 'target-icon'}))
		table.append(colgroup)
		return table
	}

	function appendSection(table, section) {
		if (!section.length) {
			return
		}
		for (row of section) {
			table.append(row)
		}
		table.append($('<tr>', {class: 'blank-row'}))
	}

	function requirementRow(text, goalId, checkable = false) {
		var targetCell = $('<td>', {class: 'target-cell', 'data-goal-id': goalId})
		var targetIcon = $('<span>', {class: 'target-icon'})
		targetIcon.append('🎯')
		targetCell.append(targetIcon)

		var td = $('<td>')
		var reqId = `req-${nextReqId()}`

		if (checkable) {
			var checkbox = $('<input>', {type: 'checkbox', id: reqId})
			td.append(checkbox)
		}

		var description = $('<label>', {class: 'req-description', for: reqId})
		description.text(text)
		td.append(description)

		var togo = $('<span>', {class: 'togo'})
		td.append(togo)

		var tr = $('<tr>')
		tr.append(targetCell)
		tr.append(td)
		return tr
	}

	whiteVersion = $('#white-version').data('json')
	rankRequirements = $('#rank-requirements').data('json')
	requirementTargets = $('#requirement-targets').data('json')
	var initialSelectedRank = $('#selected-rank').data('x')
	for (var index in rankRequirements) {
		var rank = rankRequirements[index]
		rank.option = $('<option>', {
			value: index,
			text: rank.name,
		})
		$('#rank-select').append(rank.option)

		rank.container = $('<div>')
		rank.container.hide()

		rank.main = requirementTable()
		rank.subHeader = $('<p>')
		rank.subHeader.text('Substitutions:')
		rank.subs = requirementTable()

		var mainContent = false
		var subsContent = false
		for (let level = 1; level < 20; level++) {
			if (!(level in rank.requirements)) {
				continue
			}
			var main = []
			var subs = []
			aAn = (level == 8 || level == 11 || level == 18) ? 'an' : 'a'
			for (let requirement of rank.requirements[level]) {
				var goalId = requirement.goal_id
				switch(requirement.kind) {
				case 'scores':
					if (requirement.qty > 0) {
						var scoreText = (requirement.threshold == 990000) ? 'AAA' : (requirement.threshold/1000 + 'k+')
						var qtyText = requirement.qty == 1 ? aAn : requirement.qty
						var plural = requirement.qty == 1 ? '' : 's'
						var orHigher = requirement.or_higher ? '+' : ''
						requirement.row = requirementRow(`${scoreText} ${qtyText} ${level}${plural}${orHigher}`, goalId)
					} else {
						var exceptions = requirement.qty == 0 ? '' : ` (${-requirement.qty} exceptions)`
						var lachendy = level == 19 ? (whiteVersion > 18 ? ' (ex. Lachryma《Re:Queen’M》 & ENDYMION)' : ' (ex. ENDYMION)') : ''
						requirement.row = requirementRow(`All ${level}s over ${requirement.threshold/1000}k${exceptions}${lachendy}`, goalId)
					}
					break
				case 'clears':
					if (requirement.qty == 0) {
						requirement.row = requirementRow(`${level} ${lampTypes[requirement.threshold]} Lamp`, goalId)
					} else {
						var mandatory = requirement.mandatory ? '[MANDATORY] ' : ''
						var qtyText = requirement.qty == 1 ? aAn : requirement.qty
						var plural = requirement.qty == 1 ? '' : 's'
						var orHigher = requirement.or_higher ? '+' : ''
						requirement.row = requirementRow(`${mandatory}${clearTypes[requirement.threshold]} ${qtyText} ${level}${plural}${orHigher}`, goalId)
					}
					break
				case 'consecutives':
					requirement.row = requirementRow(`Clear ${requirement.qty} ${level}s in a row`, goalId, true)
					requirement.row.find('input').change(function() {
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
					break
				case 'averages':
					requirement.row = requirementRow(`${requirement.threshold.toLocaleString()} ${level}s average`, goalId)
					break
				default:
					requirement.row = requirementRow(JSON.stringify(requirement), goalId)
				}
				section = (requirement.sub ? subs : main)
				section.push(requirement.row)
			}
			if (level == 19 && 'lachendy' in rank.requirements) {
				var lachryma = whiteVersion > 18 ? "Lachryma《Re:Queen’M》 challenge and " : ""
				for (var requirement of rank.requirements.lachendy) {
					requirement.row = requirementRow(`${requirement.threshold/1000}k+ on ${lachryma}ENDYMION challenge`, requirement.goal_id)
					section = (requirement.sub ? subs : main)
					section.push(requirement.row)
				}
			}
			appendSection(rank.main, main)
			appendSection(rank.subs, subs)
		}

		if ('calories' in rank.requirements) {
			var main = []
			var subs = []
			for (let requirement of rank.requirements.calories) {
				requirement.row = requirementRow(`Burn ${requirement.threshold} calories in one day`, requirement.goal_id, true)

				requirement.row.find('input').change(function() {
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
				section = (requirement.sub ? subs : main)
				section.push(requirement.row)
			}
			appendSection(rank.main, main)
			appendSection(rank.subs, subs)
		}

		if ('trials' in rank.requirements) {
			var main = []
			var subs = []
			for (let requirement of rank.requirements.trials) {
				var plural = requirement.qty == 1 ? '' : 's'
				requirement.row = requirementRow(`Earn ${trialClears[requirement.threshold]} or above on ${requirement.qty} Trial${plural}`, requirement.goal_id, true)

				requirement.row.find('input').change(function() {
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
				});
				
				section = (requirement.sub ? subs : main)
				section.push(requirement.row)
			}
			appendSection(rank.main, main)
			appendSection(rank.subs, subs)
		}

		if ('mfc_points' in rank.requirements) {
			var main = []
			var subs = []
			for (var requirement of rank.requirements.mfc_points) {
				requirement.row = requirementRow('', requirement.goal_id)
				
				var label = $('<a>', {target: '_blank', href: 'https://life4ddr.com/rank-requirements/#mfcpoints'})
				label.text('MFC Points')
				var description = requirement.row.find('.req-description')
				description.append(label)
				description.append(`: ${requirement.threshold}`);

				section = (requirement.sub ? subs : main)
				section.push(requirement.row)
			}
			appendSection(rank.main, main)
			appendSection(rank.subs, subs)
		}

		rank.main.children().last().remove()
		rank.container.append(rank.main)
		if (rank.subs.find('td').index() >= 0) {
			rank.subs.children().last().remove()
			rank.container.append(rank.subHeader)
			rank.container.append(rank.subs)
		}

		$('#rank-details').append(rank.container)
	}
	selectedRank = rankRequirements[initialSelectedRank]
	$('#rank-select').val(initialSelectedRank)
	selectedRank.container.show()

	$('.requirements').on('click', '.targetable', function() {
		goalId = $(this).data('goal-id')
		var postData = JSON.stringify({'goal_id': goalId, 'version_id': whiteVersion})
		$.ajax({
			url: $(this).next().hasClass('targeted') ? '/scorebrowser/untarget_requirement' : '/scorebrowser/target_requirement',
			type: 'POST',
			data: postData,
			success: function(response) {
				requirementTargets = response.targets
				evaluateRanks()
			}
		})
	})

	function selectRank() {
		selectedRank.container.hide()

		rankIndex = $('#rank-select').find(':selected').val()
		rank = rankRequirements[rankIndex]
		selectedRank = rank
		rank.container.show()

		redrawTable() // might change what "required songs" means

		$.ajax({
			url: '/scorebrowser/set_selected_rank',
			type: 'POST',
			data: JSON.stringify({'rank': rankIndex})
		})
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
				total: 0,
				totalIncludingHigher: 0,
				distanceToLamp: 0,
				distanceToAmethystLamp: 0,
			}
		}
	}

	scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
		d = this.data()
		if (d.game_version.id > whiteVersion) {
			return
		}

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

		if (d.amethyst_required) {
			for (var clearType = d.clear_type + 1; clearType <= 6; clearType++) {
				clears[d.difficulty.rating][clearType].distanceToAmethystLamp++
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

	$("#rank-details").on('click', '.need-link', function() {
		setFilters(Object.assign({}, baseFilters, $(this).data('filters')))
	})

	function qtyAboveThreshold(scoresList, threshold) {
		var metIndex = scoresList.findIndex((score) => score >= threshold)
		if (metIndex == -1) {
			return 0
		}
		return scoresList.length - metIndex
	}

	function styleReq(requirement, distance, filters = undefined, additional = "", additionalFilters = undefined) {
		var togo = requirement.row.find('.togo')
		togo.empty()

		var checkbox = requirement.row.find('input')
		var label = requirement.row.find('label')
		var targetCell = requirement.row.find('.target-cell')

		if (!additional && (distance <= 0) && (distance != null)) {
			label.removeClass('unmet')
			label.addClass('met')
			targetCell.removeClass('targetable')
			checkbox.prop('checked', true)
			requirement.met = true
			return
		}

		var needs = []
		if (distance > 0) {
			var moreText = `${distance.toLocaleString()} more`
			if (filters) {
				var needLink = $('<button>', {class: 'need-link'})
				needLink.data('filters', filters)
				needLink.append(moreText)
				needs.push(needLink)
			} else {
				needs.push(moreText)
			}
		}
		if (additional) {
			if (needs.length) {
				needs.push('and')
			}
			var needLink = $('<button>', {class: 'need-link'})
			needLink.data('filters', additionalFilters)
			needLink.append(additional)
			needs.push(needLink)
		}
		if (needs.length) {
			togo.append(' (need')
			for (need of needs) {
				togo.append(' ')
				togo.append(need)
			}
			togo.append(')')
		}

		label.removeClass('met')
		label.addClass('unmet')
		targetCell.addClass('targetable')
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
			rank.amethyst = amethyst

			for (var level = 1; level < 20; level++) {
				if (!(level in rank.requirements)) {
					continue
				}
				var levelFilters = {"level-min": level, "level-max": level}
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
								styleReq(requirement, requirement.qty - qtyMet, {"max-score": requirement.threshold, "level-min": level})
							}
						} else {
							var needFilters = Object.assign({"max-score": requirement.threshold}, levelFilters)
							if (requirement.qty <= 0) {
								var segment = amethyst ? 'amethyst_required' : 'default'
								var qtyMet = qtyAboveThreshold(scoresByLevel[level][segment], requirement.threshold)
								//var clearLamp = clears[level][1].distanceToLamp == 0 ? "" : "clear lamp"
								var qtyUnmet = scoresByLevel[level][segment].length - qtyMet
								if (clears[level][1].distanceToLamp == 0) {
									styleReq(requirement, qtyUnmet + requirement.qty, needFilters)
								} else {
									var clearFilters = Object.assign({"clear-type-min": -1, "clear-type-max": 0}, levelFilters)
									styleReq(requirement, qtyUnmet + requirement.qty, needFilters, "clear lamp", clearFilters)
								}
							} else {
								var qtyMet = qtyAboveThreshold(scoresByLevel[level].all, requirement.threshold)
								styleReq(requirement, requirement.qty - qtyMet, needFilters)
							}
						}
						break;
					case 'clears':
						var needFilters = Object.assign({"clear-type-min": -1, "clear-type-max": requirement.threshold - 1}, levelFilters)
						if (requirement.qty == 0) {
							distanceToLamp = clears[level][requirement.threshold][amethyst ? 'distanceToAmethystLamp' : 'distanceToLamp']
							styleReq(requirement, distanceToLamp, needFilters)
						} else {
							total = clears[level][requirement.threshold][requirement.or_higher ? 'totalIncludingHigher' : 'total']
							styleReq(requirement, requirement.qty - total, needFilters)
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
			var attainedRank = true
			if (remainingOptional > 0) {
				attainedRank = false
				if (remainingMandatory > 0) {
					remainingText = `need ${remainingMandatory} mandatory, plus ${remainingOptional} more`
				} else {
					remainingText = `need ${remainingOptional} more`
				}
			} else if (remainingMandatory > 0) {
				attainedRank = false
				remainingText = `need ${remainingMandatory} mandatory`
			} else if (remainingOptional < 0) {
				remainingText = `attained, +${-remainingOptional} extra`
			}

			if (!attainedRank) {
				var numTargets = 0
				for (let targetCell of rank.main.find('.target-cell')) {
					targetCell = $(targetCell)
					description = targetCell.next().find('.req-description')
					if (requirementTargets.includes(targetCell.data('goal-id')) && description.hasClass('unmet')) {
						targetCell.next().addClass('targeted')
						numTargets++
					} else {
						targetCell.next().removeClass('targeted')
					}
				}
				for (let targetCell of rank.subs.find('.target-cell')) {
					targetCell = $(targetCell)
					description = targetCell.next().find('.req-description')
					if (requirementTargets.includes($(targetCell).data('goal-id')) && description.hasClass('unmet')) {
						targetCell.next().addClass('targeted')
						numTargets++
					} else {
						targetCell.next().removeClass('targeted')
					}
				}
				if (numTargets) {
					remainingText += `, ${numTargets} targeted`
				}
			}

			var rankOption = $(`#rank-select option[value=${index}]`)
			rankOption.text(`${rank.name} (${remainingText})`)
		}
	}
	evaluateRanks()
})