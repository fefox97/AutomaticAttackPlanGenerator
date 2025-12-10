var threat_catalog = undefined;
var default_shown_columns = undefined;

$(window).on('load', function() {
    
    threat_catalog = $('#threatCatalogTable').DataTable({
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
                    if ( type === 'sort' || type === 'type' ){
                        var data = data.replace('T', '');
                        // data = parseInt(data);
                    }

                    return data;
                },
            },
            {
                targets: [0, 3, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 25],
                searchPanes: {
                    show: false,
                },
            },
            {
                targets: [1, 2, 4, 18, 19, 20, 21, 22, 23, 24],
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

});

function replaceIDWithButton(table) {
    ["Capec Meta", "Capec Standard", 'Capec Detailed'].forEach(element => {
        table.column(element +':name').nodes().each(function (cell, i) {
            let content = cell.innerHTML;
            if (content != "None" && content != "[None]" && content != '["None"]') {
                let data = JSON.parse(content);
                let parent = document.createElement('h4');
                cell.replaceChildren(parent);
                let badges = [];
                for(let i = 0; i < data.length; i++) {
                    let badge = document.createElement('span');
                    badge.innerHTML = data[i];
                    badge.className = 'badge bg-primary';
                    badge.style = 'margin-right: 5px; cursor: pointer;';
                    badge.addEventListener('click', () => {
                        window.location.href = '/capec-detail?id=' + data[i];
                    });
                    badges.push(badge);
                }
                parent.replaceChildren(...badges);
            }
            else {
                cell.innerHTML = '';
            }
        });
    });
}

$(document).ready(function() {

    function searchQuery ( ) {
        console.log("Searching for " + $('#SearchID').val());
        if ($('#SearchID').val() === '') {
            threat_catalog.search('').columns().search('').draw();
            return;
        }
        $.ajax({
            url: '/capec',
            type: 'POST',
            data: {
                'SearchID': $('#SearchID').val(),
                'ShowTree': $('#ShowTreeToggle').is(':checked')
            },
            success: function(response) {
                ids = response.children.toString().split(',');
                ids = ids.map(function(id) { return '^' + id + '$'; }).join('|');
                threat_catalog.column(0).search(ids, true, false).draw();

            },
            error: function(error) {
                console.log(error);
            }
        });
    };
    
});
