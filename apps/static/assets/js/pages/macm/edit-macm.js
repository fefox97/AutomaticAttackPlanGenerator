function editMacm(AppID, QueryCypher) {
    $.ajax({
        url: '/api/update_macm',
        type: 'POST',
        data: {
            AppID: AppID,
            QueryCypher: QueryCypher,
        },
        success: function(response) {
            location.reload();
        },
        error: function(response) {
            $('#editMacmModal').modal('hide');
            showModal("Update failed", JSON.parse(response.responseText));
        }
    })
}