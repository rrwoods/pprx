$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	if (parseInt(data[parseInt($('#cabinet-select').find(':selected').val())]) === 2) {
		return false
	}

	var level_select = $('#level-select').find(':selected').val()
	if ((level_select != 0) && (level_select != data[6])) {
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
	var goal_met = score >= parseFloat(data[10])
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
			{ data: 'game_version', title: 'Version', render: { display: 'name', sort: 'id', type: 'id' } },
			{ data: 'song_name', title: 'Song' },
			{ data: 'difficulty', title: 'Difficulty', render: { display: 'name', sort: 'id', type: 'id' } },
			{ data: 'rating', title: 'Level' },
			{ data: 'spice', title: 'Spice', render: DataTable.render.number('', '.', 2), createdCell: function(td, cellData, rowData, row, col) {
				if (!rowData.quality) {
					$(td).addClass('autospice')
				}
			} },
			{ data: 'score', title: 'Score', render: DataTable.render.number(',', '.', 0) },
			{ data: 'quality', title: 'Quality', render: DataTable.render.number('', '.', 2) },
			{ data: 'goal', title: 'Goal', render: DataTable.render.number(',', '.', 0), createdCell: function(td, cellData, rowData, row, col) {
				if (!cellData) {
					return
				}
				if (rowData.score < cellData) {
					return
				}
				$(td).addClass('met-goal')
			} },
		],
		createdRow: function(row, data, index) {
			if (parseInt(data[$('#cabinet-select').find(':selected').val()]) === 1) {
				$(row).addClass('extra-exclusive')
			}
		},
	})

	function applyRowClasses(table) {
		table.rows().every(function(rowIdx, tableLoop, rowLoop) {
			if (parseInt(this.data()[$('#cabinet-select').find(':selected').val()]) === 1) {
				$(this.node()).addClass('extra-exclusive')
			} else {
				$(this.node()).removeClass('extra-exclusive')
			}
		})
	}

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