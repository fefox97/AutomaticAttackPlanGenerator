$(document).ready(function() {
    $('#ReloadCapec').on('click', function() {
        console.log("Reloading Databases");
        reloadDatabases("Capec");
    });
    $('#ReloadThreatCatalog').on('click', function() {
        console.log("Reloading Databases");
        reloadDatabases("ThreatCatalog");
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