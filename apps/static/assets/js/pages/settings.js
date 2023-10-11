$(document).ready(function() {
    $('#ReloadCapec').on('click', function() {
        reloadDatabases("Capec");
    });
    $('#ReloadThreatCatalog').on('click', function() {
        reloadDatabases("ThreatCatalog");
    });
    $('#ReloadToolCatalog').on('click', function() {
        reloadDatabases("ToolCatalog");
    });
    $('#TestButton').on('click', function() {
        test();
    });
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