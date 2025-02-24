var driver = neo4j.driver(
    neo4j_params.uri,
    neo4j.auth.basic(neo4j_params.user, neo4j_params.password)
);

const session = driver.session({ database: app_id });


var new_nodes = [];
var new_links = [];

session
    .run('MATCH (a)-[b]->(c) RETURN a, b, c')
    .then(function (result) {
        result.records.forEach(function (record) {
            var node_1 = record._fields[0].properties;
            var node_2 = record._fields[2].properties;
            var new_node_1 = {
                data: {
                    id: node_1.component_id,
                    label: node_1.name,
                    type: node_1.type,
                },
            };
            var new_node_2 = {
                data: {
                    id: node_2.component_id,
                    label: node_2.name,
                    type: node_2.type,
                },
            };
            var new_link = {
                data: {
                    label: record._fields[1].type,
                    source: node_1.component_id,
                    target: node_2.component_id,
                    color_link: "blue",
                    color_text: "white",
                },
            };
            new_nodes.push(new_node_1);
            new_nodes.push(new_node_2);
            new_links.push(new_link);
        });
    })
    .then(function () {
        session.close();
        driver.close();

        // define general dagre layout
        var layout = {
            name: "spread",
            rankDir: "LR",
            align: 'LR',
            animate: true,
            nodeDimensionsIncludeLabels: true,
            padding: 35,
            rankSep: 250,
            nodeSep: 20,
        };

        // define expandCollapse layout
        var cy = (window.cy = cytoscape({
            container: document.getElementById("cy"),

            boxSelectionEnabled: true,
            autounselectify: true,

            layout: layout,

            style: [
                {
                    selector: "node",
                    style: {
                        "content": "data(label)",
                        "text-valign": "center",
                        "text-halign": "center",
                        "height": "110px",
                        "width": "110px",
                        // "background-color": "data(color_node)",
                        "color": "#FFFFFF",
                        "font-family": "Georgia, serif",
                        "font-size": "14px",
                    }
                },
                {
                    selector: "edge",
                    style: {
                        "content": "data(label)",
                        "curve-style": "bezier",
                        "control-point-weight": 0.5,
                        "edge-distances": "node-position",
                        width: 2,
                        "target-arrow-shape": "triangle",
                        "line-color": "data(color_link)",
                        "target-arrow-color": "data(color_link)",
                        "color": "data(color_text)",
                    }
                }
            ],
            elements: {
                nodes: new_nodes,
                edges: new_links
            },
        }));

        

        for (let [key, value] of Object.entries(styles)) {
            cy.style().selector(`node.${key}`).style(value);
        }

        cy.nodes().forEach(node => {
            node.addClass(node.data().type.replace('.', '_'));
        });

        // add event listeners for zooming in and out
        document.getElementById("zoom-in").addEventListener("click", function () {
            cy.zoom({
                level: cy.zoom() * 1.5,
                renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
            });
        });

        document.getElementById("zoom-out").addEventListener("click", function () {
            cy.zoom({
                level: cy.zoom() * 0.5,
                renderedPosition: { x: cy.width() / 2, y: cy.height() / 2 }
            });
        });

        // add click event listener for nodes
        cy.on("tap", "node", function () {
            let node = this;
            let children = node.outgoers("node");

            if (children.length > 0) {
                for (let i = 0; i < children.length; i++) {
                    // If the node has children
                    if (children[i].visible()) {
                        // If children are visible, hide them
                        children[i].hide();
                        let grand_children = children[i].outgoers("node");
                        grand_children.hide();
                    } else {
                        // If children are hidden, show them
                        children[i].show();
                        let grand_children = children[i].outgoers("node");
                        grand_children.show();
                    }
                }
                // Run layout again to update positions
                cy.layout(layout).run();
            }
        });

        // create the popper for the node
        function create_popper_content(ele) {
            var d = ele.data();
            if (d.lastName == "YOU") {
                return `
                    <div class="en-card" >
                            <div class="en-card-header" style= 'border: 1px solid #D3D6DA !important; border-radius: 5px;
                            padding: 6px;padding-right: 10px;opacity:1;
                            background: white;'>
                                <span style="color:#48558A;font-size:14px;">
                                <span> ${d.id} </span>
                                </span>         
                                
                    </div>
                    `
            } else {
                return `
                    <div class="en-card" style='padding: 6px; margin-right: 8px; border: 1px solid #D3D6DA; background: white; border-radius: 5px;'>
                            <div class="en-card-header">
                                <span style="color:#48558A;font-size:14px;">
                                <span> ${d.id} </span>
                                </span>         
                                
                    </div>
                `
            }
        }


        // use tippy for hovering over the node
        function makePopper(ele) {
            let ref = ele.popperRef();

            ele.tippy = tippy(document.createElement('div'), {
                getReferenceClientRect: ref.getBoundingClientRect,
                content: () => {
                    let content = document.createElement('div');
                    content.innerHTML = create_popper_content(ele);
                    return content;
                },
                onHidden(instance) {
                    instance.destroy();
                },
                interactive: true,
                appendTo: document.body // or append dummyDomEle to document.body
            });
            ele.tippy.show();
            ele.on('mouseout', function (e) {
                setTimeout(function () {
                    ele.tippy.hide();
                }, 100);
            });
        }

        cy.on('mouseover', 'node', function (e) {
            makePopper(e.target);
        });



        // use changeDir button to change the direction of the graph
        var currentDir = null;
        var changeDir = document.getElementById("changeDir");
        changeDir.addEventListener("click", function () {
            // check if we already have a direction
            if (currentDir === null) {
                currentDir = cy.options().layout.rankDir;
            }
            // change the direction
            var newDir = currentDir === "LR" ? "UD" : "LR";
            // update the layout
            layout = {
                name: "spread",
                rankDir: newDir,
                align: 'LR',
                animate: true,
                nodeDimensionsIncludeLabels: true,
                padding: 35,
                rankSep: 250,
                nodeSep: 10,
            };

            cy.layout(layout).run();

            // update the button text
            changeDir.innerHTML = "Change direction to " + currentDir;

            // keep the newDir for next time
            currentDir = newDir;

        });
    });