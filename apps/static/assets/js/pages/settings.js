$(document).ready(function() {
    $('#ReloadCapec').on('click', function() {
        console.log("Reloading Capec");
        reloadDatabases("Capec");
    });
    $('#ReloadThreatCatalog').on('click', function() {
        console.log("Reloading ThreatCatalog");
        reloadDatabases("ThreatCatalog");
    });
    $('#ReloadToolCatalog').on('click', function() {
        console.log("Reloading ToolCatalog");
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
        },
        success: function(response) {
            console.log(response);
        }
    });
}

function test(){
    $.ajax({
        url: '/api/test',
        type: 'POST',
        success: function(response) {
            console.log(response);
        }
    });
}