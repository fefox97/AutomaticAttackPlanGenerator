var macm = undefined;
var default_shown_columns = undefined;
let neoVizGraph;
let neoVizSchema;
var activeTab;

$(window).on('load', function() {

    DataTable.Buttons.defaults.dom.button.className = 'btn';

    macm = $('#macmTable').DataTable({
        "paging": false,
        "ordering": true,
        "order": [[ 0, "asc" ]],
        "colReorder": true,
        dom: 'Bfrtip',
        searchPane: true,
        "scrollX": true,
        "scrollY": "50vh",
        "scrollCollapse": true,
        autoWidth: true,
        responsive: true,
        stateSave: true,
        fixedColumns: {
            left: 1
        },
        columnDefs: [
            {
                targets: 0,
                className: 'noVis',
                width: '120px',
                render: function (data, type, row) {
                    if (type === 'sort' || type === 'type') {
                        let id = $(data).find('a').attr('id');
                        return parseInt(id);
                    }
                    return data;
                }
            },
            {
                targets: [0, 1, 4, 5],
                searchPanes: {
                    show: false,
                },
            },
            {
                targets: [2, 3],
                searchPanes: {
                    show: true,
                },
            },
        ],
        buttons: [
            {
                className: 'btn-secondary',
                extend: 'colvis',
                columns: ':not(.noVis)'
            },
            {
                className: 'btn-secondary',
                extend: 'searchPanes'
            }
        ],
        initComplete: function () {
            // Add search bar for each column
            this.api().columns().every(function () {
                let column = this;
                let title = column.footer().textContent;

                // Create input element
                let input = document.createElement('input');
                input.placeholder = "Filter by " + title;
                input.className = 'form-control';
                column.footer().replaceChildren(input);

                // Event listener for user input
                input.addEventListener('keyup', () => {
                    if (column.search() !== this.value) {
                        column.search(input.value, false, true, true).draw();
                    }
                });
            });
            this.api().draw();
        }
    });


    // Collapse all cards
    $('.card-header.collapsed').each(function() {
        $(this).parent('.card').find('.collapse').collapse('hide');
        $(this).parent('.card').find('.collapse').removeClass('show');
    });

    // Edit MACM
    $('#editMacmSubmit').click(function() {
        const QueryCypher = $('#editQueryCypher').val();
        editMacm(app_id, QueryCypher);
    });

    $("#exportThreatModel").on('click', function () {
        let formData = new FormData();
        formData.append('AppID', app_id);
        downloadFiles(formData, '/api/download_threat_model', this);
    });
});

function deleteComponent(App_ID, ComponentID, ComponentName) {
$('#deleteName').text(ComponentName);
$('#deleteConfirm').click(function() {
    $.ajax({
        url: '/api/delete_macm_component',
        type: 'POST',
        data: {
            AppID: App_ID,
            ComponentID: ComponentID,
        },
        success: function(response) {
            location.reload();
        },
        error: function(response) {
            $('#deleteModal').modal('hide');
            showModal("Delete failed", JSON.parse(response.responseText));
        }
    })
});
$('#deleteModal').modal('show');
}