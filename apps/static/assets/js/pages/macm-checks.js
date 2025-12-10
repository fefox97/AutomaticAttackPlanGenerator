var macm_check_catalog = undefined;
var default_shown_columns = undefined;

$(window).on('load', function() {

    macm_check_catalog = $('#macmCheckCatalogTable').DataTable({
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
            },
            {
                targets: 3,
                width: '120px',
            }
        ],
        buttons: [
            {
                extend: 'colvis',
                columns: ':not(.noVis)'
            },
            'searchPanes',
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

});

$(document).ready(function() {
    
});
