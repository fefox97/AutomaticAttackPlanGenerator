$(document).ready(function () {
    var driver = neo4j.driver(
        neo4j_params.uri,
        neo4j.auth.basic(neo4j_params.user, neo4j_params.password)
    );

    const session = driver.session({ database: app_id });

    var new_nodes = [];
    var new_links = [];

    session
        .run(`MATCH (a)
            OPTIONAL MATCH (a)-[b]->(c)
            RETURN a, b, c`)
        .then(function (result) {
            result.records.forEach(function (record) {
                var node_1 = record._fields[0].properties;
                var new_node_1 = {
                    data: {
                        id: node_1.component_id,
                        label: node_1.name,
                        type: node_1.type,
                        parameters: node_1.parameters,
                    },
                };
                new_nodes.push(new_node_1);

                if (record._fields[2]) {
                    var node_2 = record._fields[2].properties;
                    var new_node_2 = {
                        data: {
                            id: node_2.component_id,
                            label: node_2.name,
                            type: node_2.type,
                            parameters: node_2.parameters,
                        },
                    };
                    var new_link = {
                        data: {
                            label: record._fields[1].type,
                            source: node_1.component_id,
                            target: node_2.component_id,
                        },
                    };
                    new_nodes.push(new_node_2);
                    new_links.push(new_link);
                }
            });
        })
        .then(function () {
            session.close();
            driver.close();

            // define general dagre layout
            var layout = {
                name: "euler",
                animate: true,
                springLength: 100,
                springCoeff: 0.0008,
                gravity: -2,
                maxIterations: 2000,
                fit: true,
                mass: function (node) {return 25;},
            }
            // var layout = {
            //     name: "cola",
            //     animate: true,
            //     fit: true,
            //     randomize: false,
            //     avoidOverlap: true,
            //     edgeLength: 100,
            //     nodeDimensionsIncludeLabels: true,
            //     padding: 35,
            //     nodeSpacing: function (node) {return 100;},
            // };
            // var layout = {
            //     name: "spread",
            //     rankDir: "LR",
            //     align: 'LR',
            //     animate: true,
            //     nodeDimensionsIncludeLabels: true,
            //     padding: 35,
            //     rankSep: 250,
            //     nodeSep: 10,
            // };

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
                            'content': 'data(label)',
                            'text-valign': 'center',
                            'text-halign': 'center',
                            'height': '100px',
                            'width': '100px',
                            'color': 'black',
                            'fontSize': '14px',
                            'fontWeight': 'bold',
                            'text-wrap': 'wrap',
                            'text-outline-width': 1,
                            'text-outline-color': 'white',
                            'text-max-width': '100px',
                            'border-width': 3,
                            'background-color': '#333333',
                        }
                    },
                    {
                        selector: "edge",
                        style: {
                            'content': 'data(label)',
                            'curve-style': 'bezier',
                            'control-point-weight': 0.5,
                            'edge-distances': 'node-position',
                            'width': 2,
                            'target-arrow-shape': 'triangle',
                            'line-color': 'black',
                            'target-arrow-color': 'black',
                            'color': 'black',
                            'text-outline-width': 1,
                            'text-outline-color': 'white',
                        }
                    }
                ],
                elements: {
                    nodes: new_nodes,
                    edges: new_links
                },
            }));

            for (let [key, value] of Object.entries(asset_types_colors)) {
                cy.style().selector(`node.${key.replace('.','_')}`).style({
                    'background-color': value,
                    'border-color': pSBC(-0.5, value),
                });
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

            document.getElementById("center").addEventListener("click", function () {
                cy.fit();
                cy.center();
            });

            // add click event listener for nodes
            // cy.on("tap", "node", function () {
            //     let node = this;
            //     let children = node.outgoers("node");

            //     if (children.length > 0) {
            //         for (let i = 0; i < children.length; i++) {
            //             // If the node has children
            //             if (children[i].visible()) {
            //                 // If children are visible, hide them
            //                 children[i].hide();
            //                 let grand_children = children[i].outgoers("node");
            //                 grand_children.hide();
            //             } else {
            //                 // If children are hidden, show them
            //                 children[i].show();
            //                 let grand_children = children[i].outgoers("node");
            //                 grand_children.show();
            //             }
            //         }
            //         // Run layout again to update positions
            //         cy.layout(layout).run();
            //     }
            // });

            // create the popper for the node
            function create_popper_content(ele) {
                var d = ele.data();
                if (d.lastName == "YOU") {
                    return `
                        <div class="en-card" >
                                <div class="en-card-header" style='padding: 6px;opacity:1;text-align:center;'>
                                    <span style="color:white;font-size:14px;text-align:center;">
                                        <span> <strong> Asset ${d.id} </strong> </span>
                                        <br>
                                        <span> Name: ${d.label} </span>
                                        <br>
                                        <span> Asset Type: ${d.type} </span>
                                        <br>
                                        <span> Parameters: ${d.parameters ? d.parameters : "No parameters"} </span>
                                    </span>        
                                </div>
                        </div>
                        `
                } else {
                    return `
                        <div class="en-card" style='padding: 6px;'>
                            <div class="en-card-header">
                                    <span style="color:white;font-size:14px;text-align:center;">
                                    <span> <strong> Asset ${d.id} </strong> </span>
                                    <br>
                                    <span> Name: ${d.label} </span>
                                    <br>
                                    <span> Asset Type: ${d.type} </span>
                                    <br>
                                    <span> Parameters: ${d.parameters ? d.parameters : "No parameters"}
                                </span>         
                            </div>
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

        var rearrange = document.getElementById("rearrange");
        rearrange.addEventListener("click", function () {
            var layout = {
                name: "euler",
                animate: true,
                springLength: 100,
                springCoeff: 0.0008,
                gravity: -2,
                maxIterations: 2000,
                fit: true,
                mass: function (node) {return 25;},
            };
            cy.layout(layout).run();
        });

        const initialTheme = document.querySelector('[data-bs-theme]').dataset.bsTheme;
        updateEdgeColors(initialTheme);
    }).catch(function (error) {
        console.log(error);
        session.close();
        driver.close();
    });

    function saveImage2PDF(filename) {
        currentTheme = document.querySelector('[data-bs-theme]').dataset.bsTheme;
        updateEdgeColors('light');
        let svg_image = cy.svg({ scale: 1, full: true });
        const doc = new PDFDocument({ size: [1000, 1000], bufferPages: true });
        SVGtoPDF(doc, svg_image, 0, 0, { preserveAspectRatio: 'xMidYMid meet' });
        const stream = doc.pipe(blobStream());
        stream.on('finish', function () {
            const url = stream.toBlobURL('application/pdf');
            const a = document.createElement('a');
            a.href = url;
            a.download = filename;
            a.click();
        });
        doc.end();
        updateEdgeColors(currentTheme);
    }

    function saveImage2SVG(filename) {
        currentTheme = document.querySelector('[data-bs-theme]').dataset.bsTheme;
        updateEdgeColors('light');
        const svg_image = cy.svg({ scale: 1, full: true });
        const blob = new Blob([svg_image], { type: 'image/svg+xml' });
        const url = URL.createObjectURL(blob);
        const a = document.createElement('a');
        a.href = url;
        a.download = filename;
        a.click();
        updateEdgeColors(currentTheme);
    }

    const savePopover = new bootstrap.Popover(document.getElementById("exportImage"), {
        html: true,
        content: `<div class='d-flex flex-column align-items-center justify-content-center'>
                        <a id='saveConfirmPDF' role='button' class='btn btn-secondary mb-2'>Save PDF</a>
                        <a id='saveConfirmSVG' role='button' class='btn btn-secondary'>Save SVG</a>
                    </div>`,
        title: 'Do you want to save the image?',
        placement: "top",
        trigger: "click",
    });

    savePopover._element.addEventListener("shown.bs.popover", () => {
        $("#saveConfirmPDF").click(() => {
            saveImage2PDF('graph.pdf');
            savePopover.hide();
        });
        $("#saveConfirmSVG").click(() => {
            saveImage2SVG('graph.svg');
            savePopover.hide();
        });
    });

    // Update edge colors based on the theme
    function updateEdgeColors(theme) {
        const edgeColor = theme === 'dark' ? 'white' : 'black';
        cy.style().selector('edge').style({
            'line-color': edgeColor,
            'target-arrow-color': edgeColor,
        }).update();
    }

    document.getElementById('DarkMode').addEventListener('click', () => {
        console.log('DarkMode button clicked');
        const currentTheme = document.querySelector('[data-bs-theme]').dataset.bsTheme;
        updateEdgeColors(currentTheme);
    });

});

