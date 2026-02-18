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

	unlockData = $("#unlock-data").data("json")
	rows = []
	for (group of unlockData) {
		groupCell = $("<td>").data("group-id", group.id).text(group['name'])
		currentRow = [groupCell]
		groupTaskCount = 0
		for (event of group.events) {
			eventCell = $("<td>").data("event-id", event.id).text(event['name'])
			currentRow.push(eventCell)
			eventTaskCount = 0
			for (task of event.tasks) {
				taskCell = $("<td>").data("task-id", task.id)
				if (group.deleteTasks) {
					taskCell.append("[")
					taskCell.append($(`<a class="delete-task" href="delete_task/${task.id}">`)
						.data("task-songs", task.songs)
						.text("delete")
					)
					taskCell.append("] ")
				}
				taskCell.append(task.name)
				currentRow.push(taskCell)
				eventTaskCount++
				groupTaskCount++
				rows.push(currentRow)
				currentRow = []
			}
			for (newTaskSpec of group.newTasks) {
				taskCell = $('<td class="add-task">')
				taskCell.append($(`<a href="${newTaskSpec.endpoint}/${event.id}">`).text(newTaskSpec.text))
				currentRow.push(taskCell)
				eventTaskCount++
				groupTaskCount++
				rows.push(currentRow)
				currentRow = []
			}
			eventCell.attr("rowspan", eventTaskCount)
		}
		for (newEventSpec of group.newEvents) {
			eventCell = $('<td class="add-task">')
			eventCell.append($(`<a href="${newEventSpec.endpoint}/${group.id}">`).text(newEventSpec.text))
			rows.push([eventCell])
			groupTaskCount++
		}
		groupCell.attr("rowspan", groupTaskCount)
	}

	table = $("#unlocks-table")
	for (rowCells of rows) {
		row = $("<tr>")
		for (cell of rowCells) {
			row.append(cell)
		}
		table.append(row)
	}

	table.on('click', 'a.delete-task', function(event) {
		taskSongs = $(this).data('task-songs')
		confirmText = `Deleting this pack will free the following songs from GP jail:\n\n${taskSongs}\n\nClick OK to confirm deletion.`
		if (!confirm(confirmText)) {
			event.preventDefault()
		}
	})
})