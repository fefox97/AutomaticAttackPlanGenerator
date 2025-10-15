$(document).ready(function() {
    $('#EditoMacmChecksStatusModal').on('show.bs.modal', function(e) {
        getMacmChecksStatus();
    });
});

function getMacmChecksStatus() {
    let MacmCheckStatusModal = $('#EditoMacmChecksStatusModal');
    MacmCheckStatusModal.find('.modal-title').text('MACM Integrity Checks Status');
    fetch('/api/get_macm_check_status', {
        method: 'GET',
    }).then(response => response.json())
    .then(data => {
        let checks = data.status;
        MacmCheckStatusModal.find('.modal-body').empty();
    let table = $('<table class="table table-striped"><thead><tr><th scope="col">Check Name</th><th scope="col" class="text-center align-middle">Activated</th></tr></thead><tbody></tbody></table>');
        checks.forEach(check => {
            let row = $('<tr></tr>');
            row.append('<td>' + check[1] + '</td>');
            let activatedCheckbox = $('<input type="checkbox" class="form-check-input mx-auto d-block">');
            if (check[2]) {
                activatedCheckbox.prop('checked', true);
            }
            let activatedTd = $('<td class="text-center align-middle"></td>').append(activatedCheckbox);
            row.append(activatedTd);
            row.data('check-id', check[0]);
            table.find('tbody').append(row);
        });
        MacmCheckStatusModal.find('.modal-body').append(table);
        MacmCheckStatusModal.modal('show');
    })
    .catch(error => {
        showModal("MACM Integrity Checks", "Error retrieving MACM integrity check status!", null, autohide = true)
    });
}

function editMacmChecksStatus() {
    let MacmCheckStatusModal = $('#EditoMacmChecksStatusModal');
    MacmCheckStatusModal.modal('hide');
    let rows = MacmCheckStatusModal.find('table tbody tr');
    let updates = [];
    rows.each(function() {
        let row = $(this);
        let checkId = row.data('check-id');
        let activated = row.find('input[type="checkbox"]').is(':checked');
        updates.push({
            id: checkId,
            activated: activated
        });
    });
    console.log("Updates:", JSON.stringify(updates));
    $.ajax({
        url: '/api/update_macm_check_status',
        type: 'POST',
        data: {
            check_status: JSON.stringify(updates),
        },
        success: function(response) {
            showModal("MACM Integrity Checks", response.message, null, autohide = true);
        },
        error: function(response) {
            showModal("MACM Integrity Checks", JSON.parse(response.responseText), null, autohide = true);
        }
    });
}