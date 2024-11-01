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
	'Full Combo',
	'Great Full Combo',
	'PFC',
	'MFC',
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
var maPointsEarned = 0
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
	if (userHidChartIds.includes(parseInt(data[17]))) {
		return false
	}

	if (parseInt(data[11]) < minTimestamp) {
		return false
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

	if (currentFilters["hide-optional"]) {
		var optional = selectedRank.amethyst ? (data[27] === "false") : (data[26] === "false")
		if (optional) {
			return false
		}
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

	whiteVersion = $('#white-version').data('json')
	if (whiteVersion > 18) {
		clearTypeIcons[1] = '<img src="/static/pass.png" class="inline-image">'
		clearTypeIcons[2] = '<img src="/static/hard.png" class="inline-image">'
	}

	reqsPromise = fetch("/static/rank-requirements-1.2.26.json")
		.then(x => x.json())
		.then(json => rankRequirements = json[whiteVersion])

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
	Object.assign(baseFilters, currentFilters)
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
						if (row.flare_counts) {
							return `${flareSymbols[data]} (${row.flare_points} pts)`
						}
						return `${flareSymbols[data]} <span class="reminder-text">(${row.flare_points} pts)</span>`
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
					return `<button${styles}>${text}</button>`
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
		row.invalidate()
		computeFlareSummary()
		redrawTable(true)
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

		var td = $('<td>', {class: 'desc-cell'})
		var reqId = `req-${nextReqId()}`

		var description
		if (checkable) {
			var checkbox = $('<input>', {type: 'checkbox', id: reqId})
			td.append(checkbox)
			description = $('<label>', {class: 'req-description', for: reqId})
		} else {
			description = $('<span>', {class: 'req-description'})
		}

		description.html(text)
		td.append(description)

		var togo = $('<span>', {class: 'togo'})
		td.append(togo)

		var tr = $('<tr>')
		tr.append(targetCell)
		tr.append(td)
		return tr
	}

	reqsPromise.then(() => {
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
						var exceptions = ''
						if (requirement.exceptions > 0) {
							exceptions = ` (${requirement.exceptions} exceptions over ${requirement.exception_score/1000}k)`
						} else if (level === 19) {
							lach = whiteVersion > 18 ? 'Lachryma《Re:Queen’M》 & ' : ''
							exceptions = ` (ex. ${lach}ENDYMION over ${requirement.exception_score/1000}k)`
						}

						if (requirement.qty > 0) {
							var scoreText
							var sayClear = false
							if (requirement.threshold === 990000) {
								scoreText = 'AAA'
							} else if (requirement.threshold === 999910) {
								scoreText = 'SDP'
							} else {
								scoreText = requirement.threshold/1000 + 'k+'
								sayClear = true
							}

							var orHigher = requirement.or_higher ? '+' : ''
							if (requirement.qty === 1) {
								requirement.row = requirementRow(`${scoreText} ${aAn} ${level}${orHigher}`, goalId)
							} else if (sayClear) {
								requirement.row = requirementRow(`Clear ${requirement.qty} ${level}s over ${requirement.threshold/1000}k${exceptions}`, goalId)
							} else {
								requirement.row = requirementRow(`${scoreText} ${requirement.qty} ${level}s`, goalId)
							}
						} else {
							requirement.row = requirementRow(`All ${level}s over ${requirement.threshold/1000}k${exceptions}`, goalId)
						}
						break
					case 'clears':
						var ttStart = ''
						var ttEnd = ''
						if (requirement.threshold === 2) {
							ttStart = '<span class="tooltip" title="Since Flare VIII and higher fail you at four misses, rank evaluation counts a Flare VIII, IX, or EX clear as a LIFE4 clear.">'
							ttEnd = '</span>'
						}
						if (requirement.qty == 0) {
							requirement.row = requirementRow(`${level} ${ttStart}${lampTypes[requirement.threshold]} Lamp${ttEnd}`, goalId)
						} else {
							var mandatory = requirement.mandatory ? '[MANDATORY] ' : ''
							var qtyText = requirement.qty == 1 ? aAn : requirement.qty
							var plural = requirement.qty == 1 ? '' : 's'
							var orHigher = requirement.or_higher ? '+' : ''
							requirement.row = requirementRow(`${mandatory}${ttStart}${clearTypes[requirement.threshold]}${ttEnd} ${qtyText} ${level}${plural}${orHigher}`, goalId)
						}
						break
					case 'consecutives':
						requirement.row = requirementRow(`Clear ${requirement.qty} ${level}s in a row`, goalId, true)
						requirement.row.find('input').change(function() {
							var postData = JSON.stringify({'passed': this.checked, 'count': requirement.qty, 'level': level})
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
							headers: {'X-CSRFToken': csrfToken},
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
							headers: {'X-CSRFToken': csrfToken},
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

			if ('ma_points' in rank.requirements) {
				var main = []
				var subs = []
				for (var requirement of rank.requirements.ma_points) {
					requirement.row = requirementRow('', requirement.goal_id)
					
					var label = $('<a>', {target: '_blank', href: 'https://life4ddr.com/rank-requirements/#mapoints'})
					label.text('MA Points')
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
		//showAverages(selectedRank)

		$('.requirements').on('click', '.targetable', function() {
			goalId = $(this).data('goal-id')
			var postData = JSON.stringify({'goal_id': goalId, 'version_id': whiteVersion})
			$.ajax({
				url: $(this).next().hasClass('targeted') ? '/scorebrowser/untarget_requirement' : '/scorebrowser/target_requirement',
				type: 'POST',
				headers: {'X-CSRFToken': csrfToken},
				data: postData,
				success: function(response) {
					requirementTargets = response.targets
					evaluateRanks()
				}
			})
		})

		function showAverages(rank) {
			segment = rank.amethyst ? 'amethyst' : 'default'
			countSegment = rank.amethyst ? 'amethystCount' : 'defaultCount'
			for (let level = 14; level < 19; level++) {
				$(`#average-${level}`).text(Math.floor(averages[level][segment]).toLocaleString())
				$(`#raise-${level}`).text(`+${(scoresByLevel[level][countSegment] * 10).toLocaleString()}`)
			}
		}

		function selectRank() {
			selectedRank.container.hide()

			rankIndex = $('#rank-select').find(':selected').val()
			rank = rankRequirements[rankIndex]
			selectedRank = rank
			rank.container.show()
			showAverages(rank)

			redrawTable() // might change what "required songs" means

			$.ajax({
				url: '/scorebrowser/set_selected_rank',
				type: 'POST',
				headers: {'X-CSRFToken': csrfToken},
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
				'cleared': [],
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

		sdps = new Array(20).fill(0)
		mfcs = new Array(20).fill(0)
		scoresTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
			d = this.data()
			if (d.game_version.id > whiteVersion) {
				return
			}

			real_clear_type = d.clear_type
			if ((real_clear_type === 1) && (d.flare_gauge >= 8)) {
				real_clear_type = 2
			}

			if (isLachEndy(d)) {
				lachendyScores.push(d.score)
			} else {
				scoresByLevel[d.difficulty.rating].all.push(d.score)
				if (real_clear_type >= 1) {
					scoresByLevel[d.difficulty.rating].cleared.push(d.score)
				}

				var segment = d.default_chart ? 'default' : 'non_default'
				scoresByLevel[d.difficulty.rating][segment].push(d.score)

				segment = d.amethyst_required ? 'amethyst_required' : 'hard_unlocks'
				scoresByLevel[d.difficulty.rating][segment].push(d.score)
			}

			for (var clearType = 1; clearType <= real_clear_type; clearType++) {
				clears[d.difficulty.rating][clearType].total++
				for (var level = 1; level <= d.difficulty.rating; level++) {
					clears[level][clearType].totalIncludingHigher++
				}
			}

			if (d.default_chart) {
				for (var clearType = real_clear_type + 1; clearType <= 6; clearType++) {
					clears[d.difficulty.rating][clearType].distanceToLamp++
				}
			}

			if (d.amethyst_required) {
				for (var clearType = real_clear_type + 1; clearType <= 6; clearType++) {
					clears[d.difficulty.rating][clearType].distanceToAmethystLamp++
				}
			}

			if (real_clear_type == 6) {
				maPointsEarned += mfcPoints[d.difficulty.rating]
				mfcs[d.difficulty.rating] += 1
			} else if (d.score >= 999910) {
				maPointsEarned += sdpPoints[d.difficulty.rating]
				sdps[d.difficulty.rating] += 1
			}
		})

		for (var level = 1; level < 19; level++) {
			scoresByLevel[level].all.sort((a, b) => (a - b))
			scoresByLevel[level].cleared.sort((a, b) => (a - b))
			scoresByLevel[level].default.sort((a, b) => (a - b))
			scoresByLevel[level].non_default.sort((a, b) => (a - b))
			scoresByLevel[level].amethyst_required.sort((a, b) => (a - b))
			scoresByLevel[level].hard_unlocks.sort((a, b) => (a - b))

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
			scoresByLevel[level].defaultCount = defaultCount

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
			scoresByLevel[level].amethystCount = amethystCount

			averages[level] = {
				'default': defaultAverage,
				'amethyst': amethystAverage,
			}
		}
		lachendyScores.sort()

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

		function styleReq(requirement, distance, filters, moreParams = {}) {
			var togo = requirement.row.find('.togo')
			togo.empty()

			var checkbox = requirement.row.find('input')
			var targetCell = requirement.row.find('.target-cell')

			if (!moreParams.additional && !moreParams.shadow && (distance <= 0) && (distance != null)) {
				requirement.row.removeClass('unmet').addClass('met')
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
			if (moreParams.shadow) {
				if (needs.length) {
					needs.push(',')
				}
				var needLink = $('<button>', {class: 'need-link'})
				needLink.data('filters', moreParams.shadowFilters)
				needLink.append(`${moreParams.shadow} shadow`)
				needs.push(needLink)
			}
			if (moreParams.additional) {
				if (needs.length) {
					needs.push('and')
				}
				var needLink = $('<button>', {class: 'need-link'})
				needLink.data('filters', moreParams.additionalFilters)
				needLink.append(moreParams.additional)
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

			requirement.row.removeClass('met').addClass('unmet')
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
					var levelFilters = {"level-min": level, "level-max": level, "show-locked": true}
					var levelFiltersWithOptional = {"level-min": level, "level-max": level, "hide-optional": false}
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
								if (requirement.qty === 0) {
									var needFilters = Object.assign({"max-score": requirement.threshold}, levelFilters)
									var segment = amethyst ? 'amethyst_required' : 'default'
									var qtyMet = qtyAboveThreshold(scoresByLevel[level][segment], requirement.threshold)
									var qtyUnmet = scoresByLevel[level][segment].length - qtyMet
									var softUnmet = Math.max(qtyUnmet - requirement.exceptions, 0)
									var shadow = undefined
									var shadowFilters = undefined
									if (requirement.exceptions > 0) {
										let shadowMet = qtyAboveThreshold(scoresByLevel[level][segment], requirement.exception_score)
										let shadowUnmet = scoresByLevel[level][segment].length - shadowMet
										if (shadowUnmet > 0) {
											shadow = shadowUnmet
											shadowFilters = Object.assign({"max-score": requirement.exception_score}, levelFilters)
										}
									}
									if (clears[level][1].distanceToLamp == 0) {
										styleReq(requirement, softUnmet, needFilters, {shadow, shadowFilters})
									} else {
										var clearFilters = Object.assign({"clear-type-min": -1, "clear-type-max": 0}, levelFilters)
										styleReq(requirement, softUnmet, needFilters, {shadow, shadowFilters, additional: "clear lamp", additionalFilters: clearFilters})
									}
								} else {
									var needFilters = Object.assign({"max-score": requirement.threshold}, levelFiltersWithOptional)
									var segment = (requirement.qty === 1) ? 'all' : 'cleared'
									var qtyMet = qtyAboveThreshold(scoresByLevel[level][segment], requirement.threshold)
									var shadow = undefined
									var shadowFilters = undefined
									if (requirement.exceptions > 0) {
										var shadowMet = qtyAboveThreshold(scoresByLevel[level].cleared, requirement.exception_score)
										if (shadowMet < requirement.qty) {
											shadow = requirement.qty - shadowMet
											shadowFilters = Object.assign({"max-score": requirement.exception_score}, levelFiltersWithOptional)
										}
									}
									styleReq(requirement, requirement.qty - qtyMet - requirement.exceptions, needFilters, {shadow, shadowFilters})
								}
							}
							break;
						case 'clears':
							if (requirement.qty == 0) {
								var needFilters = Object.assign({"clear-type-min": -1, "clear-type-max": requirement.threshold - 1}, levelFilters)
								distanceToLamp = clears[level][requirement.threshold][amethyst ? 'distanceToAmethystLamp' : 'distanceToLamp']
								styleReq(requirement, distanceToLamp, needFilters)
							} else {
								var needFilters = Object.assign({"clear-type-min": -1, "clear-type-max": requirement.threshold - 1}, levelFiltersWithOptional)
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
							var countSegment = amethyst ? 'amethystCount' : 'defaultCount'
							var needFilters = Object.assign({"max-score": requirement.threshold}, levelFilters)
							var avgGap = requirement.threshold - averages[level][segment]
							styleReq(requirement, Math.ceil(avgGap * scoresByLevel[level][countSegment]), needFilters)
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

				if ('ma_points' in rank.requirements) {
					for (var requirement of rank.requirements.ma_points) {
						styleReq(requirement, requirement.threshold - maPointsEarned)
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
				}

				var rankOption = $(`#rank-select option[value=${index}]`)
				rankOption.text(`${rank.name} (${remainingText})`)
			}
		}
		evaluateRanks()
		showAverages(selectedRank)
	})
})