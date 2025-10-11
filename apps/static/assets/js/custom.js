codeInput.registerTemplate("syntax-highlighted", codeInput.templates.prism(Prism, []));

function showModal(title, response, icon=null, autohide = false, large = false, badge = null) {
    $("#modal-title").text(title);
    if (icon) {
        $("#modal-title").prepend(icon);
        $("#modal-title").find("i").addClass("me-2");
    }
    if (badge) {
        $("#modal-title").append(badge);
    }
    let messages = "";
    if (typeof response === "string") {
        messages = response;
    } else {
        for (let key in response) {
            messages += response[key] + "\n";
        }
    }
    $("#modal-body-text").text(messages);
    if (large) {
        $("#modal-upload").addClass("modal-lg");
    }
    $("#modal-upload").modal("show");
    if (autohide) {
        setTimeout(function() {
            $("#modal-upload").modal("hide");
        }, 5000);
    }
}

function showError(code, autohide = false) {
    if (code === 404) {
        response = "Page not found.";
    } else if (code === 500) {
        response = "Internal server error.";
    } else if (code === 403) {
        response = "Forbidden: You do not have permission to access this resource.";
    } else if (code === 401) {
        response = "Unauthorized: Please log in to access this resource.";
    } else {
        response = "An unexpected error occurred. Please try again later.";
    }
    let title = "Error " + code;
    showModal(title, response, '<i class="fas fa-exclamation-triangle"></i>', autohide);
}

function showToast(title, message, autohide = false, delay=5000, icon='<i class="fas fa-info"></i>') {
    const container = document.getElementById('toast-container');
    const toast_id = 'toast-' + Math.floor(Math.random() * 1000000);
    addToast(toast_id, container, title, message, icon, autohide, delay);
    const toast = document.getElementById(toast_id)
    toast.addEventListener('hidden.bs.toast', function() {
        deleteToast(toast_id);
    });
    const toastBootstrap = bootstrap.Toast.getOrCreateInstance(toast)
    toastBootstrap.show()
}

function addToast(id, container, title, message, icon, autohide, delay) {
    const wrapper = document.createElement('div')
    time = new Date().toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    wrapper.id = id
    wrapper.className = 'toast'
    wrapper.setAttribute('role', 'alert')
    wrapper.setAttribute('aria-live', 'assertive')
    wrapper.setAttribute('aria-atomic', 'true')
    wrapper.setAttribute('data-bs-autohide', autohide)
    wrapper.setAttribute('data-bs-delay', delay)
    wrapper.innerHTML =
        `<div class="toast-header">
            <strong class="text-body me-auto"> <i class="${icon}"></i> ${title}</strong>
            <small class="text-body-secondary">${time}</small>
            <button type="button" class="btn-close" data-bs-dismiss="toast" aria-label="Close"></button>
        </div>
        <div class="toast-body">
            ${message}
		</div>`,
    $('#toast-container').append(wrapper)
    container.appendChild(wrapper)
}

function deleteToast(id) {
    document.getElementById(id).remove();
}


function showAlert(response, type, icon){
    const wrapper = document.createElement('div')
    wrapper.innerHTML = [
        `<div class="alert alert-${type} alert-dismissible" role="alert">`,
        `   <div>
                <span class="material-symbols-outlined">${icon}</span>
                <span>${response.message}</span>
            </div>`,
        '   <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>',
        '</div>',
    ].join('')
    $('#liveAlertPlaceholder').append(wrapper)
    setTimeout(function() {
        wrapper.remove()
    }, 5000)
}

function enableTab() {
    var textareas = document.getElementsByTagName('textarea');
    var count = textareas.length;
    for(var i=0;i<count;i++){
        textareas[i].onkeydown = function(e){
            if(e.keyCode==9 || e.which==9){
                e.preventDefault();
                var s = this.selectionStart;
                this.value = this.value.substring(0,this.selectionStart) + "\t" + this.value.substring(this.selectionEnd);
                this.selectionEnd = s+1; 
            }
        }
    }
}

function sendSupportRequest() {
    let issue = $('#supportIssue').val();
    let subject = $('#supportSubject').val();
    let email = $('#supportEmail').val();
    $.ajax({
        url: '/api/issue',
        type: 'POST',
        data: {
            issue: issue,
            subject: subject,
            email: email
        },
        success: function(response) {
            $('#supportModal').modal('hide');
            showModal('Support Request', response);
        },
        error: function(response) {
            $('#supportModal').modal('hide');
            showModal('Support Request', response);
        }
    });
    $('#supportIssue').val('');
    $('#supportSubject').val('');
    $('#supportEmail').val('');
}

function sendTicket() {
    let issue = $('#ticketIssue').val();
    let subject = $('#ticketSubject').val();
    let email = $('#ticketEmail').val();
    $.ajax({
        url: '/api/ticket',
        type: 'POST',
        data: {
            issue: issue,
            subject: subject,
            email: email
        },
        success: function(response) {
            $('#ticketModal').modal('hide');
            showModal('Ticket', response);
        },
        error: function(response) {
            $('#ticketModal').modal('hide');
            showModal('Ticket', response);
        }
    });
    $('#ticketIssue').val('');
    $('#ticketSubject').val('');
    $('#ticketEmail').val('');
}

var old_tasks = [];

function getPendingTasks() {
    $.ajax({
        url: '/api/get_pending_tasks',
        type: 'GET',
        success: function(response) {
            current_tasks = response.tasks;
            for (let i = 0; i < current_tasks.length; i++) {
                let task = current_tasks[i];
                if (old_tasks.indexOf(task.task_id) === -1) {
                    getTaskStatus(task);
                }
            }
            old_tasks = current_tasks.map(task => task.task_id);
            setTimeout(function() {
                getPendingTasks();
            }, 5000);
        },
        error: function(response) {
            console.log(response);
        }
    });
}

function getTaskStatus(task, toast=false) {
    $.ajax({
        url: '/api/get_task_status',
        type: 'POST',
        data: {
            task_id: task.task_id
        },
        success: function(response) {
            if (response.task_status == 'PENDING') {
                setTimeout(function() {
                    getTaskStatus(task, true);
                }, 5000);
            } else {
                buttons = [];
                icon = '<i class="fas fa-info"></i>';
                if (response.task_status === 'SUCCESS' && task.type === 'pentest_report') {
                    buttons.push('<button class="btn btn-sm btn-primary ms-2" onclick="downloadReport(\'' + task.app_id + '\', \'' + task.task_id + '\', this)"><span>Download Report</span></button>');
                    icon = '<i class="fas fa-check"></i>';
                }
                buttons.push('<button type="button" class="btn btn-sm btn-danger ms-2" onclick="deleteTask(\'' + task.task_id + '\')"><span><i class="fas fa-trash"></i></span></button>');
                if (task.type === 'wiki_pages_retrieval') {
                    message = "Wiki pages retrieval task is " + response.task_status + ". You can now navigate to the Wiki section to view the retrieved pages.";
                } else if (task.type === 'pentest_report') {
                    message = "Pentest report task for the app " + task.app_name + " is " + response.task_status + ".";
                } else {
                    message = "Error: Unknown task type.";
                }
                addNotification(task.task_id, "Task status", message, buttons, task.created_on, toast, icon);
            }
        },
        error: function(response) {
            console.log(response.responseJSON);
        }
    });
}

function downloadReport(app_id, task_id, button) {
    let formData = new FormData();
    formData.append('AppID', app_id);
    formData.append('TaskID', task_id);
    downloadFiles(formData, '/api/download_ai_report', button);
}

function getNotifications() {
    $.ajax({
        url: '/api/get_notifications',
        type: 'GET',
        data: {
            
        },
        success: function(response) {
            notifications = response.notifications;
            for (let i = 0; i < notifications.length; i++) {
                let notification = notifications[i];
                buttons = [];
                if (notification.buttons) {
                    buttons = JSON.parse(notification.buttons);
                }
                addNotification(notification.id, notification.title, notification.message, buttons, notification.created_on, false, notification.icon);
            }
        },
        error: function(response) {
            console.log(response);
        }
    });
}


function deleteNotification(notification_id, event) {
    if (event) event.stopPropagation();
    $.ajax({
        url: '/api/delete_notification',
        type: 'POST',
        data: {
            notification_id: notification_id
        },
        success: function(response) {
            document.getElementById(notification_id + '_notification').remove();
            $('#notification_counter').text(parseInt($('#notification_counter').text()) - 1);
            if ($('#notification_counter').text() === '0') {
                $('#notification_counter').addClass('d-none');
                $('#no_notification_alert').removeClass('d-none');
            }
        },
        error: function(response) {
            console.log(response);
        }
    });
}

function clearNotifications() {
    $.ajax({
        url: '/api/delete_all_notifications',
        type: 'GET',
        success: function(response) {
            console.log(response);
            $('#notification_container').empty();
            $('#notification_counter').text('0');
            $('#notification_counter').addClass('d-none');
            $('#no_notification_alert').removeClass('d-none');
        },
        error: function(response) {
            console.log(response);
        }
    });
}

function addNotification(id, title, message, buttons, date, toast, icon='fas fa-info') {
    if ($('#no_notification_alert').length) {
        $('#no_notification_alert').addClass('d-none');
    }
    let notification = document.createElement('div');
    notification.className = "dropdown-item d-flex align-items-center justify-content-between";
    notification.id = id + '_notification';
    let formattedTime = new Date(date).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    notification.innerHTML = `
        <div class="d-flex align-items-center notification-item">
            <div class="me-3">
                <div class="icon icon-shape bg-primary text-white rounded-circle">
                    <i class="${icon}"></i>
                </div>
            </div>
            <div>
                <span class="h6">${title}</span>
                <span class="text-sm text-muted ms-2">${formattedTime}</span>
                <p class="text-sm text-muted text-wrap mb-0">${message}</p>
            </div>`;
    notification.innerHTML += '<div class="ms-auto">';
    if (buttons) {
        for (let i = 0; i < buttons.length; i++) {
            notification.innerHTML += buttons[i];
        }
    }
    notification.innerHTML += `<button type="button" class="btn btn-sm btn-danger" onclick="deleteNotification('${id}', event)"> <span class="fas fa-times"></span> </button>`;
    notification.innerHTML += '</div>';
    notification.innerHTML += '</div>';
    let container = document.getElementById('notification_container');
    if (container.firstChild) {
        container.insertBefore(notification, container.firstChild);
    } else {
        container.appendChild(notification);
    }
    if ($('#notification_counter').hasClass('d-none')) {
        $('#notification_counter').removeClass('d-none');
    }
    $('#notification_counter').text(parseInt($('#notification_counter').text()) + 1);
    if (toast)
        showToast(title, message, autohide = true, 5000, icon);
}

function downloadFiles(formData, api, button) {
    $(button).addClass('btn-loading');
    $.ajax({
        url: api,
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
        xhrFields: {
            responseType: 'blob'
        },
        success: function(response, status, xhr) {
            const header = xhr.getResponseHeader('Content-Disposition');
            if (!header) {
                throw new Error("Intestazione Content-Disposition mancante");
            }
            const parts = header.split(';');
            const filename = parts[1].split('=')[1].replace(/"/g, '');

            const url = window.URL.createObjectURL(new Blob([response]));
            const link = document.createElement('a');
            link.href = url;
            link.setAttribute('download', filename);
            document.body.appendChild(link);
            link.click();
            link.parentNode.removeChild(link);

            showModal("File Download", filename + " downloaded successfully", null, autohide = true);
            $(button).removeClass('btn-loading');
        },
        error: function(error) {
            showModal("File Download", "Error downloading the file!", null, autohide = true);
            $(button).removeClass('btn-loading');
        }
    });
}

function searchInPage(search) {
    let result = window.find(search);
    if (!result) {
        showModal("Search", "Text not found in the page.", '<i class="fa fa-search"</i>', autohide = true);
    }
}

$(window).on('load', function() {
    $('.nav-item.active').children('.multi-level.collapse').collapse('show');
    enableTab();
    $('#navbar-search-main').on('submit', function(e) {
        e.preventDefault();
        text = $('#topbarInputIconLeft').val();
        searchInPage(text);
    });

    socket.on('receive_notification', function(data) {
        addNotification(data.id, data.title, data.message, data.buttons, data.date, true, data.icon);
    });
});