var macm = undefined;
var default_shown_columns = undefined;
let neoVizGraph;
let neoVizSchema;
var activeTab;

$(window).on('load', function() {

    // Draw Neo4j with NeoVis
    drawNeo4j();

    neoVizGraph.registerOnEvent("completed", () => {
        $("#saveImage").prop("disabled", false);
        $("#centerNetwork").prop("disabled", false);
    });
    
    neoVizSchema.registerOnEvent("completed", () => {
        $("#saveImage").prop("disabled", false);
        $("#centerNetwork").prop("disabled", false);
    });
    
    const savePopover = new bootstrap.Popover(document.getElementById("saveImage"), {
        html: true,
        content: "<div class='d-flex align-items-center justify-content-center'><a id='saveConfirm' role='button' class='btn btn-secondary'>Save</a></div>",
        title: 'Do you want to save the image?',
        placement: "top",
        trigger: "click",
    });

    const tabList = document.querySelectorAll('#graph-tabs button')
    tabList.forEach(tabEl => {
        activeTab = tabEl.ariaSelected === 'true' ? tabEl.id : activeTab;
        tabEl.addEventListener('click', event => {
            activeTab = event.target.id;
        })
    });

    savePopover._element.addEventListener("shown.bs.popover", () => {
        $("#saveConfirm").click(() => {
            if (activeTab === 'graph-tab') {
                saveImage(neoVizGraph, "graph.png");
            }
            else if (activeTab === 'schema-tab') {
                saveImage(neoVizSchema, "schema.png");
            }
            savePopover.hide();
        });
    });

    $("#centerNetwork").click(() => {
        if (activeTab === 'graph-tab') {
            neoVizGraph.stabilize();
            neoVizGraph.network.fit();
        }
        else if (activeTab === 'schema-tab') {
            neoVizSchema.stabilize();
            neoVizSchema.network.fit();
        }
    });

    // Set default shown columns
    if (localStorage.getItem('macm_columns') === null) {    
        default_shown_columns = ['Component ID', 'Application', 'Name', 'Type', 'App ID'];
        localStorage.setItem('macm_columns', JSON.stringify(default_shown_columns));
    } else {
        default_shown_columns = JSON.parse(localStorage.getItem('macm_columns'));
    }
    
    macm = $('#macm_table').DataTable({
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
                        return parseInt(data);
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
});

function drawNeo4j() {
    const configGraph = {
        containerId: "graph",
        serverDatabase: "macm",
        neo4j: {
            serverUrl: "bolt://192.168.40.4:7787",
            serverUser: "neo4j",
            serverPassword: "neo4j#1234",
        },
        visConfig: {
            nodes: {
            },
            edges: {
                arrows: {
                    to: {enabled: true}
                },
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.4
                },
                
                solver: 'barnesHut',
                adaptiveTimestep: true,
            },
        },
        labels: {
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
                caption: true,
                label: "name",
                group: "type",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                    cypher: {
                        value: "MATCH (n) WHERE id(n) = $id RETURN n"
                    },
                    function: {
                        title: NeoVis.objectToTitleHtml,
                    },
                }
            },
        },
        relationships: {
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                    function: {
                        label: rel => rel.type,
                        title: (props) => NeoVis.objectToTitleHtml(props),
                    },
                },
            }
        },
        initialCypher: "MATCH (a)-[b]->(c) RETURN a,b,c"
    };

    const configSchema = {
        containerId: "schema",
        serverDatabase: "macm",
        neo4j: {
            serverUrl: "bolt://192.168.40.4:7787",
            serverUser: "neo4j",
            serverPassword: "neo4j#1234",
        },
        visConfig: {
            nodes: {
            },
            edges: {
                arrows: {
                    to: {enabled: true}
                },
            },
            physics: {
                enabled: true,
                barnesHut: {
                    gravitationalConstant: -2000,
                    centralGravity: 0.3,
                    springLength: 95,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.4
                },
                
                solver: 'barnesHut',
                adaptiveTimestep: true,
            },
        },
        labels: {
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
                caption: true,
                label: "name",
                group: "name",
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                    cypher: {
                        value: "MATCH (n) WHERE id(n) = $id RETURN n"
                    },
                    function: {
                        title: NeoVis.objectToTitleHtml,
                    },
                }
            },
        },
        relationships: {
            [NeoVis.NEOVIS_DEFAULT_CONFIG]: {
                [NeoVis.NEOVIS_ADVANCED_CONFIG]: {
                    function: {
                        label: rel => rel.type,
                        title: (props) => NeoVis.objectToTitleHtml(props),
                    },
                },
            }
        },
        initialCypher: "CALL db.schema.visualization()"
    };

    neoVizGraph = new NeoVis.default(configGraph);
    neoVizSchema = new NeoVis.default(configSchema);
    neoVizGraph.render();
    neoVizSchema.render();
}

function saveImage(neoViz, filename) {
    const link = document.createElement("a");
    const data = neoViz.network.canvas.getContext("2d").canvas.toDataURL("image/png");
    link.href = data;
    link.download = filename || "network.png";
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
}
