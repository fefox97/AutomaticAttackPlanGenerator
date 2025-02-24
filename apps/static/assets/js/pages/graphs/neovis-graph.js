let neoVizGraph;
let neoVizSchema;
var activeTab;

$(window).on('load', function() {
    // Draw Neo4j with NeoVis
    drawNeo4j(app_id);

    neoVizGraph.registerOnEvent("completed", () => {
        $("#saveImage").prop("disabled", false);
        $("#centerNetwork").prop("disabled", false);
    });
    
    neoVizSchema.registerOnEvent("completed", () => {
        $("#saveImage").prop("disabled", false);
        $("#centerNetwork").prop("disabled", false);
    });

    const tabList = document.querySelectorAll('#graph-tabs button')
    tabList.forEach(tabEl => {
        activeTab = tabEl.ariaSelected === 'true' ? tabEl.id : activeTab;
        tabEl.addEventListener('click', event => {
            activeTab = event.target.id;
        })
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

    const savePopover = new bootstrap.Popover(document.getElementById("saveImage"), {
        html: true,
        content: "<div class='d-flex align-items-center justify-content-center'><a id='saveConfirm' role='button' class='btn btn-secondary'>Save</a></div>",
        title: 'Do you want to save the image?',
        placement: "top",
        trigger: "click",
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

});

function drawNeo4j(database) {
    const configGraph = {
        containerId: "graph",
        serverDatabase: database,
        consoleDebug: false,
        neo4j: {
            serverUrl: neo4j_params.uri,
            serverUser: neo4j_params.user,
            serverPassword: neo4j_params.password,
            driverConfig: {
                encrypted: neo4j_params.encrypted,
                trust: "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
            },
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
                    theta: 0.1,
                    gravitationalConstant: -4000,
                    centralGravity: 0.5,
                    springLength: 150,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.5
                },
                minVelocity: 0.75,
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
        initialCypher: `
                        MATCH (a)
                        OPTIONAL MATCH (a)-[b]->(c)
                        RETURN a,b,c
                        `
    };

    const configSchema = {
        containerId: "schema",
        serverDatabase: database,
        neo4j: {
            serverUrl: neo4j_params.uri,
            serverUser: neo4j_params.user,
            serverPassword: neo4j_params.password,
            driverConfig: {
                encrypted: neo4j_params.encrypted,
                trust: "TRUST_SYSTEM_CA_SIGNED_CERTIFICATES",
            },
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
                    gravitationalConstant: -4000,
                    centralGravity: 0.5,
                    springLength: 150,
                    springConstant: 0.04,
                    damping: 0.09,
                    avoidOverlap: 0.5
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
