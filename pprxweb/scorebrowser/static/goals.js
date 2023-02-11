$.fn.dataTable.ext.search.push(function(settings, data, dataIndex) {
	var level_select = $('#level-select').find(':selected').val()
	if ((level_select != 0) && (level_select != data[4])) {
		return false
	}

	return true
})

$(document).ready(function () {
	var charts = JSON.parse($('#jsonData').attr('data-json'))
	var chartsTable = $('#charts').DataTable({
		data: charts,
		responsive: true,
		columns: [
			{ data: 'chart_id', visible: false },
			{ data: 'game_version', title: 'Version', render: { display: 'name', sort: 'id', type: 'id' } },
			{ data: 'song_name', title: 'Song' },
			{ data: 'difficulty', title: 'Difficulty', render: { display: 'name', sort: 'id', type: 'id' } },
			{ data: 'rating', title: 'Level' },
			{
				data: 'spice',
				title: 'Spice',
				render: DataTable.render.number('', '.', 2),
			},
			{
				data: 'goal',
				title: 'Goal',
				render: function(data, type, row, meta) {
					text = "None (Click to set)"
					if (data) {
						text = data.toLocaleString('en-US')
					}
					return '<button>'+text+'</button>'
				},
			},
		],
	})

	$('.select-filter').change(function() {
		chartsTable.draw()
	})

	$('#charts').on('click', 'button', function() {
		console.log(chartsTable.cell(this))
		row = chartsTable.row($(this).parents('tr')).data()
		newGoal = prompt("Set goal for " + row.song_name + " " + row.difficulty.name, row.goal || 0)
		if (!newGoal) {
			return
		}

		targetQuality = row.spice - Math.log2((1000001 - newGoal)/1000000)
		chartsTable.rows().every(function(rowIdx, tableLoop, rowLoop) {
			d = this.data()
			d.goal = 1000001 - 15625*Math.pow(2, 6 + d.spice - targetQuality)
			d.goal = Math.min(1000000, Math.max(0, Math.ceil(d.goal/10) * 10))
			this.invalidate()
		})
		chartsTable.draw()

		$.ajax({
			url: '/scorebrowser/set_goal',
			type: 'POST',
			data: JSON.stringify({'chart_id': row.chart_id, 'target_score': newGoal})
		})
	})
})