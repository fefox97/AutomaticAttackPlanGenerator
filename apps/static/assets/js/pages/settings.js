$(document).ready(function() {
    $("#editSettingModal").on('show.bs.modal', function(e) {
        setting_name = e.relatedTarget.dataset['bsSettingName'];
        setting_key = e.relatedTarget.dataset['bsSettingKey'];
        setting_value = e.relatedTarget.dataset['bsSettingValue'];
        if (setting_value.length > 100) {
            $('#editSettingValue').attr('rows', '6');
        }else{
            $('#editSettingValue').attr('rows', '1');
        }
        $('#editSettingName').text(setting_name);
        $('#editSettingKey').val(setting_key);
        $('#editSettingValue').val(setting_value);
        $('#editMacmModal').modal('show');
    });
    $("#editSettingSubmit").click(function() {
        setting_key = $('#editSettingKey').val();
        setting_value = $('#editSettingValue').val();
        editSetting(setting_key, setting_value, $('#editSettingModal'));
    }
    );
});

function reloadDatabases(database) {
    let button = '#Reload'+database;
    $(button).addClass('btn-loading');
    $.ajax({
        url: '/api/reload_databases',
        type: 'POST',
        data: {
            'database': database,
        }
    }).done(function(response) {
        showModal("Success", response, true);
        $(button).removeClass('btn-loading');
    }).fail(function(response) {
        showModal("Error", JSON.parse(response.responseText));
        $(button).removeClass('btn-loading');
    });
}

function uploadExcel() {
    var file = $('#excelFile')[0].files[0];
    var formData = new FormData();
    formData.append('file', file);
    $.ajax({
        url: '/api/upload_excel',
        type: 'POST',
        data: formData,
        processData: false,
        contentType: false,
    }).done(function(response) {
        showModal("Success", response, true);
    }).fail(function(response) {
        showModal("Error", JSON.parse(response.responseText));
    });
}

function downloadExcel() {
    fetch('/api/download_excel', {
        method: 'POST'
    }).then(response => {
        const header = response.headers.get('Content-Disposition');
        const parts = header.split(';');
        filename = parts[1].split('=')[1];
        return response;
    }
    )
    .then(response => 
        response.blob()
    )
    .then(blob => {
        const url = window.URL.createObjectURL(new Blob([blob]));
        const link = document.createElement('a');
        link.href = url;
        link.setAttribute('download', filename);
        document.body.appendChild(link);
        link.click();
        link.parentNode.removeChild(link);
    })
    .then(_ => {
        showModal("Excel Download", filename + " downloaded successfully", autohide = true)
    })
    .catch(error => {
        showModal("Excel Download", "Error downloading the file!", autohide = true)
    });
}

function test(){
    $.ajax({
        url: '/api/test',
        type: 'POST',
    }).done(function(response) {
        showModal("Success", response);
    }).fail(function(response) {
        showModal("Error", JSON.parse(response.responseText));
    });
}

function editSetting(SettingKey, SettingValue, settingModal) {
    $.ajax({
        url: '/api/edit_setting',
        type: 'POST',
        data: {
            key: SettingKey,
            value: SettingValue,
        },
        success: function(response) {
            location.reload();
        },
        error: function(response) {
            settingModal.modal('hide');
            showModal("Update failed", JSON.parse(response.responseText));
        }
    })
}

function retrieveWiki() {
    let button = '#RetrieveWikiPages';
    $(button).addClass('btn-loading');
    $.ajax({
        url: '/api/retrieve_wiki',
        type: 'GET',
    }).done(function(response) {
        showModal("Wiki Pages", response.message, true);
        $(button).removeClass('btn-loading');
    }).fail(function(response) {
        showModal("Error", JSON.parse(response.responseText));
        $(button).removeClass('btn-loading');
    });
}