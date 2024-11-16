$(document).ready(function() {
    
});

function reloadDatabases(database) {
    $.ajax({
        url: '/api/reload_databases',
        type: 'POST',
        data: {
            'database': database,
        }
    }).done(function(response) {
        showModal("Success", response, true);
    }).fail(function(response) {
        showModal("Error", JSON.parse(response.responseText));
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