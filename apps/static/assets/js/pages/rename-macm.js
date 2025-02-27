function renameMacm(AppID, AppName) {
    $.ajax({
        url: '/api/rename_macm',
        type: 'POST',
        data: {
            AppID: AppID,
            AppName: AppName,
        },
        success: function(response) {
            location.reload();
        },
        error: function(response) {
            $('#renameMacmModal').modal('hide');
            showModal("Update failed", JSON.parse(response.responseText));
        }
    })
}

$(document).ready(function() {
    $('#renameMacmModal').on('show.bs.modal', function(event) {
        const AppID = event.relatedTarget.getAttribute('data-bs-AppID');
        const AppName = event.relatedTarget.getAttribute('data-bs-AppName');
        this.querySelector('#renameAppID').value = AppID;
        this.querySelector('#renameCurrentAppName').textContent = AppName;
    });

    $('#renameMacmSubmit').click(function() {
        const AppID = $('#renameAppID').val();
        const NewAppName = $('#renameNewAppName').val();
        renameMacm(AppID, NewAppName);
    });
});