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

    $('#deleteMacmModal').on('show.bs.modal', function(event) {
        const button = event.relatedTarget;
        const AppID = button.getAttribute('data-bs-AppID');
        const AppName = button.getAttribute('data-bs-AppName');
        $('#app-name-body').text(AppName);
        this.querySelector('#app-id').value = AppID;
    });
});