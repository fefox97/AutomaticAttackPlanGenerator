$(document).ready(function() {
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });

    getAllCommands();
    $('.command-input').on('change', function() {
        getAllCommands();
    });

    $('#ExpandToggle').prop('checked', false);
    $('#ExpandToggle').on('click', function() {
        if ($(this).hasClass('active')) {
            $("#accordionOne .collapse").collapse('show');
        } else {
            $("#accordionOne .collapse").collapse('hide');
        }
    });
    $("#accordionOne [aria-expanded='false']").each(function() {
        $(this).closest('.accordion-item').children('.collapse').collapse('hide');
    });
    $('.bg-capec').click(function() {
        window.open($(this).attr('href'), '_blank');
    });
    $('.report-file').children('button').click(upload_report_file);
});

function upload_report_file() {
    let fileDiv = $(this).parent('.report-file').find('#reportFile');
    let parser = fileDiv.attr('parser');
    let macmID = fileDiv.attr('macmID');
    let componentID = fileDiv.attr('componentID');
    let toolID = fileDiv.attr('toolID');
    let file = fileDiv[0].files[0];
    let formData = new FormData();
    formData.append('parser', parser);
    formData.append('macmID', macmID);
    formData.append('componentID', componentID);
    formData.append('toolID', toolID);
    formData.append('reportFile', file);
    $.ajax({
        url: '/api/upload_report',
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

function copySingleCommand(element) {
    let command = '';
    element.parent('.command').find('.command-input').each(function(el) {
        if(this.nodeName == 'SPAN') {
            command += $(this).text();
        }
        else if(this.nodeName == 'INPUT') {
            let value = $(this).val();
            if(value == '') {
                value = $(this).attr('placeholder');
            }
            command += value;
        }
    });
    navigator.clipboard.writeText(command);
}

function getAllCommands(){
    let commands = [];
    $('.command').each(function() {
        let command = '';
        $(this).find('.command-input').each(function(el) {
            if(this.nodeName == 'SPAN') {
                command += $(this).text();
            }
            else if(this.nodeName == 'INPUT') {
                let value = $(this).val();
                if(value == '') {
                    value = $(this).attr('placeholder');
                }
                command += value;
            }
        });
        commands.push(command);
    });
    commands = Array.from(new Set(commands));
    $('#allCommands').text(commands.join('\n'));
    window.Prism.highlightAll();
}

function copyAllCommands() {
    navigator.clipboard.writeText($('#allCommands').text());
}

function downloadAllCommands(filename){
    const link = document.createElement("a");
    let blob = new Blob([$('#allCommands').text()], {type: "text/plain;charset=utf-8"});
    link.href = URL.createObjectURL(blob);
    link.download = filename || "commands.sh";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}