var inspector;
const MACM_LOCAL_STORAGE_KEY = 'macmDiagramCurrent';
let autoSaveTimeout = null;

function init() {
    myDiagram = new go.Diagram('macmDiagramDiv', {
        'undoManager.isEnabled': true, // enable undo & redo
        'themeManager.changesDivBackground': true,
        'themeManager.currentTheme': document.documentElement.getAttribute('data-bs-theme', 'dark'),
        layout: new ContinuousForceDirectedLayout({ // automatically spread nodes apart while dragging
            defaultSpringLength: 200
        }),
        SelectionMoved: e => e.diagram.layout.invalidateLayout()
    });

    // dragging a node invalidates the Diagram.layout, causing a layout during the drag
    myDiagram.toolManager.draggingTool.doMouseMove = function () {
      // method override must be function, not =>
        go.DraggingTool.prototype.doMouseMove.call(this);
        if (this.isActive) this.diagram.layout.doLayout(this.diagram);
    };

    // A custom function to generate unique positive keys
    myDiagram.model = new go.GraphLinksModel({
        makeUniqueKeyFunction: function() {
            let k = 1; 
            while (myDiagram.model.findNodeDataForKey(k)) {
            k++;
            }
            return k;
        },
    });

    // when the document is modified, add a "*" to the title and enable the "Save" button
    myDiagram.addDiagramListener('Modified', e => {
        const button = document.getElementById('SaveButton');
        if (button) button.disabled = !myDiagram.isModified;
        const idx = document.title.indexOf('*');
        if (myDiagram.isModified) {
            if (idx < 0) document.title += '*';
        } else {
            if (idx >= 0) document.title = document.title.slice(0, idx);
        }
        // Auto-save con debounce quando ci sono modifiche
        scheduleAutoSave();
    });

    myDiagram.addDiagramListener("ChangedSelection", function(diagramEvent) {
        var hh = myDiagram.selection.first();
        if (hh == null) {
            hideInspector();
        } else {
            showInspector();
        }
    });

    myDiagram.contextMenu =
        go.GraphObject.build('ContextMenu')
            .add(
            makeButton('Paste',
                (e, obj) =>
                e.diagram.commandHandler.pasteSelection(
                    e.diagram.toolManager.contextMenuTool.mouseDownPoint
                ),
                o =>
                o.diagram.commandHandler.canPasteSelection(
                    o.diagram.toolManager.contextMenuTool.mouseDownPoint
                )
            ),
            makeButton('Undo',
                (e, obj) => e.diagram.commandHandler.undo(),
                o => o.diagram.commandHandler.canUndo()
            ),
            makeButton('Redo',
                (e, obj) => e.diagram.commandHandler.redo(),
                o => o.diagram.commandHandler.canRedo()
            )
        );

    // set up some colors/fonts for the default ('light') and dark Themes
    myDiagram.themeManager.set('light', {
        colors: {
            text: '#fff',
            bgText: '#000',
            link: '#dcb263',
            linkOver: '#cbd5e1',
            div: '#F2F4F6',
        }
    });

    myDiagram.themeManager.set('dark', {
        colors: {
            text: '#fff',
            bgText: '#fff',
            link: '#fdb71c',
            linkOver: '#475569',
            div: '#1F2937'
        }
    });

    inspector = new Inspector('macmInspectorDiv', myDiagram, {
            // allows for multiple nodes to be inspected at once
            multipleSelection: true,
            // max number of node properties will be shown when multiple selection is true
            showSize: 4,
            // when multipleSelection is true, when showUnionProperties is true it takes the union of properties
            // otherwise it takes the intersection of properties
            showUnionProperties: true,
            // uncomment this line to only inspect the named properties below instead of all properties on each object:
            // includesOwnProperties: false,
            properties: {
                name: { name: "Name", show: Inspector.showIfPresent },
                // key would be automatically added for nodes, but we want to declare it read-only also:
                key: { name:"ID", readOnly: true, show: Inspector.showIfPresent },
                // color would be automatically added for nodes, but we want to declare it a color also:
                color: { show: false, type: 'color' },
                type: { name:'Type', show: Inspector.showIfPresent, readOnly: true },
                from: { name:'From', readOnly: true, show: Inspector.showIfPresent },
                to: { name:'To', readOnly: true, show: Inspector.showIfPresent},
                background_color: { show: false, type: 'color'},
                description: { show: false },
                primary_label: { name: "Primary Label", readOnly: true, show: Inspector.showIfPresent },
                secondary_label: { name: "Secondary Label", readOnly: true, show: Inspector.showIfPresent }
            }
        });

    const myOverview = new go.Overview('macmOverviewDiv', {
        observed: myDiagram,
        contentAlignment: go.Spot.Center
    });

    var partContextMenu =
        go.GraphObject.build('ContextMenu')
            .add(
            makeButton('Properties',
                (e, obj) => {
                // OBJ is this Button
                var contextmenu = obj.part; // the Button is in the context menu Adornment
                var part = contextmenu.adornedPart; // the adornedPart is the Part that the context menu adorns
                // now can do something with PART, or with its data, or with the Adornment (the context menu)
                if (part instanceof go.Link) alert(linkInfo(part.data));
                else alert(nodeInfo(part.data));
                }),
            makeButton('Cut',
                (e, obj) => e.diagram.commandHandler.cutSelection(),
                o => o.diagram.commandHandler.canCutSelection()
            ),
            makeButton('Copy',
                (e, obj) => e.diagram.commandHandler.copySelection(),
                o => o.diagram.commandHandler.canCopySelection()
            ),
            makeButton('Paste',
                (e, obj) =>
                e.diagram.commandHandler.pasteSelection(
                    e.diagram.toolManager.contextMenuTool.mouseDownPoint
                ),
                o =>
                o.diagram.commandHandler.canPasteSelection(
                    o.diagram.toolManager.contextMenuTool.mouseDownPoint
                )
            ),
            makeButton('Delete',
                (e, obj) => e.diagram.commandHandler.deleteSelection(),
                o => o.diagram.commandHandler.canDeleteSelection()
            ),
            makeButton('Undo',
                (e, obj) => e.diagram.commandHandler.undo(),
                o => o.diagram.commandHandler.canUndo()
            ),
            makeButton('Redo',
                (e, obj) => e.diagram.commandHandler.redo(),
                o => o.diagram.commandHandler.canRedo()
            ),
            makeButton('Group',
                (e, obj) => e.diagram.commandHandler.groupSelection(),
                o => o.diagram.commandHandler.canGroupSelection()
            ),
            makeButton('Ungroup',
                (e, obj) => e.diagram.commandHandler.ungroupSelection(),
                o => o.diagram.commandHandler.canUngroupSelection()
            )
        );

    // define the Node templates for regular nodes
    myDiagram.nodeTemplateMap.add('', // the default category
        new go.Node('Auto',
            {
                contextMenu: partContextMenu,
                toolTip:
                    go.GraphObject.build('ToolTip')
                        .add(
                            new go.TextBlock({ margin: 4 })
                            .bind('text', '', nodeInfo)
                        ),
                mouseEnter: (e, node) => showSmallPorts(node, true),
                mouseLeave: (e, node) => showSmallPorts(node, false)
            })
            .apply(nodeStyle)
            .add(
                new go.Shape('RoundedRectangle', {
                    name: 'BODY',
                    fromLinkable: true,
                    toLinkable: true,
                    // fromSpot: go.Spot.AllSides,
                    // toSpot: go.Spot.AllSides,
                })
                .apply(shapeStyle)
                .bind('fill', 'background_color', c => c || myDiagram.themeManager.findValue('background', 'colors')),
                new go.Panel('Vertical').add(
                    new go.TextBlock({
                        margin: new go.Margin(12, 12, 4, 12),
                        maxSize: new go.Size(160, NaN),
                        wrap: go.Wrap.Fit,
                        editable: true,
                        isMultiline: false
                        })
                        .apply(nodeTextStyle)
                        .bind('stroke', 'color')
                        .bindTwoWay('text', 'name'),
                    new go.TextBlock({
                        font: '6pt Figtree, sans-serif',
                        editable: false,
                        isMultiline: false
                        })
                        .apply(nodeAssetTypeStyle)
                        .bind('stroke', 'color')
                        .bindTwoWay('text', 'type')
                ),
                makePort('T', go.Spot.Top, false, true),
                makePort('L', go.Spot.Left, true, true),
                makePort('R', go.Spot.Right, true, true),
                makePort('B', go.Spot.Bottom, true, false)
            ),
    );
    
    const paletteTemplate = new go.Map();
    paletteTemplate.add('',
        new go.Node('Auto')
            .apply(nodeStyle)
            .add(
            new go.Shape('RoundedRectangle', {
                name: 'BODY',
                fromLinkable: true,
                toLinkable: true,
                fromSpot: go.Spot.AllSides,
                toSpot: go.Spot.AllSides,
                toolTip:
                    go.GraphObject.build('ToolTip')
                        .add(
                        new go.TextBlock({ margin: 4 })
                        .bind('text', '', paletteNodeInfo)
                    ),
            })
            .apply(shapeStyle)
            // Se presente data.color usa quello, altrimenti fallback al tema
            .bind('fill', 'background_color', c => c || myDiagram.themeManager.findValue('background', 'colors')),
            new go.Panel('Vertical').add(
                new go.TextBlock({
                    margin: 5,
                    editable: false,
                    isMultiline: false
                    })
                    .apply(paletteAssetTypeStyle)
                    .bind('stroke', 'color')
                    .bindTwoWay('text', 'type')
                )
            )
        );
    // replace the default Link template in the linkTemplateMap
    myDiagram.linkTemplate =
        new go.Link({
            routing: go.Routing.AvoidsNodes,
            curve: go.Curve.JumpOver,
            corner: 5,
            toShortLength: 4,
            relinkableFrom: true,
            relinkableTo: true,
            reshapable: true,
            resegmentable: true,
            contextMenu: partContextMenu,
            toolTip:
                go.GraphObject.build('ToolTip')
                    .add(
                    new go.TextBlock({ margin: 4 }) // the tooltip shows the result of calling linkInfo(data)
                        .bind('text', '', linkInfo)
                ),
            // mouse-overs subtly highlight links:
            mouseEnter: (e, link) => (link.findObject('HIGHLIGHT').stroke = link.diagram.themeManager.findValue('linkOver', 'colors')),
            mouseLeave: (e, link) => (link.findObject('HIGHLIGHT').stroke = 'transparent'),
            // context-click creates an editable link label
            click: (e, link) => {
                e.diagram.model.commit(m => {
                    if (!link.data.type)
                        m.set(link.data, 'type', 'No Type');
                });
            }
            })
            // .bindTwoWay('points')
            .add(
            // the highlight shape, normally transparent
            new go.Shape({
                isPanelMain: true,
                strokeWidth: 8,
                stroke: 'transparent',
                name: 'HIGHLIGHT'
            }),
            // the link path shape
            new go.Shape({ isPanelMain: true, strokeWidth: 2 })
                .theme('stroke', 'link'),
            // the arrowhead
            new go.Shape({ toArrow: 'standard', strokeWidth: 0, scale: 1.5 })
                .theme('fill', 'link'),
            // the link label
            new go.Panel('Auto', { visible: false })
                .bind('visible', 'type', t => typeof t === 'string' && t.length > 0) // only shown if there is text
                .add(
                // a gradient that fades into the background
                new go.Shape('Ellipse', { strokeWidth: 0 })
                    .theme('fill', 'div', null, null, c => new go.Brush("Radial", { 0: c, 0.5: `${c}00` })),
                new go.TextBlock({
                    name: 'LABEL',
                    margin: 3,
                    editable: true,
                    textEditor: window.TextEditorSelectBox,
                    choices: ['No Type', 'uses', 'connects', 'hosts', 'interacts', 'provides']
                    })
                    .apply(linkTextStyle)
                    .bindTwoWay('text', 'type')
                )
        );

    // temporary links used by LinkingTool and RelinkingTool are also orthogonal:
    myDiagram.toolManager.linkingTool.temporaryLink.routing = go.Routing.Orthogonal;
    myDiagram.toolManager.relinkingTool.temporaryLink.routing = go.Routing.Orthogonal;
    // Imposta il dato archetipo dei nuovi link: avranno "No Type" di default
    myDiagram.toolManager.linkingTool.archetypeLinkData = { type: 'No Type' };
    // Uniforma eventuali link esistenti privi di type
    myDiagram.model.commit(m => {
        m.linkDataArray.forEach(ld => { if (!ld.type) m.set(ld, 'type', 'No Type'); });
    }, 'Set default link type');


    // initialize the Palette that is on the left side of the page
    // asset_types è un oggetto { id: { name, description, primary_label, secondary_label, color } }
    // Genera un nodo per ogni tipo di asset con nome e colore corretti
    const paletteNodes = Object.values(asset_types).map(at => ({
        name: at.name,
        type: at.name,
        primary_label: at.primary_label,
        secondary_label: at.secondary_label,
        description: at.description,
        background_color: at.color,
        color: getTextColor(at.color)
    }));
    
    // Raggruppa gli asset types per primary_label
    const groupedByLabel = {};
    paletteNodes.forEach(node => {
        const label = node.primary_label || 'Other';
        if (!groupedByLabel[label]) {
            groupedByLabel[label] = [];
        }
        groupedByLabel[label].push(node);
    });

    // Crea le palette per ogni primary_label
    window.palettes = {};
    const labels = Object.keys(groupedByLabel).sort();
    const paletteDiv = document.getElementById('macmPaletteDiv');
    
    labels.forEach((label, index) => {
        // Crea l'item dell'accordion
        const accordionItem = document.createElement('div');
        accordionItem.className = 'macm-accordion-item' + (index === 0 ? ' active' : '');
        
        // Crea la tab (sempre visibile)
        const tab = document.createElement('div');
        tab.className = 'macm-palette-tab';
        tab.textContent = label;
        tab.onclick = () => switchPaletteTab(label);
        
        // Crea il contenuto della palette
        const paletteId = `macmPaletteDiv_${label.replace(/\s+/g, '_')}`;
        const paletteContent = document.createElement('div');
        paletteContent.className = 'macm-palette-content';
        paletteContent.id = paletteId;
        
        accordionItem.appendChild(tab);
        accordionItem.appendChild(paletteContent);
        paletteDiv.appendChild(accordionItem);
    });
    
    // Inizializza le palette GoJS
    setTimeout(() => {
        labels.forEach((label, index) => {
            const paletteId = `macmPaletteDiv_${label.replace(/\s+/g, '_')}`;
            const paletteDiv = document.getElementById(paletteId);
            
            if (!paletteDiv) {
                console.error(`Palette div not found: ${paletteId}`);
                return;
            }
            
            const rect = paletteDiv.getBoundingClientRect();
            
            try {
                window.palettes[label] = new go.Palette(paletteId, {
                    nodeTemplateMap: paletteTemplate,
                    themeManager: myDiagram.themeManager,
                    padding: 20,
                    allowZoom: false,
                    model: new go.GraphLinksModel(groupedByLabel[label])
                });
            } catch (error) {
                console.error(`Error initializing palette ${label}:`, error);
            }
        });
    }, 100);

    // Carica automaticamente il diagramma se presente in localStorage
    load();
}

function nodeInfo(d) {
        var str = 'Asset ' + d.key + '\n'
        str += 'Name: ' + d.name + '\n';
        if (d.type) str += 'Asset Type: ' + d.type;
        return str;
    }

function paletteNodeInfo(d) {
    var str = 'Asset Type: ' + d.type + '\n';
    if (d.primary_label) str += 'Primary Label: ' + d.primary_label + '\n';
    if (d.secondary_label) str += 'Secondary Label: ' + d.secondary_label + '\n';
    if (d.description) str += 'Description: ' + d.description + '\n';
    return str;
}

function linkInfo(d) {
    var str = 'Relationship:\n';
    if (d.type)
        str += 'Type: ' + d.type + '\n';
    str += 'from ' + d.from + ' to ' + d.to;;
    return str;
}

// helper definitions for node templates
function nodeStyle(node) {
    node
        // the Node.location is at the center of each node
        .set({ locationSpot: go.Spot.Center })
        // The Node.location comes from the "loc" property of the node data,
        // converted by the Point.parse static method.
        // If the Node.location is changed, it updates the "loc" property of the node data,
        // converting back using the Point.stringify static method.
        // .bindTwoWay('location', 'loc', go.Point.parse, go.Point.stringify);
}

function shapeStyle(shape) {
    shape.set({ strokeWidth: 0, portId: '', cursor: 'pointer' });
}

function nodeTextStyle(textblock) {
    textblock.set({ font: 'bold 11pt Figtree, sans-serif' })
}

function nodeAssetTypeStyle(textblock) {
    textblock.set({ font: '8pt Figtree, sans-serif' })
}

function paletteAssetTypeStyle(textblock) {
    textblock.set({ font: '11pt Figtree, sans-serif' })
}

function linkTextStyle(textblock) {
    textblock
        .set({ font: 'italic 9pt Figtree, sans-serif'})
        .theme('stroke', 'bgText');
}

function makeButton(text, action, visiblePredicate) {
    const button =
        go.GraphObject.build('ContextMenuButton')
        .add(new go.TextBlock(text, { click: action }));
    // don't bother with binding GraphObject.visible if there's no predicate
    if (visiblePredicate) {
        button.bindObject('visible', '', (o, e) => o.diagram ? visiblePredicate(o, e) : false);
    }
    return button;
}

function makePort(name, spot, output, input) {
      // the port is basically just a small transparent circle
    return new go.Shape('Circle', {
        fill: null, // not seen, by default; set to a translucent gray by showSmallPorts, defined below
        stroke: null,
        desiredSize: new go.Size(7, 7),
        alignment: spot, // align the port on the main Shape
        alignmentFocus: spot, // just inside the Shape
        portId: name, // declare this object to be a "port"
        fromSpot: spot,
        toSpot: spot, // declare where links may connect at this port
        fromLinkable: output,
        toLinkable: input, // declare whether the user may draw links to/from here
        cursor: 'pointer', // show a different cursor to indicate potential link point
    });
}

function showSmallPorts(node, show) {
    node.ports.each(port => {
        if (port.portId !== '') {
            port.fill = show ? 'rgba(0,0,0,.3)' : null;
        }
    });
}

function confirmClearDiagram() {
    $('#deleteName').text("the entire diagram");
    $('#deleteConfirm').click(clearDiagram);
    $('#deleteModal').modal('show');
}

function clearDiagram() {
    myDiagram.startTransaction('clear diagram');
    myDiagram.clear();
    hideInspector();
    save();
    myDiagram.commitTransaction('clear diagram');
    $('#deleteModal').modal('hide');
}

// Debounce per auto-save
function scheduleAutoSave() {
    if (autoSaveTimeout) clearTimeout(autoSaveTimeout);
    autoSaveTimeout = setTimeout(() => {
        if (myDiagram && myDiagram.isModified) {
            save();
        }
    }, 800); // 800ms di inattività prima del salvataggio
}

// Salva lo stato corrente del diagramma in localStorage
function save() {
    if (!myDiagram) return;
    try {
        const json = myDiagram.model.toJson();
        localStorage.setItem(MACM_LOCAL_STORAGE_KEY, json);
        // Reset stato modificato
        myDiagram.isModified = false;
        const button = document.getElementById('SaveButton');
        if (button) button.disabled = true;
        console.log('[MACM] Diagramma salvato in localStorage');
    } catch (err) {
        console.error('[MACM] Errore salvataggio diagramma:', err);
    }
}

// Carica lo stato del diagramma da localStorage (se presente)
function load() {
    if (!myDiagram) return;
    try {
        const json = localStorage.getItem(MACM_LOCAL_STORAGE_KEY);
        if (!json) {
            console.log('[MACM] Nessun diagramma salvato trovato');
            return;
        }
        const model = go.Model.fromJson(json);
        // Reinserisce la funzione di key unica (persa nel fromJson)
        if (model instanceof go.GraphLinksModel) {
            model.makeUniqueKeyFunction = function() {
                let k = 1;
                while (model.findNodeDataForKey(k)) k++;
                return k;
            };
        }
        myDiagram.model = model;
        // Assicura che ogni link abbia almeno il type di default
        myDiagram.model.commit(m => {
            m.linkDataArray.forEach(ld => { if (!ld.type) m.set(ld, 'type', 'No Type'); });
        }, 'Normalize link types after load');
        myDiagram.isModified = false;
        const button = document.getElementById('SaveButton');
        if (button) button.disabled = true;
        console.log('[MACM] Diagramma caricato da localStorage');
    } catch (err) {
        console.error('[MACM] Errore caricamento diagramma:', err);
    }
}

// Rimuove il diagramma salvato (utility opzionale)
function removeSavedDiagram() {
    localStorage.removeItem(MACM_LOCAL_STORAGE_KEY);
    console.log('[MACM] Diagramma salvato rimosso');
}

  // print the diagram by opening a new window holding SVG images of the diagram contents for each page
function printDiagram() {
    const svgWindow = window.open();
    if (!svgWindow) return; // failure to open a new Window
    svgWindow.document.title = "GoJS Flowchart";
    svgWindow.document.body.style.margin = "0px";
    const printSize = new go.Size(700, 960);
    const bnds = myDiagram.documentBounds;
    let x = bnds.x;
    let y = bnds.y;
    while (y < bnds.bottom) {
    while (x < bnds.right) {
        const svg = myDiagram.makeSvg({
        scale: 1.0,
        position: new go.Point(x, y),
        size: printSize,
        background: myDiagram.themeManager.findValue('div', 'colors')
        });
        svgWindow.document.body.appendChild(svg);
        x += printSize.width;
    }
    x = bnds.x;
    y += printSize.height;
    }
    setTimeout(() => { svgWindow.print(); svgWindow.close(); }, 1);
}

function changeTheme() {
    const myDiagram = go.Diagram.fromDiv('macmDiagramDiv');
    console.log("Changing theme");
    if (myDiagram) {
        myDiagram.themeManager.currentTheme = document.documentElement.getAttribute('data-bs-theme', 'dark')
    }
}

function showInspector() {
    const el = document.getElementById('macmInspectorDiv');
    if (el && el.classList.contains('is-visible')) return;
    el.classList.remove('is-hidden', 'exit-right', 'is-visible');
    void el.offsetWidth;
    requestAnimationFrame(() => {
        el.classList.add('is-visible');
        el.addEventListener('transitionend', function onTransitionEnd() {
            const inspectorWidth = el.offsetWidth;
            document.documentElement.style.setProperty('--macm-inspector-width', `${inspectorWidth}px`);
            el.removeEventListener('transitionend', onTransitionEnd);
        }, { once: true });
    });
}

function hideInspector() {
    const el = document.getElementById('macmInspectorDiv');
    if (el && el.classList.contains('is-hidden')) return;
    // Resetta subito la larghezza a 0 per far ricalcolare la palette
    document.documentElement.style.setProperty('--macm-inspector-width', '0px');
    el.classList.add('exit-right');
    el.addEventListener('transitionend', function onEnd() {
        el.classList.remove('is-visible');
        el.classList.add('is-hidden');
        el.removeEventListener('transitionend', onEnd);
    }, { once: true });
}

function getCypher() {
    var jsonDiagram = myDiagram.model.toJson();
    jsonDiagram = JSON.parse(jsonDiagram);
    console.log(jsonDiagram);
    nodeArray = jsonDiagram.nodeDataArray;
    linkArray = jsonDiagram.linkDataArray;
    if (nodeArray.length === 0 && linkArray.length === 0)
        return null;
    cypherQuery = "CREATE \n";
    try {
        for (const node of nodeArray) {
            cypherQuery += `(Node${node.key}:${node.primary_label}`
            if (node.secondary_label)
                cypherQuery += `:${node.secondary_label}`
            cypherQuery += ` {name:"${node.name}", component_id:"${node.key}", type:"${node.type}"}),\n`;
        }
        for (const link of linkArray) {
            if (!link.type || link.type === 'No Type'){
                throw new Error(`Link from Node ${nodeArray[link.from-1].name} to Node ${nodeArray[link.to-1].name} has no type defined.`);
            }
            cypherQuery += `(Node${link.from})-[:${link.type}]->(Node${link.to}),\n`;
        }
        // remove the last comma and add a semicolon
        cypherQuery = cypherQuery.slice(0, -2);
    }
    catch (error) {
        alert(error);
        return null;
    }
    return cypherQuery;
}

function switchPaletteTab(selectedLabel) {
    // Rimuovi active da tutti gli accordion items
    const allItems = document.querySelectorAll('.macm-accordion-item');
    allItems.forEach(item => item.classList.remove('active'));
    
    // Trova e attiva l'accordion item selezionato
    allItems.forEach(item => {
        const tab = item.querySelector('.macm-palette-tab');
        if (tab && tab.textContent === selectedLabel) {
            item.classList.add('active');
            
            // Forza il ridimensionamento della palette attiva dopo la transizione
            setTimeout(() => {
                if (window.palettes && window.palettes[selectedLabel]) {
                    window.palettes[selectedLabel].requestUpdate();
                }
            }, 320); // Aspetta la fine della transizione (0.3s + buffer)
        }
    });
}

function showC2MModal() {
    let cypher = getCypher();
    if (cypher) {
        $('#modalC2MOutput').text(cypher);
        $('#modalC2MOutputPre').show();
        $('#modalC2MAlert').hide();
        $('#copyC2MOutput').show();
        $('#copyC2MOutput').attr('data-clipboard-text', cypher);
        $('#uploadC2MOutput').show();
        $('#modalC2MacmAppNameGroup').show();
    }
    else {
        $('#modalC2MOutputPre').hide();
        $('#modalC2MAlert').show();
        $('#uploadC2MOutput').hide();
        $('#copyC2MOutput').hide();
        $('#modalC2MacmAppNameGroup').hide();
    }
    $('#modalC2M').modal('show');
    Prism.highlightAll();
}


window.addEventListener('DOMContentLoaded', () => {
    setTimeout(() => {
    init();
    }, 300);
    document.getElementById('DarkMode').addEventListener('click', () => {
        changeTheme();
    });
    $('#saveModelBtn').on('click', () => {
        save();
    });
    $('#loadModelBtn').on('click', () => {
        load();
    });

    $('#uploadC2MOutput').click(function() {
        let uploadButton = $(this);
        uploadButton.addClass('btn-loading');
        let cypher = $('#modalC2MOutput').text();
        let appName = $('#modalC2MacmAppName').val().trim();
        if (cypher) {
            let formData = new FormData();
            formData.append('macmAppName', appName);
            formData.append('macmCypher', cypher);
            $.ajax({
                url: '/api/upload_macm',
                type: 'POST',
                data: formData,
                processData: false,
                contentType: false
            }).done(function(response) {
                location.reload();
            }).fail(function(response) {
                uploadButton.removeClass('btn-loading');
                $('#modalC2M').modal('hide');
                showModal("Upload failed", JSON.parse(response.responseText));
            });
        }
    });
});