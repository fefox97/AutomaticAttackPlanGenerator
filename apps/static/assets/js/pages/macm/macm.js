$(document).ready(function() {

    // Collapse all cards
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });

    $('#uploadMacmForm').submit(function(e) {
        e.preventDefault();
        $('.upload_macm').addClass('btn-loading');
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
            $('.upload_macm').removeClass('btn-loading');
            showModal("Upload failed", JSON.parse(response.responseText));
        });
    });

    $('#uploadDockerComposeForm').submit(function(e) {
        e.preventDefault();
        $('.upload_docker_compose').addClass('btn-loading');
        let formData = new FormData(this);
        $.ajax({
            url: '/api/upload_docker_compose',
            type: 'POST',
            data: formData,
            enctype: 'multipart/form-data',
            processData: false,
            contentType: false,
            cache: false,
        }).done(function(response) {
            showDC2MModal(response.app_name + " MACM", response.cypher, response.app_name);
        }).fail(function(response) {
            $('.upload_docker_compose').removeClass('btn-loading');
            showModal("Upload failed", JSON.parse(response.responseText));
        });
    });

    $('#uploadDC2MOutput').click(function() {
        $(this).addClass('btn-loading');
        let cypher = $('#modalDC2MOutput').text();
        if (cypher) {
            let formData = new FormData();
            formData.append('macmAppName', $('#uploadDC2MOutput').attr('data-app-name'));
            formData.append('macmCypher', cypher);
            $.ajax({
                url: '/api/upload_macm',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false
            }).done(function(response) {
                location.reload();
            }).fail(function(response) {
                $(this).removeClass('btn-loading');
                $('#modalDC2M').modal('hide');
                showModal("Upload failed", JSON.parse(response.responseText), autohide = true);
            });
        }
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
});

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

function showDC2MModal(title, cypher, app_name) {
    $('#modalDC2MLabel').text(title);
    if (cypher) {
        $('#modalDC2MOutput').text(cypher);
        $('#modalDC2MOutputPre').show();
        $('#modalDC2MAlert').hide();
        $('#uploadDC2MOutput').attr('data-app-name', app_name);
        $('#uploadDC2MOutput').show();
        $('#copyDC2MOutput').show();
        $('#copyDC2MOutput').attr('data-clipboard-text', cypher);
    } else {
        $('#modalDC2MOutputPre').hide();
        $('#modalDC2MAlert').show();
        $('#uploadDC2MOutput').hide();
        $('#copyDC2MOutput').hide();
    }
    $('#modalDC2M').modal('show');
    Prism.highlightAll();
    $('.upload_macm').removeClass('btn-loading');
}