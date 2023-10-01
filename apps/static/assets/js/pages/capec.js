import Tags from "/static/assets/node_modules/bootstrap5-tags/tags.js";

let capec_table = undefined;
let default_shown_columns = undefined;
let tags = undefined;

$(window).on('load', function() {

    // Set default shown columns
    if (localStorage.getItem('capec_table_columns') === null) {    
        default_shown_columns = ['Capec ID', 'Name', 'Capec Parents ID', 'Capec Childs ID', 'Abstraction', 'Description', 'Extended Description'];
        localStorage.setItem('capec_table_columns', JSON.stringify(default_shown_columns));
    } else {
        default_shown_columns = JSON.parse(localStorage.getItem('capec_table_columns'));
    }
    
    capec_table = $('#capec_table').DataTable({
        "paging": true,
        "ordering": true,
        "order": [],
        "colReorder": true,
        dom: 'Bfrtip',
        // "orderCellsTop": true,
        "scrollX": true,
        "scrollY": "50vh",
        "scrollCollapse": true,
        searchPane: true,
        fixedColumns: {
            left: 1
        },
        columnDefs: [
            {
                targets: 0,
                className: 'noVis'
            },
            {
                targets: [0, 1, 2, 3, 4, 5, 6, 7, 8, 10, 11, 12, 13, 15, 16, 17, 19, 20, 21, 22, 23, 25, 26, 27],
                searchPanes: {
                    show: false,
                },
            },
            {
                targets: [9, 14, 18, 24],
                searchPanes: {
                    show: true,
                },
            },
        ],
        lengthMenu: [
            [ 10, 25, 50, -1 ],
            [ '10 rows', '25 rows', '50 rows', 'Show all' ]
        ],
        buttons: [
            {
                extend: 'colvis',
                columns: ':not(.noVis)'
            },
            'pageLength',
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
    capec_table.settings()[0].aoColumns.forEach(function(column) {
        column.sName = column.sTitle;
    });
    
    // Replace Capec IDs with buttons
    replaceIDWithButton(capec_table);

    capec_table.on('column-reorder', function (e, settings, details) {
        replaceIDWithButton(capec_table);
    });

    // Save column visibility state
    capec_table.on('column-visibility.dt', function (e, settings, column, state) {
        if (state) {
            default_shown_columns.push(settings.aoColumns[column].sTitle);
        } else {
            default_shown_columns = default_shown_columns.filter(function(value, index, arr){ return value != settings.aoColumns[column].sTitle;});
        }
        localStorage.setItem('capec_table_columns', JSON.stringify(default_shown_columns));
    });

    // Add tags
    Tags.init("#tags-input");

    tags = Tags.getInstance(document.querySelector("#tags-input"));
    tags.setConfig("onCreateItem", function (item) {
        console.log(item.innerHTML);
    });
});

function replaceIDWithButton(table) {
    table.column('Capec ID:name').nodes().each(function (cell, i) {
        let id = cell.innerHTML;

        let parent = document.createElement('h3');
        cell.replaceChildren(parent);
        cell.addEventListener('click', () => {
            window.location.href = '/capec-detail?id=' + id;
        });
        cell.style = 'cursor: pointer;';
        
        let new_content = document.createElement('span');
        new_content.innerHTML = id;
        new_content.className = 'badge bg-primary';
        parent.replaceChildren(new_content);
    });

    ["Capec Parents ID", "Capec Childs ID", 'Peer Of Refs'].forEach(element => {
        table.column(element +':name').nodes().each(function (cell, i) {
            let content = cell.innerHTML;
            if (content != "None") {
                let data = JSON.parse(content);
                let parent = document.createElement('h4');
                cell.replaceChildren(parent);
                let badges = [];
                for(const element of data) {
                    let badge = document.createElement('span');
                    badge.innerHTML = element;
                    badge.className = 'badge bg-primary';
                    badge.style = 'margin-right: 5px; cursor: pointer;';
                    badge.addEventListener('click', () => {
                        window.location.href = '/capec-detail?id=' + element;
                    });
                    badges.push(badge);
                }
                parent.replaceChildren(...badges);
            }
        });
    });
}

$(document).ready(function() {

    function searchIDQuery () {
        console.log("Searching for " + $('#SearchID').val());
        if ($('#SearchID').val() === '') {
            capec_table.search('').columns().search('').draw();
            return;
        }
        $.ajax({
            url: '/capec',
            type: 'POST',
            data: {
                'SearchID': $('#SearchID').val(),
                'ShowTree': $('#ShowTreeToggle').hasClass('active')
            },
            success: function(response) {
                let ids = response.childs.toString().split(',');
                ids = ids.map(function(id) { return '^' + id + '$'; }).join('|');
                capec_table.column(0).search(ids, true, false).draw();
                console.log(response);
            },
            error: function(error) {
                console.log(error);
            }
        });
    };
    
    $('#SearchIDButton').on('click', searchIDQuery);

    $("#ShowTreeToggle").on('click', searchIDQuery);

    $('#ResetIDButton').on('click', function() {
        console.log("Resetting filters");
        $('#SearchID').val('');
        capec_table.search('').columns().search('').draw();
    });
    
    $('#SearchID').on('keyup', function(e) {
        searchIDQuery();
    });
    
    $('#ResetTagButton').on('click', function() {
        console.log("Resetting tags");
        tags.removeAll();
    });

});
