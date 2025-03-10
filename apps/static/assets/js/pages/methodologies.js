var methodology_catalog = undefined;
var default_shown_columns = undefined;

$(window).on('load', function() {

    // Set default shown columns
    if (localStorage.getItem('methodologies_catalog_columns') === null) {    
        default_shown_columns = ['Methodology ID', 'Name', 'Asset Type', 'Description', 'Link'];
        localStorage.setItem('methodologies_catalog_columns', JSON.stringify(default_shown_columns));
    } else {
        default_shown_columns = JSON.parse(localStorage.getItem('methodologies_catalog_columns'));
    }
    
    methodology_catalog = $('#methodologiesCatalogTable').DataTable({
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
            },
            {
                targets: [0, 1, 3, 4],
                searchPanes: {
                    show: false,
                },
            },
            {
                targets: [2],
                searchPanes: {
                    show: true,
                },
            },
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
    methodology_catalog.settings()[0].aoColumns.forEach(function(column) {
        column.sName = column.sTitle;
    });
    

    // Save column visibility state
    methodology_catalog.on('column-visibility.dt', function (e, settings, column, state) {
        if (state) {
            default_shown_columns.push(settings.aoColumns[column].sTitle);
        } else {
            default_shown_columns = default_shown_columns.filter(function(value, index, arr){ return value != settings.aoColumns[column].sTitle;});
        }
        localStorage.setItem('methodologies_catalog_columns', JSON.stringify(default_shown_columns));
    });
});

$(document).ready(function() {
    
});
