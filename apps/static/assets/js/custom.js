codeInput.registerTemplate("syntax-highlighted", codeInput.templates.prism(Prism, []));

function showModal(title, response, icon=null, autohide = false, large = false, badge = null) {
    $("#modal-title").text(title);
    if (icon) {
        $("#modal-title").prepend(icon);
    }
    if (badge) {
        $("#modal-title").append(badge);
    }
    let messages = "";
    if (typeof response === "string") {
        messages = response;
    } else {
        for (let key in response) {
            messages += key + ": " + response[key] + "\n";
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

function getTaskStatus(task) {
    $.ajax({
        url: '/api/get_task_status',
        type: 'POST',
        data: {
            task_id: task.task_id
        },
        success: function(response) {
            if (response.task_status == 'PENDING') {
                setTimeout(function() {
                    getTaskStatus(task);
                }, 5000);
            } else {
                buttons = [];
                icon = '<i class="fas fa-info"></i>';
                if (response.task_status === 'SUCCESS') {
                    buttons.push('<button class="btn btn-sm btn-primary ms-2" onclick="downloadReport(\'' + task.app_id + '\', \'' + task.task_id + '\', this)"><span>Download Report</span></button>');
                    icon = '<i class="fas fa-check"></i>';
                }
                buttons.push('<button class="btn btn-sm btn-danger ms-2" onclick="deleteTask(\'' + task.task_id + '\')"><span><i class="fas fa-trash"></i></span></button>');
                addNotification(task.task_id, "Task status", task.task_name + " for the app " + task.app_name + " is " + response.task_status, buttons, task.created_on, icon);
            }
        },
        error: function(response) {
            console.log(response.responseJSON);
        }
    });
}

function deleteTask(task_id) {
    $.ajax({
        url: '/api/delete_task',
        type: 'POST',
        data: {
            task_id: task_id
        },
        success: function(response) {
            console.log(response);
            removeNotification(task_id);
        },
        error: function(response) {
            console.log(response);
        }
    });
}

function downloadReport(app_id, task_id, button) {
    let formData = new FormData();
    formData.append('AppID', app_id);
    formData.append('TaskID', task_id);
    downloadFiles(formData, '/api/download_ai_report', button);
}

function addNotification(id, title, message, buttons, time, icon='<i class="fas fa-info"></i>') {
    if ($('#no_notification_alert').length) {
        $('#no_notification_alert').addClass('d-none');
    }
    let notification = document.createElement('div');
    notification.className = "dropdown-item d-flex align-items-center justify-content-between";
    notification.id = id + '_notification';
    let formattedTime = new Date(time).toLocaleString('en-GB', { day: '2-digit', month: '2-digit', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    notification.innerHTML = `
        <div class="d-flex align-items-center">
            <div class="me-3">
                <div class="icon icon-shape bg-primary text-white rounded-circle">
                    `+ icon +`
                </div>
            </div>
            <div>
                <span class="h6">`+ title +`</span>
                <span class="text-sm text-muted ms-2">`+ formattedTime +`</span>
                <p class="text-sm text-muted mb-0">`+ message +`</p>
            </div>
        </div>`;
    if (buttons) {
        for (let i = 0; i < buttons.length; i++) {
            notification.innerHTML += buttons[i];
        }
    }
    $('#notification_container').append(notification);
    if ($('#notification_counter').hasClass('d-none')) {
        $('#notification_counter').removeClass('d-none');
    }
    $('#notification_counter').text(parseInt($('#notification_counter').text()) + 1);
}

function removeNotification(id) {
    document.getElementById(id + '_notification').remove();
    $('#notification_counter').text(parseInt($('#notification_counter').text()) - 1);
    if ($('#notification_counter').text() === '0') {
        $('#notification_counter').addClass('d-none');
        $('no_notification_alert').removeClass('d-none');
    }
}

function clearNotifications() {
    for (let i = 0; i < old_tasks.length; i++) {
        deleteTask(old_tasks[i]);
    }
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
        showModal("Search", "Text not found in the page", null, autohide = true);
    }
}

$(window).on('load', function() {
    $('.nav-item.active').children('.multi-level.collapse').collapse('show');
    enableTab();
    $('#navbar-search-main').on('submit', function(e) {
        e.preventDefault();
        text = $('#topbarInputIconLeft').val();
        searchInPage(text);
    }
    );
});
