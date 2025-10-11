$(document).ready(function() {
    $('#shareMacmModal').on('show.bs.modal', function(event) {
        $('#shareAppName').text(event.relatedTarget.dataset.bsAppname);
        $('#shareSubmit').click(function() { shareMacm(event.relatedTarget.dataset.bsAppid); });
        event.currentTarget.querySelectorAll('[type="checkbox"]').forEach(checkbox => {
            if (usersPerApp[event.relatedTarget.dataset.bsAppid].includes(parseInt(checkbox.value))) {
                checkbox.checked = true;
            }
        });
    });
    $('#unshareMacmModal').on('show.bs.modal', function(event) {
        $('#unshareAppName').text(event.relatedTarget.dataset.bsAppname);
        $('#unshareConfirm').click(function() { unshareMacm(event.relatedTarget.dataset.bsAppid, event.relatedTarget.dataset.bsUserid); });
    });
});

function shareMacm(AppID) {
    var Users = [];
    document.querySelectorAll('#shareMacmModal input[type="checkbox"]:checked').forEach(checkbox => {
        Users.push(checkbox.value);
    });
    var formData = new FormData();
    formData.append('AppID', AppID);
    formData.append('Users', Users);
    $.ajax({
        url: '/api/share_macm',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
    }).done(function(response) {
        location.reload();
    }).fail(function(response) {
        $('#shareMacmModal').modal('hide');
        showModal("Share failed", JSON.parse(response.responseText), autohide = true);
    });
}

function unshareMacm(AppID, UserID) {
    var formData = new FormData();
    formData.append('AppID', AppID);
    formData.append('UserID', UserID);
    $.ajax({
        url: '/api/unshare_macm',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
    }).done(function(response) {
        location.reload();
    }).fail(function(response) {
        $('#unshareMacmModal').modal('hide');
        showModal("Unshare failed", JSON.parse(response.responseText), autohide = true);
    });
}