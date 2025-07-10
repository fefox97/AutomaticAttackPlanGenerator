import Tags from "/static/assets/node_modules/bootstrap5-tags/tags.js";

let capec_table = undefined;
let default_shown_columns = undefined;

$(window).on('load', function() {

    // Set default shown columns
    if (localStorage.getItem('capec_table_columns') === null) {    
        default_shown_columns = ['Capec ID', 'Name', 'Capec Parents ID', 'Capec Children ID', 'Abstraction', 'Description', 'Extended Description'];
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
                targets: [0, 1, 3, 4, 5, 6, 7, 8, 9, 10, 12, 13, 14, 15, 16, 17, 18, 19, 21, 22, 23],
                searchPanes: {
                    show: false,
                },
            },
            {
                targets: [2, 11, 20],
                searchPanes: {
                    show: true,
                },
            },
            {
                targets: 2,
                render: function (data, type, row) {
                    if (type === 'sort' || type === 'type') {
                            if (data.includes('Meta')) { return 0; }
                            else if (data.includes('Standard')) { return 1; }
                            else { return 2; }
                    }
                    return data;
                }   
            }
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

    // Save column visibility state
    capec_table.on('column-visibility.dt', function (e, settings, column, state) {
        if (state) {
            default_shown_columns.push(settings.aoColumns[column].sTitle);
        } else {
            default_shown_columns = default_shown_columns.filter(function(value, index, arr){ return value != settings.aoColumns[column].sTitle;});
        }
        localStorage.setItem('capec_table_columns', JSON.stringify(default_shown_columns));
    });
});

$(document).ready(function() {
    
    $('#SearchIDButton').on('click', searchIDQuery);

    $("#ShowTreeToggle").on('click', searchIDQuery);

    $('#ResetIDButton').on('click', function() {
        $('#SearchID').val('');
        capec_table.search('').columns().search('').draw();
    });
    
    $('#SearchID').on('keyup', function(e) {
        searchIDQuery();
    });

    // Add tags
    Tags.init("#tags-input");
    $("#tags-input").on("change", function (event) {
        searchKeywordQuery();
    });
    
    let tags = Tags.getInstance(document.querySelector("#tags-input"));
    $('#ResetTagButton').on('click', function() {
        tags.removeAll();
        searchKeywordQuery();
    });

    $('[name="SearchType"]').on('change', function() {
        searchKeywordQuery();
    });
});

function searchIDQuery () {
    if ($('#SearchID').val() === '') {
        capec_table.search('').columns().search('').draw();
        return;
    }
    $.ajax({
        url: '/api/search_capec_by_id',
        type: 'POST',
        data: {
            'SearchID': $('#SearchID').val(),
            'ShowTree': $('#ShowTreeToggle').hasClass('active')
        },
    }).done(function(response) {
        console.log(response);
        let ids = response.children.toString().split(',');
        ids = ids.map(function(id) { return '^' + id + '$'; }).join('|');
        capec_table.column(0).search(ids, true, false).draw();
    }).fail(function(error) {
        showError(error.status, autohide = true);
    });
};

function searchKeywordQuery() {
    let tags = $("#tags-input").val();
    if (tags.length === 0) {
        capec_table.search('').columns().search('').draw();
        return;
    }
    console.log("Searching for " + tags);
    $.ajax({
        url: '/api/search_capec_by_keyword',
        type: 'POST',
        data: {
            'SearchKeyword': JSON.stringify(tags),
            'SearchType': $('[name="SearchType"]:checked').val()
        },
    }).done(function(response) {
        let ids = response.ids;
        ids = ids.map(function(id) { return '^' + id + '$'; }).join('|');
        capec_table.column(0).search(ids, true, false).draw();
    }).fail(function(error) {
        showError(error.status, autohide = true);
    });
}