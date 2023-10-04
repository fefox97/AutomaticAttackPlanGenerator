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
});

function reloadDatabases(database) {
    console.log("Reloading Databases");
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