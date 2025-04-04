function confirmDeleteReportFile(macmID, componentID, toolID, filename) {
    $('#deleteName').text(filename);
    $('#deleteConfirm').click(function() { deleteReportFile(macmID, componentID, toolID); });
    $('#deleteModal').modal('show');
}

function deleteReportFile(macmID, componentID, toolID) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);
    $.ajax({
        url: '/api/delete_report',
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            location.reload();
        },
        error: function(data) {
            showModal("Report Upload", JSON.parse(data.responseText), autohide = true)
        }
    });
}

function parseReportFile(element, macmID, componentID, toolID, parser) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);
    $(element).addClass('btn-loading');
    $.ajax({
        url: '/api/' + parser,
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            $('#copyParserOutput').on('click', function() { 
                navigator.clipboard.writeText(data.output); 
                showToast('Copied', 'Output copied to clipboard', true);
            });
            $('#executeParserOutput').on('click', function() { executeParser(data.output, macmID); });
            if (data.output.length > 0) {
                $('#parserOutput').text(data.output);
                window.Prism.highlightAll();
            } else {
                $('#parserOutputPre').hide();
                $('#modalParserAlert').show();
                $('#copyParserOutput').hide();
                $('#executeParserOutput').hide();
            }
            $(element).removeClass('btn-loading');
            $('#modalParserOutput').modal('show');
        },
        error: function(data) {
            $(element).removeClass('btn-loading');
            showModal("Report Upload", "Error parsing the report.", autohide = true)
        }
    });
}

function downloadReportFile(macmID, componentID, toolID) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);
    downloadReportFiles(formData, '/api/download_report');
}

function downloadAllReportFiles(macmID) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    downloadReportFiles(formData, '/api/download_all_reports');
}

function downloadReportFiles(formData, api) {
    fetch(api, {
        method: 'POST',
        body: formData
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
        showModal("Report Download", "Report " + filename + " downloaded successfully", null, autohide = true)
    })
    .catch(error => {
        showModal("Report Download", "Error downloading the file!", null, autohide = true)
    });
}

function executeParser(query, macmID) {
    let formData = new FormData();
    formData.append('AppID', macmID);
    formData.append('QueryCypher', query);
    $.ajax({
        url: '/api/update_macm',
        type: 'POST',
        contentType: false,
        processData: false,
        data: formData,
        success: function(data) {
            location.reload();
        },
        error: function(data) {
            console.log(data);
        }
    });
}