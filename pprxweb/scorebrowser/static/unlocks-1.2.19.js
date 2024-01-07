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

var csrfToken = null

$(document).ready(function () {
	csrfToken = getCookie('csrftoken')

	function eventButton(button, check) {
		eventId = button.attr('data-event')
		$(`div[data-event='${eventId}']`).find(':checkbox').prop('checked', check)
		$.ajax({
			url: '/scorebrowser/update_unlock_event',
			type: 'POST',
			headers: {'X-CSRFToken': csrfToken},
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