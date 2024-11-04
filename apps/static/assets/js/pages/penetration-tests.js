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
        this.querySelector('#edit-app-id').value = AppID;
        this.querySelector('#edit-app-name').textContent = AppName;
    });

    $('#edit-submit').click(function() {
        const AppID = $('#edit-app-id').val();
        const QueryCypher = $('#edit-query-cypher').val();
        $.ajax({
            url: '/api/update_macm',
            type: 'POST',
            data: {
                AppID: AppID,
                QueryCypher: QueryCypher,
            },
            success: function(response) {
                location.reload();
            },
            error: function(response) {
                $('#editMacmModal').modal('hide');
                showModal("Update failed", JSON.parse(response.responseText));
            }
        })
    });

    $('#deleteMacmModal').on('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const AppID = button.getAttribute('data-bs-AppID');
        const AppName = button.getAttribute('data-bs-AppName');
        $('#app-name-body').text(AppName);
        this.querySelector('#delete-app-id').value = AppID;
    });
});