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

function parseReportFile(macmID, componentID, toolID, parser) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);
    $.ajax({
        url: '/api/' + parser,
        type: 'POST',
        data: formData,
        contentType: false,
        processData: false,
        success: function(data) {
            $('#copyParserOutput').attr('data-clipboard-text', data.output);
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
            $('#modalParserOutput').modal('show');
        },
        error: function(data) {
            console.log(data);
        }
    });
}

function downloadReportFile(macmID, componentID, toolID) {
    let formData = new FormData();
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);

    fetch('/api/download_report', {
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
    .then(data => {
        showModal("Report Download", "Report " + filename + " downloaded successfully", autohide = true)
    })
    .catch(error => {
        showModal("Report Download", JSON.parse(error.responseText), autohide = true)
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
            $('#modalParserOutput').modal('hide');
            showModal("MACM Update", data, autohide = true,)
        },
        error: function(data) {
            console.log(data);
        }
    });
}