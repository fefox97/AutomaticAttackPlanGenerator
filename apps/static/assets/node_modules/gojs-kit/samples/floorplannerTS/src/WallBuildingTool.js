/**
 * Copyright 1998-2025 by Northwoods Software Corporation
 * All Rights Reserved.
 *
 * FLOOR PLANNER - WALL BUILDING TOOL
 * Used to construct new Walls in a Floorplan with mouse clicking / mouse point
 */
import * as go from 'gojs';
export class WallBuildingTool extends go.Tool {
    constructor(init) {
        super();
        this._buildingWall = null; // the wall being built
        // whether or not the "wall" we're building is really just a room / floor divider (not a physical wall)
        this._isBuildingDivider = false;
        this.name = 'WallBuilding';
        this._startPoint = null;
        this._endPoint = null;
        this._wallReshapingTool = null;
        this._isBuildingDivider = false;
        if (init)
            Object.assign(this, init);
    }
    // Get / set the current startPoint
    get startPoint() {
        return this._startPoint;
    }
    set startPoint(value) {
        this._startPoint = value;
    }
    // Get / set the current endPoint
    get endPoint() {
        return this._endPoint;
    }
    set endPoint(value) {
        this._endPoint = value;
    }
    // Get / set the floorplan's WallReshapingTool
    get wallReshapingTool() {
        return this._wallReshapingTool;
    }
    set wallReshapingTool(value) {
        this._wallReshapingTool = value;
    }
    // Get / set the wall being built
    get buildingWall() {
        return this._buildingWall;
    }
    set buildingWall(value) {
        this._buildingWall = value;
    }
    // Get / set whether or not we're actually building a room / floor divider, not a wall
    get isBuildingDivider() {
        return this._isBuildingDivider;
    }
    set isBuildingDivider(value) {
        this._isBuildingDivider = value;
    }
    /**
     * Start wall building transaction.
     * If the mouse point is inside a wall or near a wall endpoint, snap to that wall or endpoint
     */
    doActivate() {
        this.endPoint = null;
        this.startTransaction(this.name);
        this.diagram.isMouseCaptured = true;
        const tool = this;
        const fp = tool.diagram;
        let clickPt = tool.diagram.lastInput.documentPoint;
        let isSnapped = false;
        // if the clickPt is inside some other wall's geometry, project it onto that wall's segment
        const walls = fp.findNodesByExample({
            category: 'WallGroup',
        });
        walls.iterator.each(function (w) {
            if (fp.isPointInWall(w, clickPt)) {
                // don't check if you're inside the wall you're building, you obviously are
                if (tool.buildingWall === null) {
                    const snapPt = clickPt.projectOntoLineSegmentPoint(w.data.startpoint, w.data.endpoint);
                    clickPt = snapPt;
                    isSnapped = true;
                }
            }
        });
        // if the click point is close to another wall's start/endpoint, use that as the startpoint of the new wall
        walls.iterator.each(function (w) {
            const sp = w.data.startpoint;
            const ep = w.data.endpoint;
            const distSp = Math.sqrt(sp.distanceSquaredPoint(clickPt));
            // TODO probably need a better "closeness" metric than just a raw number -- it could be an optional parameter?
            if (distSp < 15) {
                clickPt = sp;
                isSnapped = true;
            }
            const distEp = Math.sqrt(ep.distanceSquaredPoint(clickPt));
            if (distEp < 15) {
                clickPt = ep;
                isSnapped = true;
            }
        });
        // assign startpoint based on grid (iff startpoint was not determined by another wall's endpoint)
        if (true) {
            let gs = fp.model.modelData.gridSize;
            if (!tool.diagram.toolManager.draggingTool.isGridSnapEnabled || isSnapped)
                gs = 0.0001;
            const newx = gs * Math.round(clickPt.x / gs);
            const newy = gs * Math.round(clickPt.y / gs);
            clickPt = new go.Point(newx, newy);
        }
        this.startPoint = clickPt;
        this.wallReshapingTool = fp.toolManager.mouseDownTools.elt(3);
        // Default functionality:
        this.isActive = true;
    }
    /**
     * Add wall data to Floorplan and begin reshaping the new wall
     */
    doMouseDown() {
        const diagram = this.diagram;
        const tool = this;
        tool.diagram.currentCursor = 'crosshair';
        const data = {
            key: 'wall',
            category: 'WallGroup',
            caption: tool.isBuildingDivider ? 'Divider' : 'Wall',
            type: tool.isBuildingDivider ? 'Divider' : 'Wall',
            startpoint: tool.startPoint,
            endpoint: tool.startPoint,
            smpt1: tool.startPoint,
            smpt2: tool.startPoint,
            empt1: tool.startPoint,
            empt2: tool.startPoint,
            thickness: tool._isBuildingDivider
                ? 0.005
                : parseFloat(diagram.model.modelData.wallThickness),
            color: 'lightgray',
            isGroup: true,
            notes: '',
            isDivider: tool.isBuildingDivider,
        };
        this.diagram.model.addNodeData(data);
        const wall = diagram.findPartForKey(data.key);
        this.buildingWall = wall;
        const fp = diagram;
        fp.updateWall(wall);
        const part = diagram.findPartForData(data);
        if (part === null)
            return;
        // set the TransactionResult before raising event, in case it changes the result or cancels the tool
        tool.transactionResult = tool.name;
        diagram.raiseDiagramEvent('PartCreated', part);
        if (tool.wallReshapingTool === null)
            return;
        // start the wallReshapingTool, tell it what wall it's reshaping (more accurately, the shape that will have the reshape handle)
        tool.wallReshapingTool.isEnabled = true;
        diagram.select(part);
        tool.wallReshapingTool.isBuilding = true;
        tool.wallReshapingTool.adornedShape = part.findObject('SHAPE');
        tool.wallReshapingTool.doActivate();
    }
    /**
     * If user presses Esc key, cancel the wall building
     */
    doKeyDown() {
        const fp = this.diagram;
        const e = fp.lastInput;
        if (e.commandKey === 'Escape') {
            const wall = fp.selection.first();
            fp.remove(wall);
            fp.pointNodes.iterator.each(function (node) {
                fp.remove(node);
            });
            fp.dimensionLinks.iterator.each(function (link) {
                fp.remove(link);
            });
            fp.pointNodes.clear();
            fp.dimensionLinks.clear();
            this.doDeactivate();
        }
        super.doKeyDown();
    }
    /**
     * When the mouse moves, reshape the wall
     */
    doMouseMove() {
        if (this.wallReshapingTool === null)
            return;
        this.diagram.currentCursor = 'crosshair';
        this.wallReshapingTool.doMouseMove();
    }
    /**
     * End transaction, update wall dimensions and geometries (mitering?)
     */
    doDeactivate() {
        const diagram = this.diagram;
        this.buildingWall = null;
        this.diagram.currentCursor = '';
        this.diagram.isMouseCaptured = false;
        if (this.wallReshapingTool !== null) {
            this.wallReshapingTool.isEnabled = false;
            this.wallReshapingTool.adornedShape = null;
            this.wallReshapingTool.doMouseUp(); // perform mitering
            this.wallReshapingTool.doDeactivate();
            this.wallReshapingTool.isBuilding = false;
        }
        const fp = diagram;
        fp.updateWallDimensions();
        this.stopTransaction();
        this.isActive = false; // Default functionality
    }
}
// export = WallBuildingTool;
