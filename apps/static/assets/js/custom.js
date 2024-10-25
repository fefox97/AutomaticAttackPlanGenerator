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
        }, 2000);
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

$(document).ready(function() {
    $('.nav-item.active').children('.multi-level.collapse').collapse('show');
});