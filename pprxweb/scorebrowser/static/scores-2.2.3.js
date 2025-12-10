// scores.js

var csrfToken = null

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
	'FC',
	'GFC',
	'PFC',
	'MFC',
]

const clearTypeNumbers = {
	'fail': 0,
	'clear': 1,
	'life4': 2,
	'good': 3,
	'great': 4,
	'perfect': 5,
	'marvelous': 6,
}

const lampTypes = [
	'Fail',
	'Clear',
	'Red',
	'Blue',
	'Green',
	'Gold',
	'White',
]

const trialClears = [
	"",
	"silver",
	"gold",
	"platinum",
	"diamond",
	"cobalt",
	"pearl",
	"topaz",
	"amethyst",
	"emerald",
	"onyx",
	"ruby",
]

const trialNumbers = {
	"silver": 1,
	"gold": 2,
	"platinum": 3,
	"diamond": 4,
	"cobalt": 5,
	"pearl": 6,
	"topaz": 7,
	"amethyst": 8,
	"emerald": 9,
	"onyx": 10,
	"ruby": 11,
}

const mfcPoints = [0,  0.1,  0.25,  0.25,  0.5,  0.5,  0.5,   1,   1,   1,  1.5,   2,   4,   6,   8,  15,  25,  25,  25,  25]
const sdpPoints = [0, 0.01, 0.025, 0.025, 0.05, 0.05, 0.05, 0.1, 0.1, 0.1, 0.15, 0.2, 0.4, 0.6, 0.8, 1.5, 2.5, 2.5, 2.5, 2.5]

var romanizeTitles = false

const MAX_VERSION = 20
const classicEra = [1, 13]
const whiteEra = [14, 16]
const goldEra = [17, MAX_VERSION]
const eras = {
	"Classic era": {versionRange: classicEra, top30: []},
	"White era": {versionRange: whiteEra, top30: []},
	"Gold era": {versionRange: goldEra, top30: []},
}
let totalFlarePoints = 0
let flareTargetFloor = 0
let versionFlareTargets = false

const baseFlarePoints = [undefined, 145, 155, 170, 185, 205, 230, 225, 290, 335, 400, 465, 510, 545, 575, 600, 620, 635, 650, 665]
const flareSymbols = ["—", "I", "II", "III", "IV", "V", "VI", "VII", "VIII", "IX", "EX"]
const flareRanks = {
	"None+": 500,
	"None++": 1000,
	"None+++": 1500,
	"Mercury": 2000,
	"Mercury+": 3000,
	"Mercury++": 4000,
	"Mercury+++": 5000,
	"Venus": 6000,
	"Venus+": 7000,
	"Venus++": 8000,
	"Venus+++": 9000,
	"Earth": 10000,
	"Earth+": 11500,
	"Earth++": 13000,
	"Earth+++": 14500,
	"Mars": 16000,
	"Mars+": 18000,
	"Mars++": 20000,
	"Mars+++": 22000,
	"Jupiter": 24000,
	"Jupiter+": 26500,
	"Jupiter++": 29000,
	"Jupiter+++": 31500,
	"Saturn": 34000,
	"Saturn+": 36750,
	"Saturn++": 39500,
	"Saturn+++": 42250,
	"Uranus": 45000,
	"Uranus+": 48750,
	"Uranus++": 52500,
	"Uranus+++": 56250,
	"Neptune": 60000,
	"Neptune+": 63750,
	"Neptune++": 67500,
	"Neptune+++": 71250,
	"Sun": 75000,
	"Sun+": 78750,
	"Sun++": 82500,
	"Sun+++": 86250,
	"WORLD": 90000,
}

var currentFilters = {}
var defaultFilters = {}
var requirementFilters = {}
var userHidChartIds = []
var minTimestamp = 0

var metGoals = 0
var totalGoals = 0

var allCharts = null
var selectedRank = null
var requirementTargets = null
var averages = []
var clears = []
var scoresByLevel = []
var maPointsEarned = 0
var checkedRequirements = null
var whiteVersion = 0
var allowAjax = true

function escapeHtml(unsafe) {
	return unsafe
		.replace(/&/g, "&amp;")
		.replace(/</g, "&lt;")
		.replace(/>/g, "&gt;")
		.replace(/"/g, "&quot;")
		.replace(/'/g, "&#039;");
}

$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	if (userHidChartIds.includes(parseInt(data[17]))) {
		return false
	}

	if (minTimestamp != 0) {
		if (currentFilters["older-newer"] == 1) {
			if (parseInt(data[11]) < minTimestamp) {
				return false
			}
		} else {
			if (parseInt(data[11]) > minTimestamp) {
				return false
			}
		}
	}

	visibility = parseInt(data[currentFilters["cabinet-select"]])
	if (visibility === 3) {
		if (data[28] === "true") {
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
	if ((visibility === 1) && !currentFilters["show-extra-exclusive"]) {
		return false
	}

	const hidden_chart = data[30] === "true"
	if (hidden_chart && !currentFilters["show-new"]) {
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
	song_levels = allCharts[data[22]]
	for (var i = (currentFilters["song-beginner"] ? 0 : 1); i < song_levels.length; i++) {
		if ((song_levels[i] >= currentFilters["song-level-min"]) && (song_levels[i] <= currentFilters["song-level-max"])) {
			song_level_met = true
			break
		}
	}
	if (!song_level_met) {
		return false
	}

	if (currentFilters["for-requirement"] && (data[31] === "false")) {
		return false
	}

	const is_spiced = data[16] === "true"
	if (currentFilters["spice-status"] == 1) {
		if (data[29] !== "true") {
			return false
		}
	} else if (currentFilters["spice-status"] == 2) {
		if (!is_spiced) {
			return false
		}
	}

	if (currentFilters["bookmarks-only"] && (data[25] === "false")) {
		return false
	}

	var score = parseFloat(data[9])
	if (score < currentFilters["min-score"]) {
		return false
	}
	if (score >= currentFilters["max-score"]) {
		return false
	}

	var clear_type = (score === 0) ? -1 : parseInt(data[24])
	// count flare VIII+ as at worst life4 clear when filtering
	if ((clear_type === 1) && (parseInt(data[12]) >= 8)) {
		clear_type = 2
	}
	if (clear_type < currentFilters["clear-type-min"]) {
		return false
	}
	if (clear_type > currentFilters["clear-type-max"]) {
		return false
	}

	var flare_target = parseInt(data[13])
	if ((flare_target === 0) && currentFilters["flare-helps-only"]) {
		return false
	}

	if (is_spiced) {
		totalGoals++
		var goal_met = (score >= parseFloat(data[14])) && (score > 0)
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

function getCookie(name) {
	let cookieValue = null;
	if (document.cookie && document.cookie !== '') {
		const cookies = document.cookie.split(';');
		for (let i = 0; i < cookies.length; i++) {
			const cookie = cookies[i].trim();
			// Does this cookie string begin with the name we want?
			if (cookie.substring(0, name.length + 1) === (name + '=')) {
				cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
				break;
			}
		}
	}
	return cookieValue;
}

$(document).ready(function () {
	const loadTimestamp = Math.floor(Date.now()/1000)

	$("button.vis-button").click(function() {
		visibilityId = $(this).data('vis')
		$.ajax({
			url: '/scorebrowser/set_profile_visibility',
			type: 'POST',
			data: new URLSearchParams([
				['visibility', visibilityId],
				['csrfmiddlewaretoken', csrfToken],
			]).toString()
		}).done(function(data) {
			$("dialog.one-time-dialog").removeAttr("open")
		})
	})

	allowAjax = ($("#allow-ajax").data('x') === "True")

	whiteVersion = $('#white-version').data('json')
	if (whiteVersion > 18) {
		clearTypeIcons[1] = '<img src="/static/pass.png" class="inline-image">'
		clearTypeIcons[2] = '<img src="/static/hard.png" class="inline-image">'
	} else if (!allowAjax) {
		clearTypeIcons[2] = ' ❗'
	}

	reqsPromise = fetch("/static/ranks-2.2.3.json").then(x => x.json())

	csrfToken = getCookie('csrftoken')
	romanizeTitles = $("#romanize-titles").data("x") === "True"

	$("[type='checkbox'].filter").each(function() {
		currentFilters[this.id] = $(this).data('default')
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = currentFilters[this.id]
		}
	})
	$("[type='number'].filter").each(function() {
		currentFilters[this.id] = $(this).data('default')
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = currentFilters[this.id]
		}
	})
	$("select.filter").each(function() {
		currentFilters[this.id] = $(this).data('default')
		if (!$(this).hasClass("persistent")) {
			defaultFilters[this.id] = currentFilters[this.id]
		}
	})
	Object.assign(requirementFilters, currentFilters)
	requirementFilters['for-requirement'] = true

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

	checkedRequirements = $('#life4-reqs').data('json')
	allCharts = $('#all-charts').data('json')
	var scores = $('#jsonData').data('json')
	var scoresTable = $('#scores').DataTable({
		data: scores,
		responsive: true,
		deferRender: true,
		columns: [
			{ data: '0', visible: false }, // white visibility
			{ data: '1', visible: false }, // gold visibility
			{ data: '2', visible: false }, // gold-only visibility
			// 3: (buttons)
			{
				data: null,
				name: 'tools',
				orderable: false,
				searchable: false,
				className: 'buttons-cell',
				width: '1px',
				render: function(data, type, row, meta) {
					if (type !== "display") {
						return 0
					}
					var hideButton = '<button class="hide-button">X</button>'
					if (!allowAjax) {
						return hideButton
					}

					var notesIcon = row.notes ? '📋' : '✏️'
					var notesButton = `<button class="notes-button">${notesIcon}</button>`
					var bookmarkFile = row.bookmarked ? 'saved.png' : 'save.png'
					var bookmarkButton = `<button class="bookmark-button"><img src="/static/${bookmarkFile}" class="inline-image"></button>`
					return `${hideButton} ${notesButton} ${bookmarkButton}`
				}
			},
			// 4:
			{
				data: 'game_version',
				name: 'version',
				title: 'Version',
				render: { display: 'name', sort: 'id', type: 'id', filter: 'id' },
			},
			// 5:
			{ 
				data: 'song_name',
				title: 'Song',
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
				className: 'border-left',
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
				name: 'spice',
				title: 'Spice',
				type: 'nonzero-number',
				render: DataTable.render.number('', '.', 2),
			},
			// 9:
			{
				data: 'score',
				title: 'Score',
				className: 'border-left',
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
				name: 'quality', 
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
				name: 'age',
				title: 'Age',
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
				data: 'flare_gauge',
				name: 'flare',
				title: 'Flare',
				className: 'border-left',
				render: function(data, type, row, meta) {
					if (type === "filter") {
						if (data === null || row.flare_points === undefined) {
							return -1
						}
						return data
					}
					if (data === null || row.flare_points === undefined) {
						return ''
					}
					if (type === "display") {
						var startSpan = row.manual_flare ? '<span class="manual-flare">' : ''
						var endSpan = row.manual_flare ? '</span>' : ''
						if (row.flare_counts) {
							return `${startSpan}${flareSymbols[data]} (${row.flare_points} pts)${endSpan}`
						}
						return `${startSpan}${flareSymbols[data]} <span class="reminder-text">(${row.flare_points} pts)</span>${endSpan}`
					}
					if (type === "sort") {
						return row.flare_points + (row.flare_counts ? 0.1 : 0)
					}
					return row.flare_points
				},
			},
			// 13:
			{
				data: null,
				name: 'flare_target',
				title: 'Flare Target',
				type: 'nonzero-number',
				render: function(data, type, row, meta) {
					if (!versionFlareTargets) {
						return 0
					}
					
					let eraTarget = versionFlareTargets[row.game_version.id]
					let targetPoints = Math.max(flareTargetFloor, eraTarget, row.flare_points + 1)
					let targetGauge = Math.ceil((((targetPoints / baseFlarePoints[row.rating]) - 1) / 0.06) - 0.0001)
					if (targetGauge > 10) {
						if (type === "display") {
							return '<span class="reminder-text">N/A</span>'
						}
						return 0
					}

					if (targetGauge < 0) {
						targetGauge = 0
					}
					targetPoints = Math.floor(baseFlarePoints[data.rating] * (1 + (0.06 * targetGauge)))
					let exceeding = Math.max(eraTarget - 1, row.flare_points)
					let increase = targetPoints - exceeding
					if (type === "display") {
						return `${flareSymbols[targetGauge]} (+${increase}) <button class="hit-flare" data-target="${targetGauge}">✅</button>`
					}
					return increase
				},
			},
			// 14:
			{
				data: 'goal',
				name: 'goal',
				title: 'Goal',
				className: 'border-left',
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
					if (allowAjax) {
						return `<button${styles}>${text}</button>`
					}
					return `<span${styles}>${text}</span>`
				},
			},
			// 15:
			{
				data: 'distance',
				name: 'distance',
				title: 'Dist.',
				type: 'nonzero-number',
				render: function(data, type, row, meta) {
					if (type === "sort" && data <= 0) {
						return 0
					}

					if (type === "sort" || type === "type" || type === "filter") {
						return data
					}

					if (data <= 0) {
						return ""
					}
					return "+" + data.toLocaleString()
				},
			},
			// 16:
			{ data: 'spiced', visible: false },
			// 17:
			{ data: 'chart_id', visible: false },
			// 18:
			{ data: 'rank', visible: false },
			// 19:
			{ data: 'alternate_title', visible: false },
			// 20:
			{ data: 'romanized_title', visible: false },
			// 21:
			{ data: 'searchable_title', visible: false },
			// 22:
			{ data: 'song_id', visible: false },
			// 23:
			{ data: 'notes', visible: false },
			// 24:
			{ data: 'clear_type', visible: false },
			// 25:
			{ data: 'bookmarked', visible: false },
			// 26:
			{ data: 'default_chart', visible: false },
			// 27:
			{ data: 'amethyst_required', visible: false },
			// 28:
			{ data: 'removed', visible: false },
			// 29:
			{ data: 'tracked', visible: false },
			// 30:
			{ data: 'hidden', visible: false },
			// 31:
			{ data: 'active_requirement', visible: false },
		],
		createdRow: function(row, data, index) {
			if (data['hidden']) {
				$(row).addClass('very-new')
				return
			}
			
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
		order: [[18, 'asc']],
	})
	setFilters()

	let hideableColumns = {
		'Tools/Version': ['tools:name', 'version:name'],
		'Spice/Quality': ['spice:name', 'quality:name'],
		'Age': ['age:name'],
		'Flare': ['flare:name', 'flare_target:name'],
		'Goals': ['goal:name', 'distance:name'],
	}

	for (groupName in hideableColumns) {
		let label = $("<label>")
		let toggle = $('<input type="checkbox" checked>')
		let thisGroupName = groupName
		toggle.change(function() {
			for (columnSelector of hideableColumns[thisGroupName]) {
				scoresTable.columns(columnSelector).visible(this.checked)
			}
		})
		label.append(` ${groupName}:`)
		label.append(toggle)
		$("#column-toggles").append(label)
	}

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

	function setFilters(newFilters = currentFilters) {
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

	$('#classic-era').click(function() {
		setFilters({"version-min": classicEra[0], "version-max": classicEra[1]})
	})
	$('#white-era').click(function() {
		setFilters({"version-min": whiteEra[0], "version-max": whiteEra[1]})
	})
	$('#gold-era').click(function() {
		setFilters({"version-min": goldEra[0], "version-max": goldEra[1]})
	})

	$('#all-unlocks').click(function() {
		setFilters({
			"show-extra-exclusive": true,
			"show-removed": true,
			"show-locked": true,
			"show-new": true,
		})
	})

	$('#default-only').click(function() {
		setFilters({
			"show-extra-exclusive": false,
			"show-removed": false,
			"show-locked": false,
			"show-new": false,
		})
	})

	

	function targetFlareRankChange(targetPoints) {
		$("#selected-flare").data("x", targetPoints)

		$.ajax({
			url: '/scorebrowser/set_selected_flare',
			type: 'POST',
			headers: {'X-CSRFToken': csrfToken},
			data: JSON.stringify({'flare': targetPoints})
		})

		if (targetPoints === 0) {
			flareTargetFloor = 0
			$("#min-flare-points").text("")
			return
		}

		if (totalFlarePoints >= targetPoints) {
			flareTargetFloor = 0
			$("#min-flare-points").text("Achieved!")
			return
		}

		let remainingPoints = targetPoints
		for (let i = 0; i < allFlarePoints.length; i++) {
			let progressiveFloor = Math.ceil(remainingPoints / (90 - i))
			if (allFlarePoints[i] < progressiveFloor) {
				flareTargetFloor = progressiveFloor
				break;
			}
			remainingPoints -= allFlarePoints[i]
		}
		$("#min-flare-points").text(`(Target Flare floor: ${flareTargetFloor} pts)`)
	}
	$("#target-flare-rank").change(function() {
		targetFlareRankChange(parseInt($(this).val()))
		scoresTable.rows().invalidate()
		redrawTable(true)

		if (flareTargetFloor === 0) {
			$("#flare-summary td").each(function() {
				$(this).removeClass("unmet").removeClass("met")
			})
		} else {
			$("#flare-summary td").each(function() {
				chartPoints = $(this).data("points")
				if (chartPoints < flareTargetFloor) {
					$(this).removeClass("met").addClass("unmet")
				} else {
					$(this).removeClass("unmet").addClass("met")
				}
			})
		}
	})

	let allFlarePoints
	function computeFlareSummary() {
		$('#flare-summary').empty()
		for (eraName in eras) {
			eras[eraName].top30.length = 0
		}

		scoresTable.rows().every(function() {
			let points = 0
			let data = this.data()
			if (data.flare_gauge !== null) {
				points = Math.floor(baseFlarePoints[data.rating] * (1 + (0.06 * data.flare_gauge)))
			}
			data.flare_points = points

			gameVersion = data.game_version.id
			for (eraName in eras) {
				let range = eras[eraName].versionRange
				if ((gameVersion < range[0]) || (gameVersion > range[1])) {
					continue
				}

				let top30 = eras[eraName].top30
				if (top30.length < 30) {
					top30.push(this)
					break
				}
				let thirtieth = top30.reduce((a, b) => a.data().flare_points < b.data().flare_points ? a : b)
				if (points > thirtieth.data().flare_points) {
					top30.push(this)
					eras[eraName].top30 = top30.filter(item => item !== thirtieth)
				}
				break
			}
		})

		versionFlareTargets = []
		totalFlarePoints = 0

		let flareHeader = $("<tr>")
		for (eraName in eras) {
			eras[eraName].top30.sort((a, b) => b.data().flare_points - a.data().flare_points)
			let target = eras[eraName].top30[29].data().flare_points + 1
			for (let version = eras[eraName].versionRange[0]; version <= eras[eraName].versionRange[1]; version++) {
				versionFlareTargets[version] = target
			}

			let eraPoints = 0
			for (row of eras[eraName].top30) {
				totalFlarePoints += row.data().flare_points
				eraPoints += row.data().flare_points
				row.data().flare_counts = true
			}

			flareHeader.append(`<th colspan=3 class="border-right border-left">${eraName} (${eraPoints.toLocaleString()} pts)</th>`)
		}
		$("#flare-summary").append(flareHeader)

		allFlarePoints = []
		for (let i = 0; i < 30; i++) {
			let flareRow = $("<tr>")
			for (eraName in eras) {
				if (eras[eraName].top30.length <= i) {
					flareRow.append('<td class="border-left"></td>')
					flareRow.append('<td></td>')
					flareRow.append('<td class="border-right"></td>')
					continue
				}

				let data = eras[eraName].top30[i].data()
				romanizeTitle = data.romanized_title && romanizeTitles
				displayTitle = romanizeTitle ? data.romanized_title : data.song_name.title
				displayClass = romanizeTitle ? ' romanized-title' : ""
				flareRow.append(`<td data-points="${data.flare_points}" class="border-left${displayClass}">${displayTitle}</td>`)
				flareRow.append(`<td data-points="${data.flare_points}">${data.difficulty.name} ${data.rating}</td>`)
				flareRow.append(`<td data-points="${data.flare_points}" class="border-right">${flareSymbols[data.flare_gauge]} (${data.flare_points})</td>`)
				allFlarePoints.push(data.flare_points)
			}
			$("#flare-summary").append(flareRow)
		}
		allFlarePoints.sort((a, b) => b - a)

		$("#total-flare-points").text(totalFlarePoints.toLocaleString())
		$("#target-flare-rank").empty()
		$("#target-flare-rank").append('<option value="0">Any improvement</option>')
		let currentFlareRank = "None"
		for (flareRank in flareRanks) {
			if (flareRanks[flareRank] <= totalFlarePoints) {
				currentFlareRank = flareRank
				continue
			}
			$("#target-flare-rank").append(`<option value="${flareRanks[flareRank]}">${flareRank}</option>`)
		}

		let selectedFlare = $('#selected-flare').data('x')
		if ($(`#target-flare-rank option[value='${selectedFlare}']`).length === 0) {
			selectedFlare = 0
		}
		$("#target-flare-rank").val(selectedFlare).change()
		
		$("#flare-rank").text(currentFlareRank)
	}
	computeFlareSummary()

	var spiceHeader = scoresTable.column(8).header()
	$(spiceHeader).addClass('tooltip').attr('title', "How hard a chart is to score, relative to all other charts (not just of the same rating).")

	var qualityHeader = scoresTable.column(10).header()
	$(qualityHeader).addClass('tooltip').attr('title', 'How good your score is, relative to your other scores on other songs, based on similarly skilled players\' scores.')

	function applyRowClasses(table) {
		var cab = currentFilters["cabinet-select"]
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			visibility = parseInt(this.data()[cab])
			if (visibility === 1) {
				$(this.node()).addClass('extra-exclusive').removeClass('locked-chart')                
			} else if (visibility === 2) {
				$(this.node()).removeClass('extra-exclusive').addClass('locked-chart')                
			} else {
				$(this.node()).removeClass('extra-exclusive').removeClass('locked-chart')                
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
		newGoal = Math.min(1000000, Math.max(1, newGoal)) - 1

		$.ajax({
			url: '/scorebrowser/set_goal',
			type: 'POST',
			headers: {'X-CSRFToken': csrfToken},
			data: JSON.stringify({'chart_id': row.chart_id, 'target_score': newGoal}),
			success: function(response) {
				scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
					d = this.data()
					if (!d.spiced) {
						return
					}
					d.goal = response[d.chart_id]
					if (d.goal) {
						d.distance = d.goal - d.score
					} else {
						d.distance = 0
					}
					this.invalidate()
				})
			}
		})
		redrawTable(true)
	})

	$('#scores').on('click', 'button.hit-flare', function() {
		row = scoresTable.row($(this).parents('tr'))
		targetGauge = $(this).data("target")
		row.data().flare_gauge = targetGauge
		row.data().manual_flare = true
		row.invalidate()
		computeFlareSummary()
		redrawTable(true)

		$("#manual-flare-explanation").show()
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
					headers: {'X-CSRFToken': csrfToken},
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
			headers: {'X-CSRFToken': csrfToken},
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
			headers: {'X-CSRFToken': csrfToken},
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

	function requirementRow(html, goalId, checkable = false) {
		var targetCell = $('<td>', {class: 'target-cell', 'data-goal-id': goalId})
		// var targetIcon = $('<span>', {class: 'target-icon'})
		// targetIcon.append('🎯')
		// targetCell.append(targetIcon)

		var td = $('<td>', {class: 'desc-cell'})
		var reqId = `req-${nextReqId()}`

		var description
		if (checkable) {
			var checkbox = $('<input>', {type: 'checkbox', id: reqId})
			if (!allowAjax) {
				checkbox.attr("disabled", true)
			}
			td.append(checkbox)
			description = $('<label>', {class: 'req-description', for: reqId})
		} else {
			description = $('<span>', {class: 'req-description'})
		}

		for (element of html) {
			description.append(element)
		}
		td.append(description)

		var togo = $('<span>', {class: 'togo'})
		td.append(togo)

		var tr = $('<tr>')
		tr.append(targetCell)
		tr.append(td)
		return tr
	}

	function prettyName(ugly) {
		// "copper4" -> "Copper IV"
		// cheating and using flareSymbols for the roman numerals since 1-5 are identical
		return ugly[0].toUpperCase() + ugly.slice(1, -1) + " " + flareSymbols[ugly.slice(-1) - '0']
	}

	function fillSection(table, section) {
		for (level of [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 'calories', 'set', 'trial', 'ma_points']) {
			if (level in section) {
				for (row of section[level]) {
					table.append(row)
				}
				table.append($('<tr>', {class: 'blank-row'}))
			}
		}
		table.children().last().remove()
	}

	function scoreK(score) {
		return (score/1000) + 'k'
	}

	function scoreName(score) {
		switch (score) {
		case 990000:
			return 'AAA'
		case 999910:
			return 'SDP'
		default:
			return scoreK(score)
		}
	}

	reqsPromise.then(ranks => {
		goalsById = {}
		goalsByLevel = []
		acceptsHigherLevel = []
		for (let level = 1; level <= 19; level++) {
			goalsByLevel[level] = []
			acceptsHigherLevel[level] = []
		}
		for (goal of ranks.goals) {
			goalsById[goal.id] = goal
			goal.elements = []
			if (goal.d) {
				goal.under = []
				goal.shadow = []
				goal.meets = []
				goalsByLevel[goal.d].push(goal)

				if (goal.higher_diff) {
					for (higher = goal.d+1; higher <= 19; higher++) {
						acceptsHigherLevel[higher].push(goal)
					}
				}

				if (goal.clear_type === 'sdp') {
					goal.score = 999910
					delete goal.clear_type
				}
			}
		}

		relevantGameVersion = (whiteVersion == MAX_VERSION) ? 'WORLD' : 'A20'
		sectionNames = ['mandatory_goal_ids', 'substitutions']
		checkableTypes = ['calories', 'set', 'trial']

		var rankList = ranks.game_versions[relevantGameVersion].rank_requirements
		for (var index in rankList) {
			var rank = rankList[index]
			rank.option = $('<option>', {
				value: index,
				text: prettyName(rank.rank),
			})
			$('#rank-select').append(rank.option)

			rank.container = $('<div>')
			rank.container.hide()

			rank.main = requirementTable()
			rank.subsHeader = $('<p>')
			rank.subsHeader.text('Substitutions:')
			rank.subs = requirementTable()

			sections = {}
			for (sectionName of sectionNames) {
				if (sectionName in rank) {
					section = {}
					sections[sectionName] = section
					for (goalId of rank[sectionName]) {
						let goal = goalsById[goalId]
						let goalHtml = []
						switch (goal.t) {
						case 'calories':
							goalHtml.push(`Burn ${goal.count} calories in one day`)
							break
						case 'ma_points':
							let maPointsLink = $('<a>', {target: '_blank', href: 'https://life4ddr.com/rank-requirements/#mapoints'})
							maPointsLink.text("MA Points")
							goalHtml.push(maPointsLink)
							goalHtml.push(`: ${goal.points}`)
							break
						case 'set':
							goalHtml.push(`Clear ${goal.diff_nums.length} ${goal.diff_nums[0]}+s in a row`)
							break
						case 'trial':
							var capitalizedRank = goal.rank[0].toUpperCase() + goal.rank.slice(1)
							var plural = (goal.count > 1) ? 's' : ''
							goalHtml.push(`Earn ${capitalizedRank} or better on ${goal.count} trial${plural}`)
							break
						case 'songs':
							var quantity = 'all'
							var orHigher = (goal.higher_diff) ? '+' : ''
							var plural = 's'
							if (goal.song_count) {
								if (goal.song_count === 1) {
									plural = ''
									quantity = ((goal.d === 8) || (goal.d === 11) || (goal.d === 18)) ? "an" : "a"
								} else {
									quantity = "" + goal.song_count
								}
							}

							var realClearType = null
							if (goal.clear_type) {
								realClearType = clearTypes[clearTypeNumbers[goal.clear_type]]
							} else if ((goal.song_count !== 1) || !goal.score) {
								realClearType = 'Clear'
							}
							if (goal.score === 999910) {
								realClearType = 'SDP'
							}
							if (realClearType) {
								var scoreText = ''
								var goalLink = $('<span>', {class: 'filter-link'})
								goalLink.data('goal-id', goalId)
								goalHtml.push(goalLink)
								var goalText
								if ((goal.score === 990000) && (realClearType === 'Clear')) {
									goalText = `AAA ${quantity} ${goal.d}${orHigher}${plural}`
								} else if (goal.score && (goal.score !== 999910)) {
									var scoreText = ` over ${scoreK(goal.score)}`
									goalText = `${realClearType} ${quantity} ${goal.d}${orHigher}${plural}${scoreText}`
								} else if (goal.average_score) {
									var scoreText = ` with a ${goal.average_score.toLocaleString()} average`
									goalText = `${realClearType} ${quantity} ${goal.d}${orHigher}${plural}`
									goalHtml.push(scoreText)
								} else {
									goalText = `${realClearType} ${quantity} ${goal.d}${orHigher}${plural}`
								}
								goalLink.text(goalText)
								goalLink.data('include-under', false)
								goalLink.data('include-shadow', false)
								goalLink.data('include-meets', true)
								goalLink.data('filter-text', `Show only charts satisfying ${goalText}`)
								goal.mainText = goalText
							} else {
								goal.mainText = `${scoreName(goal.score)} ${quantity} ${goal.d}${orHigher}${plural}`
								var goalLink = $('<span>', {class: 'filter-link'})
								goalLink.text(goal.mainText)
								goalLink.data('goal-id', goalId)
								goalLink.data('include-under', false)
								goalLink.data('include-shadow', false)
								goalLink.data('include-meets', true)
								goalLink.data('filter-text', `Show only charts satisfying ${goal.mainText}`)
								goalHtml.push(goalLink)
							}
							if (goal.exceptions) {
								var exceptionsPlural = goal.exceptions === 1 ? '' : 's'
								var scoreText = goal.exception_score ? ` and over ${scoreK(goal.exception_score)}` : ''
								goal.exceptionsText = `${goal.exceptions} exception${exceptionsPlural}, cleared${scoreText}`
								var exceptionsLink = $('<span>', {class: 'filter-link'})
								exceptionsLink.text(goal.exceptionsText)
								exceptionsLink.data('goal-id', goalId)
								goalHtml.push(' (')
								goalHtml.push(exceptionsLink)
								goalHtml.push(')')
								exceptionsLink.data('include-under', false)
								exceptionsLink.data('include-shadow', true)
								exceptionsLink.data('include-meets', false)
								exceptionsLink.data('filter-text', `Show only charts that could count as one of ${goal.exceptionsText}`)
							}
							break
						}

						subsectionName = (goal.t === 'songs') ? goal.d : goal.t
						if (!(subsectionName in section)) {
							section[subsectionName] = []
						}
						subsection = section[subsectionName]
						newElement = requirementRow(goalHtml, goalId, checkableTypes.includes(goal.t))
						if (allowAjax) {
							switch (goal.t) {
							case 'calories':
								newElement.find('input').change(function() {
									var postData = JSON.stringify({passed: this.checked, calories: goal.count})
									$.ajax({
										url: '/scorebrowser/set_calories',
										type: 'POST',
										headers: {'X-CSRFToken': csrfToken},
										data: postData,
										success: function(response) {
											checkedRequirements.calories = response.calories
											evaluateRanks()
										}
									})
								})
								break
							case 'set':
								newElement.find('input').change(function() {
									var postData = JSON.stringify({passed: this.checked, count: goal.diff_nums.length, level: goal.diff_nums[0]})
									$.ajax({
										url: '/scorebrowser/set_consecutives',
										type: 'POST',
										headers: {'X-CSRFToken': csrfToken},
										data: postData,
										success: function(response) {
											checkedRequirements.consecutives = response
											evaluateRanks()
										}
									})
								})
								break
							case 'trial':
								newElement.find('input').change(function() {
									var postData = JSON.stringify({passed: this.checked, count: goal.count, rank: trialNumbers[goal.rank]})
									$.ajax({
										url: '/scorebrowser/set_trials',
										type: 'POST',
										headers: {'X-CSRFToken': csrfToken},
										data: postData,
										success: function(response) {
											checkedRequirements.trials = response
											evaluateRanks()
										}
									})
								})
								break
							default:
								break
							}
						}
						goal.elements.push(newElement)
						subsection.push(newElement)
					}
				}
			}

			fillSection(rank.main, sections.mandatory_goal_ids)
			rank.container.append(rank.main)

			if (sections.substitutions) {
				fillSection(rank.subs, sections.substitutions)
				rank.container.append(rank.subsHeader)
				rank.container.append(rank.subs)
			}
			$('#rank-details').append(rank.container)
		}
		const initialSelectedRank = $('#selected-rank').data('x')
		selectedRank = rankList[initialSelectedRank]
		$('#rank-select').val(initialSelectedRank)
		selectedRank.container.show()

		// $('.requirements').on('click', '.targetable', function() {
		//     goalId = $(this).data('goal-id')
		//     var postData = JSON.stringify({'goal_id': goalId, 'version_id': whiteVersion})
		//     $.ajax({
		//         url: $(this).next().hasClass('targeted') ? '/scorebrowser/untarget_requirement' : '/scorebrowser/target_requirement',
		//         type: 'POST',
		//         headers: {'X-CSRFToken': csrfToken},
		//         data: postData,
		//         success: function(response) {
		//             requirementTargets = response.targets
		//             evaluateRanks()
		//         }
		//     })
		// })

		function showAverages(rank) {
			// segment = rank.amethyst ? 'amethyst' : 'default'
			// countSegment = rank.amethyst ? 'amethystCount' : 'defaultCount'
			// for (let level = 14; level < 19; level++) {
			// 	$(`#average-${level}`).text(Math.floor(averages[level][segment]).toLocaleString())
			// 	$(`#raise-${level}`).text(`+${(scoresByLevel[level][countSegment] * 10).toLocaleString()}`)
			// }
		}

		function selectRank() {
			selectedRank.container.hide()

			rankIndex = $('#rank-select').find(':selected').val()
			rank = rankList[rankIndex]
			selectedRank = rank
			rank.container.show()
			showAverages(rank)

			redrawTable() // might change what "required songs" means

			if (allowAjax) {
				$.ajax({
					url: '/scorebrowser/set_selected_rank',
					type: 'POST',
					headers: {'X-CSRFToken': csrfToken},
					data: JSON.stringify({'rank': rankIndex})
				})
			}
		}
		$('#rank-select').change(selectRank)

		sdps = new Array(20).fill(0)
		mfcs = new Array(20).fill(0)
		scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
			d = this.data()
			if (d.game_version.id > whiteVersion) {
				return
			}

			realClearType = d.clear_type
			if ((realClearType === 1) && (d.flare_gauge >= 8)) {
				realClearType = 2
			}

			for (goal of goalsByLevel[d.difficulty.rating]) {
				const scoreMet = !(goal.score) || (d.score >= goal.score)
				const countForAverage = !(goal.average_score) || (d.default_chart) || (d.score >= goal.average_score)
				let requiredClear = 1
				if (goal.clear_type) {
					requiredClear = clearTypeNumbers[goal.clear_type]
				} else if (goal.score && (goal.song_count === 1)) {
					requiredClear = 0
				}
				if (scoreMet && countForAverage && (realClearType >= requiredClear)) {
					goal.meets.push(this)
					continue
				}

				if ((!(goal.exception_score) || (d.score >= goal.exception_score)) && (realClearType >= 1)) {
					if ((goal.song_count) || (d.default_chart)) {
						goal.shadow.push(this)
					}
				} else {
					if (d.default_chart) {
						goal.under.push(this)
					}
				}
			}

			for (goal of acceptsHigherLevel[d.difficulty.rating]) {
				const scoreMet = (!(goal.score) || (d.score >= goal.score))
				const requiredClear = goal.clear_type ? clearTypeNumbers[goal.clear_type] : 1
				if (scoreMet && (realClearType >= requiredClear)) {
					goal.meets.push(this)
				}
			}

			if (realClearType == 6) {
				maPointsEarned += mfcPoints[d.difficulty.rating]
				mfcs[d.difficulty.rating] += 1
			} else if (d.score >= 999910) {
				maPointsEarned += sdpPoints[d.difficulty.rating]
				sdps[d.difficulty.rating] += 1
			}
		})

		$("#ma-points-display").text(+(maPointsEarned.toFixed(3)))
		$("#table-total-points").text(+(maPointsEarned.toFixed(3)))
		sdpPointsTotal = 0
		sdpsTotal = 0
		mfcPointsTotal = 0
		mfcsTotal = 0
		for (let i = 1; i < 20; i++) {
			let rowSdpPoints = sdps[i] * sdpPoints[i]
			if (sdps[i] > 0) {
				$(`#sdps-${i}`).text(sdps[i])
				$(`#sdp-points-${i}`).text(+(rowSdpPoints.toFixed(3)))
			}
			let rowMfcPoints = mfcs[i] * mfcPoints[i]
			if (mfcs[i] > 0) {
				$(`#mfcs-${i}`).text(mfcs[i])
				$(`#mfc-points-${i}`).text(+(rowMfcPoints.toFixed(3)))
			}

			if ((sdps[i] > 0) || (mfcs[i] > 0)) {
				$(`#row-points-${i}`).text(+((rowSdpPoints + rowMfcPoints).toFixed(3)))
			}

			sdpsTotal += sdps[i]
			sdpPointsTotal += rowSdpPoints
			mfcsTotal += mfcs[i]
			mfcPointsTotal += rowMfcPoints
		}
		$("#sdps-total-count").text(sdpsTotal)
		$("#mfcs-total-count").text(mfcsTotal)
		$("#sdps-total-points").text(+(sdpPointsTotal.toFixed(3)))
		$("#mfcs-total-points").text(+(mfcPointsTotal.toFixed(3)))

		$("#rank-details").on('click', '.filter-link', function() {
			$('#requirement-filter-label').show()
			var goal = goalsById[$(this).data('goal-id')]
			var includeUnder = $(this).data('include-under')
			var includeShadow = $(this).data('include-shadow')
			var includeMeets = $(this).data('include-meets')
			scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
				this.data().active_requirement = false
				this.invalidate()
			})
			if (includeUnder) {
				for (row of goal.under) {
					row.data().active_requirement = true
					row.invalidate()
				}
			}
			if (includeShadow) {
				for (row of goal.shadow) {
					row.data().active_requirement = true
					row.invalidate()
				}
			}
			if (includeMeets) {
				for (row of goal.meets) {
					row.data().active_requirement = true
					row.invalidate()
				}
			}

			$('#requirement-filter-text').text($(this).data('filter-text'))
			setFilters(requirementFilters)
		})

		requirementTargets = $('#requirement-targets').data('json')

		function evaluateRanks() {
			for (let goal of ranks.goals) {
				goal.shadowDistance = 0
				goal.totalScoreDistance = 0

				if (goal.t === 'songs') {
					exceptions = goal.exceptions || 0
					if (goal.song_count) {
						strictCount = goal.song_count - exceptions
						goal.distance = strictCount - goal.meets.length
						goal.shadowDistance = goal.song_count - goal.meets.length - goal.shadow.length
					} else {
						goal.distance = (goal.under.length + goal.shadow.length) - exceptions
						goal.shadowDistance = goal.under.length
						if (goal.average_score) {
							goal.under.sort((a, b) => (a.data().score - b.data().score))
							goal.shadow.sort((a, b) => (a.data().score - b.data().score))
							goal.meets.sort((a, b) => (a.data().score - b.data().score))
							var countForAverage = (goal.under.concat(goal.shadow).concat(goal.meets)).slice(goal.exceptions)
							var totalThreshold = goal.average_score * countForAverage.length
							var playerTotal = countForAverage.reduce(((acc, row) => acc + row.data().score), 0)
							goal.totalScoreDistance = totalThreshold - playerTotal
						}
					}
				} else {
					if (goal.t === 'calories') {
						goal.distance = goal.count - checkedRequirements.calories
					} else if (goal.t === 'set') {
						var attained = checkedRequirements.consecutives[goal.diff_nums.length]
						goal.distance = (attained >= goal.diff_nums[0]) ? 0 : 1
					} else if (goal.t === 'trial') {
						var attained = (goal.count === 1) ? checkedRequirements.trials.best : checkedRequirements.trials.second
						goal.distance = (attained >= trialNumbers[goal.rank]) ? 0 : 1
					} else if (goal.t === 'ma_points') {
						goal.distance = goal.points - maPointsEarned
					}
				}

				for (row of goal.elements) {
					let togo = row.find('.togo')
					togo.empty()

					let checkbox = row.find('input')
					let targetCell = row.find('.target-cell')

					if ((goal.distance <= 0) && (goal.shadowDistance <= 0) && (goal.totalScoreDistance <= 0)) {
						row.removeClass('unmet').addClass('met')
						targetCell.removeClass('targetable')
						checkbox.prop('checked', true)
						goal.met = true
						continue
					}

					goal.met = false
					row.removeClass('met').addClass('unmet')
					checkbox.prop('checked', false)
					if (checkableTypes.includes(goal.t)) {
						continue
					}

					togo.append(' (need ')
					if (goal.distance > 0) {
						let moreText = `${goal.distance.toLocaleString()} more`
						let moreLink = $("<span>", {class: 'filter-link'})
						moreLink.text(moreText)
						moreLink.data('goal-id', goal.id)
						moreLink.data('include-under', true)
						moreLink.data('include-shadow', true)
						moreLink.data('include-meets', false)
						moreLink.data('filter-text', `Show only songs not satisfying ${goal.mainText}`)
						togo.append(moreLink)
						togo.append('<span>, </span>')
					}
					if ((goal.shadowDistance > 0) && (goal.exceptions)) {
						let shadowText = `${goal.shadowDistance} shadow`
						let shadowLink = $("<span>", {class: 'filter-link'})
						shadowLink.text(shadowText)
						shadowLink.data('goal-id', goal.id)
						shadowLink.data('include-under', true)
						shadowLink.data('include-shadow', false)
						shadowLink.data('include-meets', false)
						shadowLink.data('filter-text', `Show only songs that can't count as one of ${goal.exceptionsText}`)
						togo.append(shadowLink)
						togo.append('<span>, </span>')
					}
					if (goal.totalScoreDistance > 0) {
						let moreText = `${goal.totalScoreDistance.toLocaleString()} more total points`
						togo.append(moreText)
						togo.append('<span>, </span>')
					}
					togo.children().last().remove()
					togo.append(')')
				}
			}

			for (var index in rankList) {
				var rank = rankList[index]
				var threshold = rank.requirements || rank.mandatory_goal_ids.length
				var met = 0
				for (goalId of rank.mandatory_goal_ids) {
					if (goalsById[goalId].met) {
						met++
					}
				}
				if (rank.substitutions) {
					for (goalId of rank.substitutions) {
						if (goalsById[goalId].met) {
							met++
						}
					}
				}

				var distance = threshold - met
				var remainingText = 'attained'
				if (distance > 0) {
					remainingText = `need ${distance} more`
					var numTargets = 0
					for (let targetCell of rank.main.find('.target-cell')) {
						targetCell = $(targetCell)
						if (requirementTargets.includes(targetCell.data('goal-id')) && targetCell.parent().hasClass('unmet')) {
							targetCell.next().addClass('targeted')
							numTargets++
						} else {
							targetCell.next().removeClass('targeted')
						}
					}
					for (let targetCell of rank.subs.find('.target-cell')) {
						targetCell = $(targetCell)
						if (requirementTargets.includes($(targetCell).data('goal-id')) && targetCell.parent().hasClass('unmet')) {
							targetCell.next().addClass('targeted')
							numTargets++
						} else {
							targetCell.next().removeClass('targeted')
						}
					}
					if (numTargets) {
						remainingText += `, ${numTargets} targeted`
					}
				} else if (distance < 0) {
					remainingText = `attained, +${-distance} extra`
				}

				var rankOption = $(`#rank-select option[value=${index}]`)
				rankOption.text(`${prettyName(rank.rank)} (${remainingText})`)
			}
		}

		evaluateRanks()
		showAverages(selectedRank)
	})
})
