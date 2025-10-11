var macm = undefined;
var default_shown_columns = undefined;

$(window).on('load', function() {
    
    $("#editMacmModal").on('click', function () {
        $('#editAppName').text(app_name);
        $('#editMacmModal').modal('show');
    });

    // Set default shown columns
    if (localStorage.getItem('macm_columns') === null) {    
        default_shown_columns = ['Component ID', 'Name', 'Type', 'Action'];
        localStorage.setItem('macm_columns', JSON.stringify(default_shown_columns));
    } else {
        default_shown_columns = JSON.parse(localStorage.getItem('macm_columns'));
    }
    
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
        autoWidth: false,
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
                        // let id = data.match(/(<a.*>\s*)(\d*)(\s)/)[2];
                        let id = $(data).find('a').attr('id');
                        return parseInt(id);
                    }
                    return data;
                }
            },
            {
                targets: [0, 1, 4],
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
            // Hide columns that are not in default_shown_columns
            this.api().columns().every(function () {
                if (!default_shown_columns.includes(this.header().innerHTML)) {
                    this.visible(false);
                }
            });
            this.api().draw();
        }
    });

    // Set column names for search
    macm.settings()[0].aoColumns.forEach(function(column) {
        column.sName = column.sTitle;
    });
    
    // Save column visibility state
    macm.on('column-visibility.dt', function (e, settings, column, state) {
        if (state) {
            default_shown_columns.push(settings.aoColumns[column].sTitle);
        } else {
            default_shown_columns = default_shown_columns.filter(function(value, index, arr){ return value != settings.aoColumns[column].sTitle;});
        }
        localStorage.setItem('macm_columns', JSON.stringify(default_shown_columns));
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

    $("#exportAttackPlan").on('click', function () {
        let formData = new FormData();
        formData.append('AppID', app_id);
        downloadFiles(formData, '/api/download_attack_plan', this);
    });
    
    $("#generateAIReport").on('click', function () {
        generateAIReport(app_id);
    });

    function generateAIReport(app_id) {
        $.ajax({
            url: '/api/generate_ai_report',
            type: 'POST',
            data: {
                AppID: app_id,
            },
            success: function(response) {
                showModal("AI Report", "AI Report generation started successfully. You will be notified when it is ready. Remeber that this process may take a while and the feature is still in beta.", icon="<i class='bi bi-stars'></i>", false, false, badge="<span class='badge rounded-pill bg-warning text-dark ms-2'>Beta</span>");
            },
            error: function(response) {
                showModal("AI Report", response.responseJSON.message, icon="<i class='bi bi-stars'></i>", false, false, badge="<span class='badge rounded-pill bg-warning text-dark ms-2'>Beta</span>");
            }
        });
    }

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
