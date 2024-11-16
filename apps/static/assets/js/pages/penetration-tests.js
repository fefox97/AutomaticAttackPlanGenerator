$(document).ready(function() {

    // Collapse all cards
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });

    $('#uploadMacmForm').submit(function(e) {
        e.preventDefault();
        let formData = new FormData(this);
        $.ajax({
            url: '/api/upload_macm',
            type: 'POST',
            data: formData,
            enctype: 'multipart/form-data',
            processData: false,
            contentType: false,
            cache: false,
        }).done(function(response) {
            location.reload();
        }).fail(function(response) {
            showModal("Upload failed", JSON.parse(response.responseText));
        });
    });

    $('#editMacmModal').on('show.bs.modal', function(event) {
        const AppID = event.relatedTarget.getAttribute('data-bs-AppID');
        const AppName = event.relatedTarget.getAttribute('data-bs-AppName');
        this.querySelector('#editAppID').value = AppID;
        this.querySelector('#editAppName').textContent = AppName;
    });

    $('#editMacmSubmit').click(function() {
        const AppID = $('#editAppID').val();
        const QueryCypher = $('#editQueryCypher').val();
        editMacm(AppID, QueryCypher);
    });

    $('#deleteModal').on('show.bs.modal', function(event) {
        const AppID = event.relatedTarget.dataset.bsAppid;
        const AppName = event.relatedTarget.dataset.bsAppname;
        $('#deleteName').text(AppName);
        $('#deleteConfirm').click(function() { deleteMacm(AppID); });
        this.querySelector('#deleteID').value = AppID;
    });

    $('#shareMacmModal').on('show.bs.modal', function(event) {
        $('#shareAppName').text(event.relatedTarget.dataset.bsAppname);
        $('#shareSubmit').click(function() { shareMacm(event.relatedTarget.dataset.bsAppid); });
        event.currentTarget.querySelectorAll('[type="checkbox"]').forEach(checkbox => {
            if (usersPerApp[event.relatedTarget.dataset.bsAppid].includes(parseInt(checkbox.value))) {
                checkbox.checked = true;
            }
        });
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

function deleteMacm(AppID) {
    var formData = new FormData();
    formData.append('AppID', AppID);
    $.ajax({
        url: '/api/delete_macm',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false
    }).done(function(response) {
        location.reload();
    }).fail(function(response) {
        $('#deleteModal').modal('hide');
        showModal("Delete failed", JSON.parse(response.responseText), autohide = true);
    });
}