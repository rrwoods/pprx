$(document).ready(function () {
	function eventButton(button, check) {
		eventId = button.attr('data-event')
		$(`div[data-event='${eventId}']`).find(':checkbox').prop('checked', check)
		$.ajax({
			url: '/scorebrowser/update_unlock_event',
			type: 'POST',
			data: JSON.stringify({'event_id': eventId, 'unlock': check})
		})
	}

	$('.all-button').click(function () {
		eventButton($(this), true)
	})

	$('.none-button').click(function() {
		eventButton($(this), false)
	})
})