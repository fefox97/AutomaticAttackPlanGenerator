codeInput.registerTemplate("syntax-highlighted", codeInput.templates.prism(Prism, []));

function showModal(title, response, autohide = false, large = false){
    $("#modal-title").text(title);
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

$(document).ready(function() {
    $('.nav-item.active').children('.multi-level.collapse').collapse('show');
    enableTab();
});