$(document).ready(function () {
	function updateDerivedTargets() {
		primaryScore = $('#target-score').val()
		if (!$.isNumeric(primaryScore)) {
			return
		}
		primaryScore = parseFloat(primaryScore)

		primarySpice = $('#benchmark-select').find(':selected').attr('data-spice')
		targetQuality = primarySpice - Math.log2((1000001 - primaryScore)/1000000)
		$('#quality').text(targetQuality.toLocaleString('en-US'))

		$('#derived-targets').find('span').each(function() {
			spice = parseFloat($(this).attr('data-spice'))
			target = 1000001 - (15625 * Math.pow(2, 6 + spice - targetQuality))
			target = Math.ceil(target/10) * 10
			// todo- clamp to 0 - 1000000
			$(this).text(target.toLocaleString('en-US'))
		})
	}

	$('.select-filter').change(function() {
		updateDerivedTargets()
	})

	$('.text-filter').keyup(function() {
		updateDerivedTargets()
	})

	updateDerivedTargets()
})