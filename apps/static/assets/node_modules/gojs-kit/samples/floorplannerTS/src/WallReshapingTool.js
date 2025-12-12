/*
 * Copyright 1998-2025 by Northwoods Software Corporation
 * All Rights Reserved.
 *
 * FLOOR PLANNER: WALL RESHAPING TOOL
 * Used to reshape walls via their endpoints in a Floorplan
 */
import * as go from 'gojs';
export class WallReshapingTool extends go.Tool {
    /**
     * @constructor
     * This tool is responsible for allowing walls in a Floorplan to be reshaped via handles on either side.
     */
    constructor(init) {
        super();
        const h = new go.Shape();
        h.figure = 'Diamond';
        h.desiredSize = new go.Size(12, 12);
        h.fill = 'lightblue';
        h.stroke = 'dodgerblue';
        h.cursor = 'move';
        this._handleArchetype = h;
        this._handle = null;
        this._adornedShape = null;
        this._reshapeObjectName = 'SHAPE';
        this._angle = 0;
        this._length = 0;
        this._isBuilding = false; // only true when a wall is first being constructed, set in WallBuildingTool's doMouseUp function
        this._isIntersecting = false;
        this._joinedWalls = new go.Set();
        this._returnPoint = null; // used if reshape is cancelled; return reshaping wall endpoint to its previous location
        this._returnData = null; // used if reshape is cancelled; return all windows/doors of a reshaped wall to their old place
        this._joinedWalls = new go.Set();
        this._wallIntersecting = null;
        if (init)
            Object.assign(this, init);
    }
    // Get the archetype for the handle (a Shape)
    get handleArchetype() {
        return this._handleArchetype;
    }
    // Get / set current handle being used to reshape the wall
    get handle() {
        return this._handle;
    }
    set handle(value) {
        this._handle = value;
    }
    // Get / set adorned shape (shape of the Wall Group being reshaped)
    get adornedShape() {
        return this._adornedShape;
    }
    set adornedShape(value) {
        this._adornedShape = value;
    }
    // Get / set current angle
    get angle() {
        return this._angle;
    }
    set angle(value) {
        this._angle = value;
    }
    // Get / set length of the wall being reshaped (used only with SHIFT + drag)
    get length() {
        return this._length;
    }
    set length(value) {
        this._length = value;
    }
    // Get / set the name of the object being reshaped
    get reshapeObjectName() {
        return this._reshapeObjectName;
    }
    set reshapeObjectName(value) {
        this._reshapeObjectName = value;
    }
    // Get / set flag telling tool whether it's reshaping a new wall (isBuilding = true) or reshaping an old wall (isBuilding = false)
    get isBuilding() {
        return this._isBuilding;
    }
    set isBuilding(value) {
        this._isBuilding = value;
    }
    // Get set loc data for wallParts to return to if reshape is cancelled
    get returnData() {
        return this._returnData;
    }
    set returnData(value) {
        this._returnData = value;
    }
    // Get / set the point to return the reshaping wall endpoint to if reshape is cancelled
    get returnPoint() {
        return this._returnPoint;
    }
    set returnPoint(value) {
        this._returnPoint = value;
    }
    // Get / set whether the reshaping wall is intersecting at least one other wall. if so, ignore grid snap
    get isIntersecting() {
        return this._isIntersecting;
    }
    set isIntersecting(value) {
        this._isIntersecting = value;
    }
    // Get / set the wall the reshaping endpoint is currently intersecting
    get wallIntersecting() {
        return this._wallIntersecting;
    }
    set wallIntersecting(value) {
        this._wallIntersecting = value;
    }
    // Get / set the wall created during after a reshape event by combining some colinear walls
    get joinedWalls() {
        return this._joinedWalls;
    }
    set joinedWalls(value) {
        this._joinedWalls = value;
    }
    /**
     * Places reshape handles on either end of a wall node.
     * @param {go.Part} part The wall to adorn
     */
    updateAdornments(part) {
        if (part === null || part instanceof go.Link)
            return;
        if (part.isSelected && !this.diagram.isReadOnly) {
            const seleltgo = part.findObject(this.reshapeObjectName);
            if (seleltgo !== null &&
                seleltgo.part !== null &&
                seleltgo.part.data.category === 'WallGroup') {
                const selelt = seleltgo;
                let adornment = part.findAdornment(this.name);
                if (adornment === null) {
                    adornment = this.makeAdornment(selelt);
                }
                if (adornment !== null && selelt.part !== null && selelt.geometry != null) {
                    // update the position/alignment of each handle
                    const geo = selelt.geometry;
                    const b = geo.bounds;
                    const pb = selelt.part.actualBounds;
                    // update the size of the adornment
                    const graphObj = adornment.findObject('BODY');
                    if (graphObj === null)
                        return;
                    graphObj.desiredSize = b.size;
                    adornment.elements.each(function (h) {
                        if (h.name === undefined)
                            return;
                        let x = 0;
                        let y = 0;
                        switch (h.name) {
                            case 'sPt': {
                                x = part.data.startpoint.x - pb.x;
                                y = part.data.startpoint.y - pb.y;
                                break;
                            }
                            case 'ePt': {
                                x = part.data.endpoint.x - pb.x;
                                y = part.data.endpoint.y - pb.y;
                                break;
                            }
                        }
                        let xCheck = Math.min((x - b.x) / b.width, 1);
                        let yCheck = Math.min((y - b.y) / b.height, 1);
                        if (xCheck < 0)
                            xCheck = 0;
                        if (yCheck < 0)
                            yCheck = 0;
                        if (xCheck > 1)
                            xCheck = 1;
                        if (yCheck > 1)
                            yCheck = 1;
                        if (isNaN(xCheck))
                            xCheck = 0;
                        if (isNaN(yCheck))
                            yCheck = 0;
                        h.alignment = new go.Spot(Math.max(0, xCheck), Math.max(0, yCheck));
                    });
                    part.addAdornment(this.name, adornment);
                    adornment.location = selelt.getDocumentPoint(go.Spot.Center);
                    return;
                }
            }
        }
        part.removeAdornment(this.name);
    }
    /**
     * If the user has clicked down at a visible handle on a wall node, then the tool may start.
     * @return {boolean}
     */
    canStart() {
        if (!this.isEnabled)
            return false;
        const diagram = this.diagram;
        if (diagram === null || diagram.isReadOnly)
            return false;
        if (!diagram.allowReshape)
            return false;
        if (!diagram.lastInput.left)
            return false;
        const h = this.findToolHandleAt(diagram.firstInput.documentPoint, this.name);
        return h !== null || this.isBuilding;
    }
    /**
     * Start a new transaction for the wall reshaping.
     * Store pre-reshape location of reshaping wall's reshaping endpoint.
     * Store pre-reshape locations of all wall's members (windows / doors).
     */
    doActivate() {
        const diagram = this.diagram;
        if (diagram === null)
            return;
        if (this.isBuilding) {
            // this.adornedShape has already been set in WallBuildingTool's doMouseDown function
            if (this.adornedShape !== null && this.adornedShape.part !== null) {
                const wall = this.adornedShape.part;
                this.handle = this.findToolHandleAt(wall.data.endpoint, this.name);
                this.returnPoint = wall.data.startpoint;
            }
        }
        else {
            this.handle = this.findToolHandleAt(diagram.firstInput.documentPoint, this.name);
            if (this.handle === null)
                return;
            const adorn = this.handle.part;
            const shape = adorn.adornedObject;
            const wall = shape.part;
            if (!shape)
                return;
            this.adornedShape = shape;
            // store pre-reshape location of wall's reshaping endpoint
            this.returnPoint = this.handle.name === 'sPt' ? wall.data.startpoint : wall.data.endpoint;
            // store pre-reshape locations of all wall's members (windows / doors)
            const wallParts = wall.memberParts;
            if (wallParts.count !== 0) {
                const locationsMap = new go.Map();
                wallParts.iterator.each(function (wallPart) {
                    locationsMap.add(wallPart.data.key, wallPart.location);
                });
                this.returnData = locationsMap;
            }
        }
        // diagram.isMouseCaptured = true;
        this.startTransaction(this.name);
        this.isActive = true;
    }
    /**
     * Adjust the handle's coordinates, along with the wall's points.
     */
    doMouseMove() {
        const fp = this.diagram;
        const tool = this;
        if (tool.handle === null)
            return;
        const adorn = tool.handle.part;
        const wall = adorn.adornedPart;
        // the stationaryPt
        let mousePt = fp.lastInput.documentPoint;
        if (tool.isActive && fp !== null) {
            // if user is holding shift, make sure the angle of the reshaping wall (from stationaryPt to mousePt) is a multiple of 45
            if (fp.lastInput.shift) {
                // what's the current angle made from stationaryPt to mousePt?
                const type = tool.handle.name;
                const stationaryPt = type === 'sPt' ? wall.data.endpoint : wall.data.startpoint;
                let ang = stationaryPt.directionPoint(mousePt);
                const length = Math.sqrt(stationaryPt.distanceSquaredPoint(mousePt));
                ang = Math.round(ang / 45) * 45;
                let newPoint = new go.Point(stationaryPt.x + length, stationaryPt.y);
                // rotate the new point ang degrees
                const dx = stationaryPt.x;
                const dy = stationaryPt.y;
                newPoint = newPoint.offset(-dx, -dy); // move point to origin
                newPoint = newPoint.rotate(ang); // rotate ang degrees around origin
                newPoint = newPoint.offset(dx, dy); // add back offset
                mousePt = newPoint;
            }
            // if the mousePt is close to some wall's endpoint, snap the mousePt to that endpoint
            const walls = fp.findNodesByExample({
                category: 'WallGroup',
            });
            walls.iterator.each(function (w) {
                if (w.data.key !== wall.data.key) {
                    const spt = w.data.startpoint;
                    const ept = w.data.endpoint;
                    // if the mousePt is inside the geometry of another wall, project the point onto that wall
                    if (fp.isPointInWall(w, mousePt)) {
                        mousePt = mousePt.projectOntoLineSegmentPoint(w.data.startpoint, w.data.endpoint);
                        tool.isIntersecting = true; // yes, the current reshaping wall is intersecting another wall
                    }
                    // if the mousePt is close to some wall's endpoint, snap the mousePt to that endpoint
                    if (Math.sqrt(spt.distanceSquaredPoint(mousePt)) < 10) {
                        mousePt = spt;
                    }
                    else if (Math.sqrt(ept.distanceSquaredPoint(mousePt)) < 10) {
                        mousePt = ept;
                    }
                }
            });
            // if the resulting segment between stationary pt and mousePt would intersect other wall(s), project mousePt onto the first wall it would intersect
            const iw = tool.getClosestIntersectingWall(mousePt);
            // if we are or just were intersecting some wall, miter it
            if (iw === null || tool.wallIntersecting !== null) {
                if (tool.wallIntersecting !== null &&
                    tool.wallIntersecting !== undefined &&
                    tool.wallIntersecting.data !== null) {
                    tool.performMiteringOnWall(tool.wallIntersecting);
                }
            }
            if (iw != null) {
                tool.isIntersecting = true; // yes, the current reshaping wall is intersecting another wall
                tool.wallIntersecting = iw;
                mousePt = mousePt.projectOntoLineSegmentPoint(iw.data.startpoint, iw.data.endpoint);
                // if the mousePt is really close to an endpoint of its intersecting wall, make it that endpoint
                const distToSpt = Math.sqrt(mousePt.distanceSquaredPoint(iw.data.startpoint));
                const distToEpt = Math.sqrt(mousePt.distanceSquaredPoint(iw.data.endpoint));
                if (distToSpt < 25) {
                    mousePt = iw.data.startpoint;
                }
                else if (distToEpt < 10) {
                    mousePt = iw.data.endpoint;
                }
            }
            else {
                tool.isIntersecting = false;
                // if the wall we were previously intersecting is not touching the reshaping wall, forget it
                if (tool.wallIntersecting !== null &&
                    tool.wallIntersecting !== undefined &&
                    tool.wallIntersecting.data !== null &&
                    fp.getWallsIntersection(wall, tool.wallIntersecting) === null) {
                    tool.wallIntersecting = null;
                }
            }
            tool.calcAngleAndLengthFromHandle(mousePt); // sets this.angle and this.length (useful for when SHIFT is held)
            tool.reshape(mousePt);
        }
        tool.performMiteringOnWall(wall);
        fp.updateWallDimensions();
        fp.updateWallAngles();
    }
    /**
     * Get the closest wall the reshaping wall intersects with.
     * Returns null if reshaping wall does not intersect with any other wall.
     * @param {go.Point} proposedPt The proposed point for the reshaping wall's moving pt
     * @return {go.Group | null} The closest wall the reshaping wall's reshaping endpoint intersects with
     */
    getClosestIntersectingWall(proposedPt) {
        const tool = this;
        if (tool.handle === null)
            return null;
        const adorn = tool.handle.part;
        const wall = adorn.adornedPart;
        const type = tool.handle.name;
        const stationaryPt = type === 'sPt' ? wall.data.endpoint : wall.data.startpoint;
        // dummy wall is used for intersection checks, since the reshaping wall has not had its data yet set
        const dummyWallData = {
            key: 'wall',
            category: 'WallGroup',
            caption: 'Wall',
            type: 'Wall',
            startpoint: stationaryPt,
            smpt1: stationaryPt,
            smpt2: stationaryPt,
            endpoint: proposedPt,
            empt1: proposedPt,
            empt2: proposedPt,
            thickness: parseFloat(tool.diagram.model.modelData.wallThickness),
            isGroup: true,
            notes: '',
        };
        tool.diagram.model.addNodeData(dummyWallData);
        const dummyWall = tool.diagram.findPartForKey(dummyWallData.key);
        const fp = tool.diagram;
        const walls = tool.diagram.findNodesByExample({
            category: 'WallGroup',
        });
        let closestWall = null;
        let closestDistance = Number.MAX_VALUE;
        walls.iterator.each(function (w) {
            if (w.data.key !== wall.data.key && w.data.key !== dummyWall.data.key) {
                // check if wall and w intersect, and if so, where
                const intersectPoint = fp.getWallsIntersection(dummyWall, w);
                // also, don't project onto a wall the stationaryPt is already along (this would make two walls on top of each other)
                let isStationaryPtOnW = false;
                const ab = parseFloat(Math.sqrt(w.data.startpoint.distanceSquaredPoint(stationaryPt)).toFixed(2));
                const bc = parseFloat(Math.sqrt(stationaryPt.distanceSquaredPoint(w.data.endpoint)).toFixed(2));
                const ac = parseFloat(Math.sqrt(w.data.startpoint.distanceSquaredPoint(w.data.endpoint)).toFixed(2));
                if (Math.abs(ab + bc - ac) <= 0.1) {
                    isStationaryPtOnW = true;
                }
                if (intersectPoint !== null && !isStationaryPtOnW) {
                    // calc distance from stationaryPoint to proposed intersection point
                    const dist = Math.sqrt(stationaryPt.distanceSquaredPoint(intersectPoint));
                    if (dist < closestDistance) {
                        closestDistance = dist;
                        closestWall = w;
                    }
                }
            }
        });
        // remove the dummy wall
        fp.remove(dummyWall);
        return closestWall;
    }
    /**
     * Returns whether or not 2 points are "close enough" to each other.
     * "Close enough" is, by default, defined as a point whose x and y values are within .05
     * document units of another point's x and y values.
     * @param {go.Point} p1
     * @param {go.Point} p2
     * @return {boolean}
     */
    pointsApproximatelyEqual(p1, p2) {
        const x1 = p1.x;
        const x2 = p2.x;
        const y1 = p1.y;
        const y2 = p2.y;
        const diff1 = Math.abs(x2 - x1);
        const diff2 = Math.abs(y2 - y1);
        if (diff2 < 0.05 && diff1 < 0.05) {
            return true;
        }
        return false;
    }
    /**
     * Sets the counterclockwise mitering point for wallA / clockwise mitering point for wallB.
     * This algorithm based on https://math.stackexchange.com/questions/1849784/calculate-miter-points-of-stroked-vectors-in-cartesian-plane.
     * @param {go.Group} wa wallA
     * @param {go.Group} wb wallB
     */
    performMitering(wa, wb) {
        const tool = this;
        const diagram = this.diagram;
        // wall endpoints, thicknesses, lengths
        const as = wa.data.startpoint;
        const ae = wa.data.endpoint;
        const bs = wb.data.startpoint;
        const be = wb.data.endpoint;
        const wat = wa.data.thickness;
        const wbt = wb.data.thickness;
        const wal = Math.sqrt(as.distanceSquaredPoint(ae));
        const wbl = Math.sqrt(bs.distanceSquaredPoint(be));
        // points
        const B = diagram.getWallsIntersection(wa, wb); // intersection point
        if (B === null) {
            return;
        }
        let A = tool.pointsApproximatelyEqual(as, B) ? ae : as; // wallA non-intersection point
        let C = tool.pointsApproximatelyEqual(bs, B) ? be : bs; // wallB non-intersection point
        // edge case: non-endpoint intersection
        // must know which wall is outer wall (the one who has no endpoint in the intersection)
        // and which wall is inner wall (the one with an endpoint in the intersection)
        let ow = null;
        let iw = null;
        if (!tool.pointsApproximatelyEqual(as, B) && !tool.pointsApproximatelyEqual(ae, B)) {
            ow = wa;
            iw = wb;
        }
        else if (!tool.pointsApproximatelyEqual(bs, B) && !tool.pointsApproximatelyEqual(be, B)) {
            ow = wb;
            iw = wa;
        }
        // if wall A is the inner wall, use the endpoint of wall B that counterclockwise from point A for point C
        if (ow !== null && iw !== null && wa.data.key === iw.data.key) {
            if (tool.isClockwise(A, B, ow.data.startpoint)) {
                C = ow.data.startpoint;
            }
            else {
                C = ow.data.endpoint;
            }
        }
        // if wall B is the inner wall, use endpoint of wall A that's clockwise from point C for point A
        if (ow !== null && iw !== null && wb.data.key === iw.data.key) {
            if (tool.isClockwise(B, C, ow.data.startpoint)) {
                A = ow.data.startpoint;
            }
            else {
                A = ow.data.endpoint;
            }
        }
        // angle between wallA and wallB, clockwise, in degrees
        const a1 = B.directionPoint(A);
        const a2 = B.directionPoint(C);
        let ang = Math.abs(a1 - a2 + 360) % 360;
        if (Math.abs(ang - 180) < 0.1) {
            return;
        }
        ang = ang * (Math.PI / 180); // radians
        // create a parallelogram with altitudes wat/2 and wbt/2, s.t. u and v are the lengths from B to reach D (counterclockwise mitering point)
        const u = Math.abs(wbt / (2 * Math.sin(ang)));
        const v = Math.abs(wat / (2 * Math.sin(ang)));
        // get u and v vectors
        const ab = Math.sqrt(A.distanceSquaredPoint(B));
        const bc = Math.sqrt(B.distanceSquaredPoint(C));
        const ux = ((A.x - B.x) / ab) * u;
        const uy = ((A.y - B.y) / ab) * u;
        // only for endpoint-endpoint?
        const vx = ((C.x - B.x) / bc) * v;
        const vy = ((C.y - B.y) / bc) * v;
        // these are the mitering points
        const D = new go.Point(B.x + ux + vx, B.y + uy + vy);
        const E = new go.Point(B.x - ux - vx, B.y - uy - vy);
        // miter limit TODO???
        const minLength = Math.min(wal, wbl);
        if (Math.sqrt(D.distanceSquaredPoint(B)) > minLength) {
            return;
        }
        // mitering point / other mitering point
        const mpt = tool.isClockwise(B, A, D) ? E : D;
        if (isNaN(mpt.x) || isNaN(mpt.y)) {
            return;
        }
        // now figure out which mitering point of wallA's data to modify
        // only modify a mitering point in data if B is one of wallA's endpoints
        if (tool.pointsApproximatelyEqual(as, B) || tool.pointsApproximatelyEqual(ae, B)) {
            let prop = null;
            // wall A's direction to point B is from startpoint to endpoint
            if (tool.pointsApproximatelyEqual(A, as)) {
                // if ang2 is clockwise of ang1, update empt1
                if (tool.isClockwise(A, B, mpt)) {
                    prop = 'empt1';
                }
                else {
                    prop = 'empt2';
                }
            }
            else if (tool.pointsApproximatelyEqual(A, ae)) {
                // wall A's direction to point B is from endpoint to startpoint
                if (tool.isClockwise(A, B, mpt)) {
                    prop = 'smpt2';
                }
                else {
                    prop = 'smpt1';
                }
            }
            if (prop !== null) {
                diagram.model.setDataProperty(wa.data, prop, mpt);
                diagram.updateWall(wa);
            }
        }
        // same, but for wall B
        if (tool.pointsApproximatelyEqual(bs, B) || tool.pointsApproximatelyEqual(be, B)) {
            let prop = null;
            // wall A's direction to point B is from startpoint to endpoint
            if (tool.pointsApproximatelyEqual(C, bs)) {
                // if ang2 < ang1, update empt1
                if (tool.isClockwise(C, B, mpt)) {
                    prop = 'empt1';
                }
                else {
                    prop = 'empt2';
                }
            }
            else if (tool.pointsApproximatelyEqual(C, be)) {
                // wall A's direction to point B is from endpoint to startpoint
                if (tool.isClockwise(C, B, mpt)) {
                    prop = 'smpt2';
                }
                else {
                    prop = 'smpt1';
                }
            }
            if (prop !== null) {
                diagram.model.setDataProperty(wb.data, prop, mpt);
                diagram.updateWall(wb);
            }
        }
    }
    /**
     * Returns a set of all the wall intersections in the entire floorplan.
     * Each entry is a stringified points (i.e. "0 0").
     * @return {go.Set<string>}
     */
    getAllWallIntersectionPoints() {
        const tool = this;
        const diagram = tool.diagram;
        // get all walls
        const walls = diagram.findNodesByExample({
            category: 'WallGroup',
        });
        const intersectionPoints = new go.Set(); // set of Points where walls intersect
        walls.iterator.each(function (w) {
            // for each wall, go through all other walls; if this wall intersects another wall, mark it as an intersection point
            const otherWalls = diagram.findNodesByExample({
                category: 'WallGroup',
            });
            otherWalls.iterator.each(function (ow) {
                if (ow.data.key === w.data.key)
                    return; // do not check for intersection with self
                const ip = diagram.getWallsIntersection(w, ow);
                let doAdd = true;
                if (ip !== null) {
                    // make sure there is not already an intersection point in the set that's really close to this one
                    intersectionPoints.iterator.each(function (ips) {
                        const ip2 = go.Point.parse(ips);
                        if (tool.pointsApproximatelyEqual(ip2, ip)) {
                            doAdd = false;
                        }
                    });
                    if (doAdd) {
                        intersectionPoints.add(go.Point.stringify(ip));
                    }
                }
            });
        });
        return intersectionPoints;
    }
    /**
     * Get all the walls with an endpoint at a given Point.
     * Returns a List of all walls involved in that intersection.
     * @param {go.Point | null} intersectionPoint
     * @param {boolean} includeDividers Whether or not to also include Room Dividers with endpoints at intersectionPoint. Default is true.
     * @return {go.List<go.Group>}
     */
    getAllWallsAtIntersection(intersectionPoint, includeDividers) {
        if (includeDividers === undefined || includeDividers === null) {
            includeDividers = true;
        }
        const tool = this;
        const diagram = tool.diagram;
        const wallsInvolved = new go.List(); // list of walls, which will be sorted clockwise
        if (intersectionPoint === null) {
            return wallsInvolved;
        }
        diagram.findObjectsNear(intersectionPoint, 1, function (x) {
            if (x.part !== null) {
                return x.part;
            }
            return null;
        }, function (p) {
            if (!(p instanceof go.Group &&
                p.category === 'WallGroup' &&
                (includeDividers || !p.data.isDivider) &&
                !wallsInvolved.contains(p)))
                return false;
            // make sure the wall's segment includes ip
            const s = p.data.startpoint;
            const e = p.data.endpoint;
            return tool.isPointOnSegment(s, e, intersectionPoint);
        }, true, wallsInvolved);
        return wallsInvolved;
    }
    /**
     * Returns whether or not 2 walls share at least one endpoint
     * @param {go.Group} wa
     * @param {go.Group} wb
     * @return {boolean}
     */
    doWallsShareAnEndpoint(wa, wb) {
        const tool = this;
        const as = wa.data.startpoint;
        const ae = wa.data.endpoint;
        const bs = wb.data.startpoint;
        const be = wb.data.endpoint;
        if (tool.pointsApproximatelyEqual(as, bs) ||
            tool.pointsApproximatelyEqual(as, be) ||
            tool.pointsApproximatelyEqual(ae, bs) ||
            tool.pointsApproximatelyEqual(ae, be)) {
            return true;
        }
        return false;
    }
    /**
     * This function, called on {@link doMouseUp} event, checks if the reshaping wall's reshaping endpoint is now intersecting a wall.
     * If so, that intersected wall is split into 2 walls at the intersection point. All walls at the intersection point are then mitered.
     * Next, it checks if the reshapingWall has become a new, big wall (via {@link joinColinearWalls}).
     * If so, we must split the new wall at any points it intersects with others.
     * Room boundary data that depended on the split wall is then updated to reflect the split.
     */
    maybeSplitWall() {
        const tool = this;
        if (tool.handle === null)
            return;
        const adorn = tool.handle.part;
        const reshapingWall = adorn.adornedPart;
        const movingProp = tool.handle.name;
        const movingPt = movingProp === 'sPt' ? reshapingWall.data.startpoint : reshapingWall.data.endpoint;
        const jw = tool.joinedWalls;
        const wallsAtEndpoint = tool.getAllWallsAtIntersection(movingPt);
        // exclude the reshapingWall from wallsAtEndpoint
        wallsAtEndpoint.remove(reshapingWall);
        jw.iterator.each(function (ww) {
            wallsAtEndpoint.remove(ww);
        });
        if (wallsAtEndpoint.count === 1) {
            const wallToSplit = wallsAtEndpoint.first();
            if (wallToSplit !== null) {
                // make sure this is not an endpoint to endpoint connection
                if (!tool.doWallsShareAnEndpoint(reshapingWall, wallToSplit)) {
                    tool.maybePerformWallSplit(wallToSplit, movingPt);
                }
            }
        }
        // if we're building a wall, it's possible we need to split at the stationary pt too
        if (tool.isBuilding) {
            const stationaryPt = movingPt === reshapingWall.data.startpoint
                ? reshapingWall.data.endpoint
                : reshapingWall.data.startpoint;
            const wallsAtStationaryPt = tool.getAllWallsAtIntersection(stationaryPt);
            wallsAtStationaryPt.remove(reshapingWall);
            jw.iterator.each(function (ww) {
                wallsAtEndpoint.remove(ww);
            });
            if (wallsAtStationaryPt.count === 1) {
                const wallToSplit = wallsAtStationaryPt.first();
                if (wallToSplit !== null) {
                    // make sure this is not an endpoint to endpoint connection
                    if (!tool.doWallsShareAnEndpoint(reshapingWall, wallToSplit)) {
                        tool.maybePerformWallSplit(wallToSplit, stationaryPt);
                    }
                }
            }
        }
        // if this reshape event has created a big joined wall, the joined wall may need to be split
        // find out if either endpoint of the original reshaping wall is NOT one of the endpoints of joinedWall
        // if so, split the joinedWall at that endpoint
        if (jw !== null) {
            jw.iterator.each(function (ww) {
                // find all points along the joined wall where it intersects with other walls and split along them
                tool.splitNewWall(ww);
            });
        }
    }
    /**
     * Finds all points along a new wall (created via {@link joinColinearWalls}) and splits / miters at each.
     * @param w The newly joined wall
     */
    splitNewWall(w) {
        const tool = this;
        const fp = this.diagram;
        // find all walls that intersect this wall
        const walls = fp.findNodesByExample({
            category: 'WallGroup',
        });
        const ips = new go.Set();
        walls.iterator.each(function (ww) {
            const ip = fp.getWallsIntersection(w, ww);
            if (ip !== null) {
                ips.add(ip);
            }
        });
        ips.iterator.each(function (ip) {
            const wi = tool.getAllWallsAtIntersection(ip);
            wi.iterator.each(function (ww) {
                const s = ww.data.startpoint;
                const e = ww.data.endpoint;
                if (!tool.pointsApproximatelyEqual(s, ip) && !tool.pointsApproximatelyEqual(e, ip)) {
                    tool.maybePerformWallSplit(ww, ip);
                }
            });
        });
    }
    /**
     * Split a given wall into 2 at a given intersection point, if the given point is on the wall and not on one of the wall's endpoints.
     * The resultant two walls are then mitered.
     * Room boundary data that depended on the split wall is then updated to reflect the split.
     * @param {go.Group} w wall to split
     * @param {go.Point} ip intersection point where the split should occur
     */
    maybePerformWallSplit(w, ip) {
        const tool = this;
        const fp = tool.diagram;
        const s = w.data.startpoint;
        const e = w.data.endpoint;
        const type = w.data.isDivider ? 'Divider' : 'Wall';
        // this wall has neither endpoint in the intersection -- it must be split into 2 walls
        const data1 = {
            key: 'wall',
            category: 'WallGroup',
            caption: type,
            type: type,
            color: w.data.color,
            startpoint: s,
            endpoint: ip,
            smpt1: s,
            smpt2: s,
            empt1: ip,
            empt2: ip,
            thickness: w.data.thickness,
            isGroup: true,
            notes: '',
            isDivider: w.data.isDivider,
        };
        const data2 = {
            key: 'wall',
            category: 'WallGroup',
            caption: type,
            type: type,
            color: w.data.color,
            startpoint: ip,
            endpoint: e,
            smpt1: ip,
            smpt2: ip,
            empt1: e,
            empt2: e,
            thickness: w.data.thickness,
            isGroup: true,
            notes: '',
            isDivider: w.data.isDivider,
        };
        // only actually split the wall if the 2 new walls would both have at least length 1
        // and if there are no walls with endpoints very close to these proposed ones
        const l1 = Math.sqrt(data1.startpoint.distanceSquaredPoint(data1.endpoint));
        const l2 = Math.sqrt(data2.startpoint.distanceSquaredPoint(data2.endpoint));
        const walls = fp.findNodesByExample({
            category: 'WallGroup',
        });
        let alreadyExists = false;
        walls.iterator.each(function (wc) {
            const ws = wc.data.startpoint;
            const we = wc.data.endpoint;
            if ((tool.pointsApproximatelyEqual(s, ws) && tool.pointsApproximatelyEqual(ip, we)) ||
                (tool.pointsApproximatelyEqual(s, we) && tool.pointsApproximatelyEqual(ip, ws))) {
                alreadyExists = true;
            }
            if ((tool.pointsApproximatelyEqual(ip, ws) && tool.pointsApproximatelyEqual(e, we)) ||
                (tool.pointsApproximatelyEqual(ip, we) && tool.pointsApproximatelyEqual(e, ws))) {
                alreadyExists = true;
            }
        });
        if (l1 > 1 && l2 > 1 && !alreadyExists) {
            fp.model.addNodeData(data1);
            fp.model.addNodeData(data2);
            const w1 = fp.findNodeForData(data1);
            const w2 = fp.findNodeForData(data2);
            // Before removing the original wall from the Floorplan, update relevant room boundarywalls data
            // iff this method is being called as a result of a user-prompted wall reshape action
            // needed so proper mitering side of replacement entry walls can be determined
            tool.premiterWall(w1);
            tool.premiterWall(w2);
            tool.performMiteringAtPoint(ip, false);
            if (tool.handle !== null) {
                const rooms = fp.findNodesByExample({ category: 'RoomNode' });
                const adorn = tool.handle.part;
                const rw = adorn.adornedPart; // reshaping wall
                // go through rooms, find any whose boundary walls contain w (the wall that was split, soon to be removed)
                rooms.iterator.each(function (r) {
                    const bw = r.data.boundaryWalls;
                    for (let i = 0; i < bw.length; i++) {
                        const entry = bw[i];
                        const wk = entry[0];
                        if (wk === w.data.key) {
                            // then, find out if the reshaping wall, at the non-ip endpoint, is connected to another wall in that room's boundary walls
                            let isConnectedToBounds = false;
                            const nonIpEndpoint = tool.pointsApproximatelyEqual(rw.data.startpoint, ip)
                                ? rw.data.endpoint
                                : rw.data.startpoint;
                            const iw = tool.getAllWallsAtIntersection(nonIpEndpoint);
                            iw.iterator.each(function (ww) {
                                // if boundary walls contains ww and ww is not the reshaping wall, reshaping wall is connected to room boundary walls at non ip endpoint
                                for (let j = 0; j < bw.length; j++) {
                                    const ee = bw[j];
                                    const wk2 = ee[0];
                                    if (ww.data.key === wk2 && ww.data.key !== rw.data.key) {
                                        isConnectedToBounds = true;
                                    }
                                }
                            });
                            // if yes, replace the w entry in boundary walls with just one new entry, using the split wall that is connected to some other wall in bounds
                            if (isConnectedToBounds) {
                                // find out whether w1 or w2 is connected to another wall in boundary walls
                                let isW1ConnectedToBounds = false;
                                const w1NonIpEndpoint = tool.pointsApproximatelyEqual(w1.data.startpoint, ip)
                                    ? w1.data.endpoint
                                    : w1.data.startpoint;
                                const iw2 = tool.getAllWallsAtIntersection(w1NonIpEndpoint);
                                iw2.remove(w); // do not include the wall soon to be destroyed
                                // go through all walls at w1's non-ip endpoint and find out if one of those is in r's boundary walls
                                iw2.iterator.each(function (ww) {
                                    for (let j = 0; j < bw.length; j++) {
                                        const entry2 = bw[j];
                                        const wk2 = entry2[0];
                                        if (ww.data.key === wk2 && w1.data.key !== ww.data.key) {
                                            // additional followup -- make sure ww2 is still connected to r's boundary walls at other endpoint (not connected to w1NonIpEndpoint)
                                            const ww2 = fp.findNodeForKey(wk2);
                                            const ww2OtherEndpoint = tool.pointsApproximatelyEqual(ww2.data.startpoint, w1NonIpEndpoint)
                                                ? ww2.data.endpoint
                                                : ww2.data.startpoint;
                                            const iw3 = tool.getAllWallsAtIntersection(ww2OtherEndpoint);
                                            iw3.iterator.each(function (ww3) {
                                                for (let k = 0; k < bw.length; k++) {
                                                    const entry3 = bw[k];
                                                    const wk3 = entry3[0];
                                                    if (wk3 === ww3.data.key && wk3 !== ww2.data.key) {
                                                        isW1ConnectedToBounds = true;
                                                    }
                                                }
                                            });
                                        }
                                    }
                                });
                                // replace this entry of r's boundary walls with the replacementWall
                                const replacementWall = isW1ConnectedToBounds ? w1 : w2;
                                const replacementEntry = tool.getUpdatedEntry(entry, replacementWall);
                                fp.startTransaction();
                                const newBounds = bw.slice();
                                newBounds[i] = replacementEntry;
                                fp.model.setDataProperty(r.data, 'boundaryWalls', newBounds);
                                fp.commitTransaction();
                            }
                            else {
                                // if no, replace the w entry with both split walls. Order those 2 entries CC, relative to reshaping wall
                                // get a List of walls involved (reshaping wall, w1, and w2)
                                let wi = new go.List();
                                wi.add(rw);
                                wi.add(w1);
                                wi.add(w2);
                                wi = fp.sortWallsClockwiseWithSetStartWall(wi, rw);
                                // get replacement entries for the entry with w
                                const replacementEntry2 = tool.getUpdatedEntry(entry, wi.toArray()[1]);
                                const replacementEntry1 = tool.getUpdatedEntry(entry, wi.toArray()[2]);
                                // insert these replacement entries into the bw at index i, remove
                                fp.startTransaction();
                                const newBounds = bw.slice();
                                newBounds.splice(i, 1, replacementEntry1);
                                newBounds.splice(i + 1, 0, replacementEntry2);
                                fp.model.setDataProperty(r.data, 'boundaryWalls', newBounds);
                                fp.commitTransaction();
                            }
                        }
                    }
                }); // end rooms iteration
            }
            // Maintain wall parts that were on the big wall -- give them new locations on the most appropriate of the split walls, if possible
            const wallParts = fp.findNodesByExample({ group: w.data.key });
            const wallsSet = new go.Set();
            wallsSet.add(w1);
            wallsSet.add(w2);
            tool.maintainWallParts(wallParts, wallsSet);
            // remove original wall
            fp.remove(w);
            // perform mitering
            tool.premiterWall(w1);
            tool.premiterWall(w2);
            const w1op = tool.pointsApproximatelyEqual(w1.data.startpoint, ip)
                ? w1.data.endpoint
                : w1.data.startpoint;
            const w2op = tool.pointsApproximatelyEqual(w2.data.startpoint, ip)
                ? w2.data.endpoint
                : w2.data.startpoint;
            tool.performMiteringAtPoint(ip, false);
            tool.performMiteringAtPoint(w1op, false);
            tool.performMiteringAtPoint(w2op, false);
        }
    }
    /**
     * Go through all walls -- if a wall crosses another at a non-endpoint-to-endpoint connection, split that wall in 2
     * such that only endpoint to endpoint connections exist (this makes mitering much easier).
     * NOTE: Since this goes through all walls in the Floorplan, performance can get bad quickly. Use this method sparingly, if at all
     */
    splitAllWalls() {
        const tool = this;
        const intersectionPoints = tool.getAllWallIntersectionPoints();
        intersectionPoints.iterator.each(function (ips) {
            const ip = go.Point.parse(ips);
            const wallsInvolved = tool.getAllWallsAtIntersection(ip);
            // find all walls involved that do not have their start or endpoint at the intersection point
            wallsInvolved.iterator.each(function (w) {
                const s = w.data.startpoint;
                const e = w.data.endpoint;
                if (!tool.pointsApproximatelyEqual(s, ip) && !tool.pointsApproximatelyEqual(e, ip)) {
                    tool.maybePerformWallSplit(w, ip);
                }
            });
        });
    }
    /**
     * Return whether or not wall A is parallel to wall B.
     * @param {go.Group} wa Wall A
     * @param {go.Group} wb Wall B
     * @return {boolean}
     */
    areWallsParallel(wa, wb) {
        const tool = this;
        const fp = this.diagram;
        const as = wa.data.startpoint;
        const ae = wa.data.endpoint;
        const bs = wb.data.startpoint;
        const be = wb.data.endpoint;
        let isParallel = false;
        const a1 = +as.directionPoint(ae);
        const a2 = +bs.directionPoint(be);
        if (Math.abs(a1 - a2) < 1 || (Math.abs(a1 - a2) > 179 && Math.abs(a1 - a2) < 181)) {
            isParallel = true;
        }
        return isParallel;
    }
    /**
     * Returns whether wall B is colinear to wall A.
     * Wall A is colinear with Wall B if it:
     *  0) Is the same wall type as Wall B (wall | divider)
     *  1) Is parallel with Wall B
     *  2) Shares an endpoint, 'p', with Wall B, and
     *    2a) Any / all walls with endpoints at p are all parallel to wall A / B
     * @param {go.Group} wa wall A
     * @param {go.Group} wb wall B
     * @return {boolean}
     */
    isWallColinear(wa, wb) {
        const tool = this;
        const fp = this.diagram;
        if (wa.data.isDivider !== wb.data.isDivider) {
            return false;
        }
        const as = wa.data.startpoint;
        const ae = wa.data.endpoint;
        const bs = wb.data.startpoint;
        const be = wb.data.endpoint;
        let isColinear = false;
        // 1) Is wall A parallel with Wall B? (or close enough to parallel)
        if (tool.areWallsParallel(wa, wb)) {
            // get the endpoint shared by wa and wb, if it exists
            let sharedEndpoint = null;
            if (tool.pointsApproximatelyEqual(as, bs) || tool.pointsApproximatelyEqual(as, be)) {
                sharedEndpoint = as;
            }
            else if (tool.pointsApproximatelyEqual(ae, bs) || tool.pointsApproximatelyEqual(ae, be)) {
                sharedEndpoint = ae;
            }
            if (sharedEndpoint !== null) {
                // Make sure all walls with an endpoint at sharedEndpoint are parallel to wa
                const wi = tool.getAllWallsAtIntersection(sharedEndpoint);
                let endpointHasNonColinearWall = false;
                wi.iterator.each(function (w) {
                    if (!tool.areWallsParallel(w, wa)) {
                        endpointHasNonColinearWall = true;
                    }
                });
                if (!endpointHasNonColinearWall) {
                    isColinear = true;
                }
            }
        }
        return isColinear;
    }
    /**
     * Get all walls colinear to wall w and store them in a given Set.
     * @param {go.Group} w
     * @param {go.Set<go.Group>} set Optional
     * @return {go.Set<go.Group>}
     */
    findAllColinearWalls(w, set) {
        if (set === null || set === undefined) {
            set = new go.Set();
        }
        // make sure Set contains w
        set.add(w);
        const tool = this;
        const diagram = tool.diagram;
        const walls = diagram.findNodesByExample({
            category: 'WallGroup',
        });
        walls.iterator.each(function (ow) {
            if (tool.isWallColinear(w, ow) && set !== undefined && !set.contains(ow)) {
                set.add(ow);
                tool.findAllColinearWalls(ow, set);
            }
        });
        return set;
    }
    /**
     * This function, called after each {@link doMouseUp} event, checks for colinear pairs of walls at two places.
     * First, it checks for colinear walls with the reshaping wall.
     * Second, it checks for colinear walls at {@link returnPoint}.
     * If there are colinear walls found, they are joined into one big wall. Resultant wall(s) are then mitered.
     * Additionally, any rooms whose geometries depended on one of the walls that was just joined have their data updated,
     * replacing the old (removed) wall(s) in data with the new one.
     * Note: These rooms will have the final update to their geometry / data done later, in updateRoomBoundaries().
     * The data manipulation done here is just to ensure the walls removed by this function are not referenced anywhere in room data anymore.
     */
    joinColinearWalls() {
        const tool = this;
        if (tool.handle === null)
            return;
        // 1) Check if the reshaping wall is colinear with another wall at one of its endpoints
        const adorn = tool.handle.part;
        const reshapingWall = adorn.adornedPart;
        const cw1 = tool.findAllColinearWalls(reshapingWall);
        const jw = tool.performColinearWallJoining(cw1, reshapingWall);
        if (jw !== null) {
            tool.joinedWalls.add(jw);
        }
        // 2) Check if there are 2 colinear walls at returnPoint (where the reshaping endpoint originally was)
        const wallsAtReturnPoint = tool.getAllWallsAtIntersection(tool.returnPoint);
        if (wallsAtReturnPoint.count === 2) {
            const wallsArr = wallsAtReturnPoint.toArray();
            const w1 = wallsArr[0];
            const w2 = wallsArr[1];
            if (tool.isWallColinear(w1, w2)) {
                const cw2 = new go.Set();
                cw2.add(w1);
                cw2.add(w2);
                const jw2 = tool.performColinearWallJoining(cw2, w1);
                if (jw2 !== null) {
                    tool.joinedWalls.add(jw2);
                }
            }
        }
    }
    /**
     * Join a set of colinear walls into one big wall. The big wall is then mitered.
     * Constituent walls in colinear wall set are removed.
     * As such, if any rooms depend on them for boundary data, those room's data is updated
     * @param {go.Set<go.Group>} colinearWalls The set of colinear walls
     * @param {go.Group} w The wall to use as reference for color / thickness when joining the walls.
     * If this is not supplied, the first wall in the colinearWalls set is used
     * @return {go.Group | null} The new, big wall created by joining colinear walls
     */
    performColinearWallJoining(colinearWalls, w) {
        const tool = this;
        const fp = tool.diagram;
        const garbage = new go.Set();
        // all colinear "walls" must be Walls OR they must all be Room Dividers, they may not be a mix
        const cwf = colinearWalls.first();
        if (cwf === null) {
            return null;
        }
        if (w === undefined) {
            w = cwf;
        }
        const acceptedCategory = cwf.data.category;
        colinearWalls.iterator.each(function (cw) {
            if (cw.data.category !== acceptedCategory) {
                return;
            }
        });
        // Find the 2 farthest endpoints in colinear walls set
        if (colinearWalls.count > 1) {
            let pt1 = null;
            let pt2 = null;
            let farthestDist = 0;
            const cw2 = colinearWalls.copy();
            // remember all the wall parts (doors / windows) that the colinear walls have
            const wallParts = new go.Set();
            // iterate over colinear walls, finding the furthest distance between all endpoints
            colinearWalls.iterator.each(function (cw1) {
                // get all wallParts that belong to cw1 and add them to wallParts Set
                const cwParts = fp.findNodesByExample({ group: cw1.data.key });
                wallParts.addAll(cwParts);
                cw2.iterator.each(function (cw2w) {
                    const s1 = cw1.data.startpoint;
                    const e1 = cw1.data.endpoint;
                    const s2 = cw2w.data.startpoint;
                    const e2 = cw2w.data.endpoint;
                    const pts1 = [s1, e1];
                    const pts2 = [s2, e2];
                    for (let i = 0; i < pts1.length; i++) {
                        const p1 = pts1[i];
                        for (let j = 0; j < pts2.length; j++) {
                            const p2 = pts2[j];
                            const dist = Math.sqrt(p1.distanceSquaredPoint(p2));
                            if (dist > farthestDist) {
                                farthestDist = dist;
                                pt1 = p1;
                                pt2 = p2;
                            }
                        }
                    }
                });
                // all colinear walls will be destroyed later (after replaced by one big wall)
                garbage.add(cw1);
            }); // end colinearWalls iteration
            // we should now have the farthest points the colinear walls make -- just add a single wall with those endpoints
            const data = {
                key: 'wall',
                category: 'WallGroup',
                caption: 'Wall',
                type: 'Wall',
                color: w.data.color,
                startpoint: pt1,
                endpoint: pt2,
                smpt1: pt1,
                smpt2: pt1,
                empt1: pt2,
                empt2: pt2,
                thickness: w.data.thickness,
                isGroup: true,
                notes: '',
            };
            fp.model.addNodeData(data);
            const newWall = fp.findNodeForData(data);
            // Before the constituent walls are removed from Floorplan, update relevant room boundaryWalls
            // find all rooms that have any of the colinear walls in this roomBoundaryWalls or holes
            // replace those entries with constituent walls with the new wall key
            // make sure the mitering side is analogous to what it was with the consituent wall too
            const rooms = fp.findNodesByExample({ category: 'RoomNode' });
            rooms.iterator.each(function (r) {
                const bw = r.data.boundaryWalls;
                // replace entries in boundaryWalls with references to soon-to-be nonexistent walls
                for (let i = 0; i < bw.length; i++) {
                    const e = bw[i];
                    const wk = e[0];
                    const ww = fp.findNodeForKey(wk);
                    if (colinearWalls.contains(ww)) {
                        // ???
                        tool.performMiteringOnWall(newWall);
                        const newEntry = tool.getUpdatedEntry(e, newWall);
                        // replace the old entry with the new one
                        fp.startTransaction();
                        const newBounds = bw.slice();
                        newBounds[i] = newEntry;
                        fp.model.setDataProperty(r.data, 'boundaryWalls', newBounds);
                        fp.commitTransaction();
                    }
                } // end boundary walls outdated entry replacement
            }); // end rooms iteration
            // Maintain relative position of all wall parts
            const newWallSet = new go.Set();
            newWallSet.add(newWall);
            tool.performMiteringOnWall(newWall);
            tool.maintainWallParts(wallParts, newWallSet);
            // remove the constituent walls from Floorplan
            garbage.iterator.each(function (ww) {
                fp.remove(ww);
            });
            // perform mitering on the new, big wall
            tool.performMiteringOnWall(newWall);
            return newWall;
        }
        return null;
    }
    /**
     * Given a set of wall parts (doors, windows) and a set of walls, place the wall parts on the proper wall based on its location, if possible.
     * @param {go.Iterable<go.Node>} wallParts
     * @param {go.Iterable<go.Group>} walls
     */
    maintainWallParts(wallParts, walls) {
        const tool = this;
        const fp = tool.diagram;
        const garbage = [];
        wallParts.iterator.each(function (wp) {
            const loc = wp.location;
            // find the wall that has this loc in its geometry's boundaries
            walls.iterator.each(function (w) {
                if (fp.isPointInWall(w, loc)) {
                    const newLoc = fp.findClosestLocOnWall(w, wp);
                    // if the wall part can fit on this wall, add it to the wall
                    if (newLoc !== null) {
                        fp.model.setDataProperty(wp.data, 'group', w.data.key);
                        wp.location = newLoc.projectOntoLineSegmentPoint(w.data.startpoint, w.data.endpoint);
                        // wp.angle = w.data.startpoint.directionPoint(w.data.endpoint);
                        if (wp.category === 'WindowNode') {
                            fp.model.setDataProperty(wp.data, 'height', w.data.thickness);
                        }
                        if (wp.category === 'DoorNode') {
                            fp.model.setDataProperty(wp.data, 'doorOpeningHeight', w.data.thickness);
                        }
                    }
                    else {
                        // otherwise, remove it from the diagram
                        garbage.push(wp);
                    }
                }
            });
        });
        for (let i = 0; i < garbage.length; i++) {
            fp.remove(garbage[i]);
        }
    }
    /**
     * Get a replacement entry in a room's boundaryWalls or hole path for an old entry that used one of the walls
     * that was just joined together (since that wall won't exist anymore in just a moment).
     * This will replace the old entry's wall key (Array element 0) with newWall.key.
     * It will also make sure the mitering side of the replacement entry is analogous to the mitering side of the old entry.
     * @param {Array<any>} oldEntry the old entry to replace
     * @param {go.Group} nw new wall
     * @return {Array<any>} The updated entry with the new wall and analogous mitering side
     */
    getUpdatedEntry(oldEntry, nw) {
        const tool = this;
        const fp = tool.diagram;
        const oldWallKey = oldEntry[0];
        const oldWall = fp.findNodeForKey(oldWallKey);
        const oldMiteringSide = oldEntry[1];
        const newEntry = [nw.data.key, null];
        // Get the mitering side of newWall that is analogous to the mitering side of oldWall
        // see if the distance between the midpoint between newWall.smpt1 and newWall.empt1 is closer to oldWall's oldMiteringSide
        // if so, use 1 as new mitering side. Else use 2
        const oms = oldWall.data['smpt' + oldMiteringSide];
        const ome = oldWall.data['empt' + oldMiteringSide];
        /**
         * Get the point on a line at a given x value
         * @param {go.Point} a line point 1
         * @param {go.Point} b line point 2
         * @param {number} x x coordinate
         * @return {go.Point}
         */
        function pointAtX(a, b, x) {
            const slope = (b.y - a.y) / (b.x - a.x);
            const y = a.y + (x - a.x) * slope;
            return new go.Point(x, y);
        }
        // Get the point on the line implied by oms and ome at nw.smpt1 and nw.smpt2
        const pt1 = pointAtX(oms, ome, nw.data.smpt1.x);
        const pt2 = pointAtX(oms, ome, nw.data.smpt2.x);
        const dist1 = nw.data.smpt1.distanceSquaredPoint(pt1);
        const dist2 = nw.data.smpt2.distanceSquaredPoint(pt2);
        if (dist1 < dist2) {
            newEntry[1] = 1;
        }
        else {
            newEntry[1] = 2;
        }
        return newEntry;
    }
    /**
     * Join all sets of colinear walls in the Floorplan.
     * Note: This can get expensive quickly, as it goes over every single wall in the Floorplan. Use this method sparingly, if at all.
     * It may be better to call {@link joinColinearWalls}
     */
    joinAllColinearWalls() {
        const tool = this;
        const diagram = tool.diagram;
        const walls = diagram.findNodesByExample({
            category: 'WallGroup',
        });
        // const garbage: go.Set<go.Group> = new go.Set<go.Group>();
        const handledWalls = new go.Set();
        // iterate over all walls
        walls.iterator.each(function (w) {
            if (!handledWalls.contains(w)) {
                handledWalls.add(w);
                // find all walls connected to an endpoint of this wall w that are also parallel
                const colinearWalls = new go.Set();
                colinearWalls.add(w);
                tool.findAllColinearWalls(w, colinearWalls);
                handledWalls.addAll(colinearWalls);
                tool.performColinearWallJoining(colinearWalls, w);
            } // end handledWalls check
        }); // end walls iteration
        tool.premiterAllWalls();
    }
    /**
     * Get a point a given distance away from a given point at a given angle
     * @param {go.Point} point
     * @param {number} angle
     * @param {number} offset
     * @return {go.Point}
     */
    translateAndRotatePoint(point, angle, offset) {
        const oldPoint = point.copy();
        const newPoint = point.copy();
        newPoint.offset(0, offset);
        newPoint.offset(-oldPoint.x, -oldPoint.y).rotate(angle).offset(oldPoint.x, oldPoint.y);
        return newPoint;
    }
    /**
     * Set a wall's mitering points in data to points thickness/2 distance from start/endpoint at perpindicular angle
     * Then, update the wall to reflect this new geometry
     * @param {go.Group} w
     * @param {string} prop Optional: 'smpt1' | 'smpt2' | 'empt1' | 'empt2'. If this is provided, only premiter that point of the wall
     */
    premiterWall(w, prop) {
        const tool = this;
        const diagram = tool.diagram;
        const ang = w.data.startpoint.directionPoint(w.data.endpoint);
        const t = w.data.thickness;
        const sp = w.data.startpoint;
        const ep = w.data.endpoint;
        switch (prop) {
            case 'smpt1': {
                const smp1 = tool.translateAndRotatePoint(sp, ang, t / 2);
                diagram.model.setDataProperty(w.data, 'smpt1', smp1);
                break;
            }
            case 'smpt2': {
                const smp2 = tool.translateAndRotatePoint(sp, ang + 180, t / 2);
                diagram.model.setDataProperty(w.data, 'smpt2', smp2);
                break;
            }
            case 'empt1': {
                const emp1 = tool.translateAndRotatePoint(ep, ang, t / 2);
                diagram.model.setDataProperty(w.data, 'empt1', emp1);
                break;
            }
            case 'empt2': {
                const emp2 = tool.translateAndRotatePoint(ep, ang + 180, t / 2);
                diagram.model.setDataProperty(w.data, 'empt2', emp2);
                break;
            }
            default: {
                // Perpindicular mitering points (updated later during mitering function)
                // end miterpoint point 1 is the point "below" endpoint (add vector)
                const emp1 = tool.translateAndRotatePoint(ep, ang, t / 2);
                diagram.model.setDataProperty(w.data, 'empt1', emp1);
                // end mitering point 2 is the point "above" endpoint (subtract vector)
                const emp2 = tool.translateAndRotatePoint(ep, ang + 180, t / 2);
                diagram.model.setDataProperty(w.data, 'empt2', emp2);
                // start mitering point 1 is the point "below" startpoint (add vector)
                const smp1 = tool.translateAndRotatePoint(sp, ang, t / 2);
                diagram.model.setDataProperty(w.data, 'smpt1', smp1);
                // end mitering point 2 is the point "above" endpoint (subtract vector)
                const smp2 = tool.translateAndRotatePoint(sp, ang + 180, t / 2);
                diagram.model.setDataProperty(w.data, 'smpt2', smp2);
                break;
            }
        }
        diagram.updateWall(w);
    }
    /**
     * Goes through all walls and sets their mitering points in data to points
     * thickness/2 distance from start/endpoint at perpindicular angle
     * Note: Since this method goes through all walls in the Floorplan, it can get expensive quickly. Use this method sparingly, if at all.
     */
    premiterAllWalls() {
        const tool = this;
        const diagram = tool.diagram;
        const walls = diagram.findNodesByExample({
            category: 'WallGroup',
        });
        walls.iterator.each(function (w) {
            tool.premiterWall(w);
        });
    }
    /**
     * Perform corner mitering at both endpoints of a given wall
     * @param {go.Group} w The wall to perform corner mitering on
     */
    performMiteringOnWall(w) {
        const tool = this;
        const sp = w.data.startpoint;
        const ep = w.data.endpoint;
        tool.premiterWall(w);
        tool.performMiteringAtPoint(sp, true);
        tool.performMiteringAtPoint(ep, true);
    }
    /**
     * Perform corner mitering on all walls that interesct at a given point.
     * This is a more granular, cheaper operation than the larger scale {@link performAllMitering} function.
     * @param {go.Point} pt The point to perform mitering at
     * @param {boolea} performPremitering Whether or not to perform pre-miterign before this op. If true, premitering will only be done at the endpoint of walls equal to pt
     */
    performMiteringAtPoint(pt, performPremitering) {
        if (performPremitering === null || performPremitering === undefined) {
            performPremitering = true;
        }
        const tool = this;
        const fp = tool.diagram;
        // walls involved at intersection point
        const wi = tool.getAllWallsAtIntersection(pt, false);
        // premiter each wall in wi, maybe
        if (performPremitering) {
            wi.iterator.each(function (w) {
                // only perform premiter on w if one of w's endpoints is ot
                if (tool.pointsApproximatelyEqual(w.data.startpoint, pt) ||
                    tool.pointsApproximatelyEqual(w.data.endpoint, pt)) {
                    // which of w's endpoints is pt?
                    const prop = tool.pointsApproximatelyEqual(w.data.startpoint, pt) ? 's' : 'e';
                    tool.premiterWall(w, prop + 'mpt1');
                    tool.premiterWall(w, prop + 'mpt2');
                }
            });
        }
        // sort all involved walls in any COUNTERCLOCWISE order
        wi.sort(function (a, b) {
            const B = fp.getWallsIntersection(a, b);
            if (B === null)
                return 0;
            const as = a.data.startpoint;
            const ae = a.data.endpoint;
            const bs = b.data.startpoint;
            const be = b.data.endpoint;
            const A = tool.pointsApproximatelyEqual(pt, as) ? ae : as;
            const C = tool.pointsApproximatelyEqual(pt, bs) ? be : bs;
            const angA = B.directionPoint(A);
            const angB = B.directionPoint(C);
            if (angA > angB)
                return 1;
            else if (angA < angB)
                return -1;
            else
                return 0;
        });
        wi.reverse();
        const wiArr = wi.toArray();
        for (let i = 0; i < wiArr.length; i++) {
            const wa = wiArr[i];
            let wb = null;
            if (i + 1 === wiArr.length) {
                wb = wiArr[0];
            }
            else {
                wb = wiArr[i + 1];
            }
            // only miter these 2 walls if they are both walls or if they are both room dividers. no mixing
            // if (wa.data.isDivider === wb.data.isDivider) {
            tool.performMitering(wa, wb);
            // }
        }
    }
    /**
     * Performs all mitering for all walls in Floorplan.
     * Note: Since this method goes through all walls in the Floorplan, it can get expensive quickly. Use this method sparingly, if at all.
     */
    performAllMitering() {
        const tool = this;
        const diagram = tool.diagram;
        tool.premiterAllWalls();
        const intersectionPoints = tool.getAllWallIntersectionPoints();
        // iterate over all points where walls intersect
        intersectionPoints.iterator.each(function (ips) {
            const ip = go.Point.parse(ips);
            // get all walls involved in intersection
            const wallsInvolved = tool.getAllWallsAtIntersection(ip);
            // sort all involved walls in any COUNTERCLOCWISE order
            wallsInvolved.sort(function (a, b) {
                const B = diagram.getWallsIntersection(a, b);
                if (B === null)
                    return 0;
                const as = a.data.startpoint;
                const ae = a.data.endpoint;
                const bs = b.data.startpoint;
                const be = b.data.endpoint;
                const A = tool.pointsApproximatelyEqual(ip, as) ? ae : as;
                const C = tool.pointsApproximatelyEqual(ip, bs) ? be : bs;
                const angA = B.directionPoint(A);
                const angB = B.directionPoint(C);
                if (angA > angB)
                    return 1;
                else if (angA < angB)
                    return -1;
                else
                    return 0;
            });
            wallsInvolved.reverse();
            // iterate over wallsInvolved, performing cc mitering on each pair
            const wi = wallsInvolved.toArray();
            for (let i = 0; i < wi.length; i++) {
                const wa = wi[i];
                let wb = null;
                if (i + 1 === wi.length) {
                    wb = wi[0];
                }
                else {
                    wb = wi[i + 1];
                }
                // only miter these 2 walls if they are both walls or if they are both room dividers. no mixing
                // if (wa.data.isDivider === wb.data.isDivider) {
                tool.performMitering(wa, wb);
                // }
            }
        }); // end iterate over intersection points
    } // end performAllMitering
    /**
     * Checks whether segment AB is clockwise of segment BC.
     * B must be the intersection point.
     * @param {go.Point} a
     * @param {go.Point} b
     * @param {go.Point} c
     * @return {boolean}
     */
    isClockwise(a, b, c) {
        return (b.x - a.x) * (c.y - a.y) - (b.y - a.y) * (c.x - a.x) > 0;
    }
    /**
     * Check if point c is on the segment between points a and b
     * @param {go.Point} a
     * @param {go.Point} b
     * @param {go.Point} c
     * @return {boolean}
     */
    isPointOnSegment(a, b, c) {
        const ac = Math.sqrt(a.distanceSquaredPoint(c));
        const bc = Math.sqrt(b.distanceSquaredPoint(c));
        const ab = Math.sqrt(a.distanceSquaredPoint(b));
        if (Math.abs(ab - (ac + bc)) <= 0.1) {
            return true;
        }
        return false;
    }
    /**
     * Joins colinear walls, splits walls, performs mitering, ommits transaction, stops tool.
     */
    doMouseUp() {
        const tool = this;
        const fp = this.diagram;
        if (tool.handle === null)
            return;
        tool.doMouseMove();
        const adorn = tool.handle.part;
        const wall = adorn.adornedPart;
        tool.joinColinearWalls();
        tool.maybeSplitWall();
        // reset joinedWall
        tool.joinedWalls.clear();
        // update all rooms TODO only update relevant rooms
        const set = new go.Set();
        set.add(wall);
        fp.updateAllRoomBoundaries(set);
        this.stopTool();
    }
    /**
     * End the wall reshaping transaction.
     * If a wall is reshaped to less than 1 document unit long, remove it from the Floorplan.
     * If tool was cancelled with Esc key, reset reshaping wall / wall parts to what they were before.
     * Remove guidelines and update wall dimension links. Commit transaction.
     */
    doDeactivate() {
        const diagram = this.diagram;
        const fp = diagram;
        // if a wall reshaped to length < 1 px, remove it
        if (this.handle === null)
            return;
        const adorn = this.handle.part;
        const wall = adorn.adornedPart;
        const sPt = wall.data.startpoint;
        const ePt = wall.data.endpoint;
        const length = Math.sqrt(sPt.distanceSquared(ePt.x, ePt.y));
        if (length < 1) {
            diagram.remove(wall); // remove wall
            wall.memberParts.iterator.each(function (member) {
                diagram.remove(member);
            }); // remove wall's parts
            const wallDimensionLinkPointNodes = [];
            fp.pointNodes.iterator.each(function (node) {
                if (node.data.key.indexOf(wall.data.key) !== -1)
                    wallDimensionLinkPointNodes.push(node);
            });
            if (wallDimensionLinkPointNodes.length === 2) {
                diagram.remove(wallDimensionLinkPointNodes[0]);
                diagram.remove(wallDimensionLinkPointNodes[1]);
            }
        }
        // remove wall's dimension links if tool cancelled via esc key
        if (diagram.lastInput.key === 'Escape' && !this.isBuilding) {
            diagram.skipsUndoManager = true;
            diagram.startTransaction('reset to old data');
            if (this.handle.name === 'sPt')
                wall.data.startpoint = this.returnPoint;
            else
                wall.data.endpoint = this.returnPoint;
            this.performAllMitering();
            fp.updateWall(wall);
            if (this.returnData) {
                this.returnData.iterator.each(function (kvp) {
                    const key = kvp.key;
                    const loc = kvp.value;
                    const wallPart = diagram.findPartForKey(key);
                    wallPart.location = loc;
                    wallPart.rotateObject.angle = wall.rotateObject.angle;
                });
            }
            diagram.commitTransaction('reset to old data');
            diagram.skipsUndoManager = false;
        }
        // remove guide line point nodes
        const glPoints = this.diagram.findNodesByExample({
            category: 'GLPointNode',
        });
        diagram.removeParts(glPoints, true);
        fp.updateWallDimensions();
        // commit transaction, deactivate tool
        diagram.commitTransaction(this.name);
        this.isActive = false;
    }
    /**
     * Creates an adornment with 2 handles
     * @param {go.Shape} selelt The adorned wall's Shape element
     * @return {go.Adornment}
     */
    makeAdornment(selelt) {
        const adornment = new go.Adornment();
        adornment.type = go.Panel.Spot;
        adornment.locationObjectName = 'BODY';
        adornment.locationSpot = go.Spot.Center;
        let h = new go.Shape();
        h.name = 'BODY';
        h.fill = null;
        h.stroke = null;
        h.strokeWidth = 0;
        adornment.add(h);
        h = this.makeHandle();
        h.name = 'sPt';
        adornment.add(h);
        h = this.makeHandle();
        h.name = 'ePt';
        adornment.add(h);
        adornment.category = this.name;
        adornment.adornedObject = selelt;
        return adornment;
    }
    /**
     * Creates a basic handle archetype (a small blue diamond)
     * @return {go.Shape}
     */
    makeHandle() {
        const h = this.handleArchetype;
        return h.copy();
    }
    /**
     * Calculate the angle and length made from the mousepoint and the non-moving handle; used to reshape wall when holding SHIFT
     * @param {go.Point} mousePt The mouse cursors coordinate position
     */
    calcAngleAndLengthFromHandle(mousePt) {
        const tool = this;
        const h = this.handle;
        if (h === null)
            return;
        if (tool.adornedShape === null)
            return;
        let otherH = null;
        const node = tool.adornedShape.part;
        if (node === null)
            return;
        const adornments = node.adornments.iterator;
        let adornment;
        while (adornments.next()) {
            const a = adornments.value;
            if (a.category === tool.name) {
                adornment = a;
            }
        }
        if (adornment === undefined)
            return;
        const atr = adornment.elements;
        while (atr.next()) {
            const e = atr.value;
            if (e.name !== undefined && e.name !== h.name) {
                otherH = e;
            }
        }
        // calc angle from otherH against the horizontal
        if (otherH === null)
            return;
        const otherHandlePt = otherH.getDocumentPoint(go.Spot.Center);
        const deltaY = mousePt.y - otherHandlePt.y;
        const deltaX = mousePt.x - otherHandlePt.x;
        let angle = Math.atan2(deltaY, deltaX) * (180 / Math.PI);
        // because atan2 goes from -180 to +180 and we want it to be 0-360
        // so -90 becomes 270, etc.
        if (angle < 0)
            angle += 360;
        tool.angle = angle;
        const distanceBetween = Math.sqrt(mousePt.distanceSquared(otherHandlePt.x, otherHandlePt.y));
        tool.length = distanceBetween;
    }
    /**
     * Takes a point -- returns a new point that is closest to the original point that conforms to the grid snap
     * @param {go.Point} point The point to snap to grid
     * @return {go.Point}
     */
    snapPointToGrid(point) {
        const diagram = this.diagram;
        const gs = diagram.toolManager.draggingTool.isGridSnapEnabled
            ? diagram.model.modelData.gridSize
            : 1;
        const newx = gs * Math.round(point.x / gs);
        const newy = gs * Math.round(point.y / gs);
        const newPt = new go.Point(newx, newy);
        return newPt;
    }
    /**
     * Reshapes the wall's geometry, updates model data
     * @param {go.Point} newPoint The point to move the reshaping wall's reshaping endpoint to
     */
    reshape(newPoint) {
        const diagram = this.diagram;
        const tool = this;
        const shape = this.adornedShape;
        if (shape === null)
            return;
        if (tool.handle === null)
            return;
        const node = shape.part;
        if (node === null)
            return;
        // if user holds SHIFT, make angle between startPoint / endPoint and the horizontal line a multiple of 45
        if (this.diagram.lastInput.shift && !this.isIntersecting) {
            let sPt; // the stationary point -- the point at the handle that is not being adjusted
            if (tool.handle.name === 'sPt')
                sPt = node.data.endpoint;
            else
                sPt = node.data.startpoint;
            const oldGridSize = diagram.model.modelData.gridSize;
            let gridSize = diagram.model.modelData.gridSize;
            // if gridSnapping is disabled, just set 'gridSize' var to 1 so it doesn't affect endPoint calculations
            if (!this.diagram.toolManager.draggingTool.isGridSnapEnabled)
                gridSize = 1;
            // these are set in mouseMove's call to calcAngleAndLengthFromHandle()
            const angle = tool.angle;
            const length = tool.length;
            // snap to 90 degrees
            if (angle > 67.5 && angle < 112.5) {
                let newy = sPt.y + length;
                newy = gridSize * Math.round(newy / gridSize);
                newPoint = new go.Point(sPt.x, newy);
            }
            // snap to 180 degrees
            if (angle > 112.5 && angle < 202.5) {
                let newx = sPt.x - length;
                newx = gridSize * Math.round(newx / gridSize);
                newPoint = new go.Point(newx, sPt.y);
            }
            // snap to 270 degrees
            if (angle > 247.5 && angle < 292.5) {
                let newy = sPt.y - length;
                newy = gridSize * Math.round(newy / gridSize);
                newPoint = new go.Point(sPt.x, newy);
            }
            // snap to 360 degrees
            if (angle > 337.5 || angle < 22.5) {
                let newx = sPt.x + length;
                newx = gridSize * Math.round(newx / gridSize);
                newPoint = new go.Point(newx, sPt.y);
            }
            // snap to 45 degrees
            if (angle > 22.5 && angle < 67.5) {
                let newx = Math.sin(0.785) * length;
                newx = gridSize * Math.round(newx / gridSize) + sPt.x;
                let newy = Math.cos(0.785) * length;
                newy = gridSize * Math.round(newy / gridSize) + sPt.y;
                newPoint = new go.Point(newx, newy);
            }
            // snap to 135 degrees
            if (angle > 112.5 && angle < 157.5) {
                let newx = Math.sin(0.785) * length;
                newx = sPt.x - gridSize * Math.round(newx / gridSize);
                let newy = Math.cos(0.785) * length;
                newy = gridSize * Math.round(newy / gridSize) + sPt.y;
                newPoint = new go.Point(newx, newy);
            }
            // snap to 225 degrees
            if (angle > 202.5 && angle < 247.5) {
                let newx = Math.sin(0.785) * length;
                newx = sPt.x - gridSize * Math.round(newx / gridSize);
                let newy = Math.cos(0.785) * length;
                newy = sPt.y - gridSize * Math.round(newy / gridSize);
                newPoint = new go.Point(newx, newy);
            }
            // snap to 315 degrees
            if (angle > 292.5 && angle < 337.5) {
                let newx = Math.sin(0.785) * length;
                newx = sPt.x + gridSize * Math.round(newx / gridSize);
                let newy = Math.cos(0.785) * length;
                newy = sPt.y - gridSize * Math.round(newy / gridSize);
                newPoint = new go.Point(newx, newy);
            }
            gridSize = oldGridSize; // set gridSize back to what it used to be in case gridSnap is enabled again
        }
        if (this.diagram.toolManager.draggingTool.isGridSnapEnabled &&
            !tool.isIntersecting &&
            !this.diagram.lastInput.shift) {
            newPoint = this.snapPointToGrid(newPoint);
        }
        else {
            newPoint = new go.Point(newPoint.x, newPoint.y);
        }
        const type = tool.handle.name;
        if (type === undefined)
            return;
        const stationaryPt = type === 'sPt' ? node.data.endpoint : node.data.startpoint;
        const movingPt = type === 'sPt' ? node.data.startpoint : node.data.endpoint;
        this.reshapeWall(node, stationaryPt, movingPt, newPoint, diagram);
        this.updateAdornments(node);
        this.showMatches();
        const fp = diagram;
        fp.updateWallDimensions();
    } // end reshape()
    /**
     * Show if the wall (at the adjustment handle being moved) lines up with other wall edges
     */
    showMatches() {
        const tool = this;
        const diagram = tool.diagram;
        if (!diagram.model.modelData.preferences.showWallGuidelines)
            return;
        if (tool.adornedShape === null)
            return;
        if (tool.handle === null)
            return;
        const wall = tool.adornedShape.part;
        let comparePt;
        if (tool.handle.name === 'sPt')
            comparePt = wall.data.startpoint;
        else
            comparePt = wall.data.endpoint;
        // the wall attached to the handle being manipulated
        const hWall = tool.adornedShape.part;
        // delete any old guideline points (these are used to show guidelines, must be cleared before a new guideline can be shown)
        const glPoints = diagram.findNodesByExample({
            category: 'GLPointNode',
        });
        diagram.removeParts(glPoints, true);
        const walls = this.diagram.findNodesByExample({
            category: 'WallGroup',
        });
        walls.iterator.each(function (w) {
            if (hWall !== null && w.data.key !== hWall.data.key) {
                const shape = w.findObject('SHAPE');
                const pt1 = w.data.startpoint;
                const pt2 = w.data.endpoint;
                tool.checkPtLinedUp(pt1, comparePt.x, pt1.x, comparePt);
                tool.checkPtLinedUp(pt1, comparePt.y, pt1.y, comparePt);
                tool.checkPtLinedUp(pt2, comparePt.x, pt2.x, comparePt);
                tool.checkPtLinedUp(pt2, comparePt.y, pt2.y, comparePt);
            }
        });
    }
    /**
     * Checks if there exists a horiontal or vertical line (decided by 'coord' parameter) between pt and compare pt
     * if so, draws a link between the two, letting the user know the wall they're reshaping lines up with another's edge
     * @param {go.Point} pt
     * @param {number} comparePtCoord
     * @param {number} ptCoord
     * @param {go.Point} comparePt
     */
    checkPtLinedUp(pt, comparePtCoord, ptCoord, comparePt) {
        function makeGuideLinePoint() {
            const $ = go.GraphObject.make;
            return $(go.Node, 'Spot', {
                locationSpot: go.Spot.TopLeft,
                locationObjectName: 'SHAPE',
                desiredSize: new go.Size(1, 1),
            }, new go.Binding('location', 'loc', go.Point.parse).makeTwoWay(go.Point.stringify), $(go.Shape, { stroke: null, strokeWidth: 1, name: 'SHAPE', fill: 'black' }));
        }
        function makeGuideLineLink() {
            const $ = go.GraphObject.make;
            return $(go.Link, $(go.Shape, { stroke: 'black', strokeWidth: 2, name: 'SHAPE' }, new go.Binding('strokeWidth', 'width'), new go.Binding('stroke', 'stroke')));
        }
        const diagram = this.diagram;
        const errorMargin = Math.abs(comparePtCoord - ptCoord);
        if (errorMargin < 2) {
            const data = { category: 'GLPointNode', loc: go.Point.stringify(pt), key: 'glpt' };
            const data2 = {
                key: 'movingPt',
                category: 'GLPointNode',
                loc: go.Point.stringify(comparePt),
            };
            const data3 = {
                key: 'guideline',
                category: 'guideLine',
                from: 'movingPt',
                to: data.key,
                stroke: 'blue',
            };
            const GLPoint1 = makeGuideLinePoint();
            const GLPoint2 = makeGuideLinePoint();
            const GLLink = makeGuideLineLink();
            diagram.add(GLPoint1);
            diagram.add(GLPoint2);
            diagram.add(GLLink);
            GLPoint1.data = data;
            GLPoint2.data = data2;
            GLLink.data = data3;
            GLLink.fromNode = GLPoint1;
            GLLink.toNode = GLPoint2;
        }
    }
    /**
     * Maintain position of all wallParts as best as possible when a wall is being reshaped.
     * Position is relative to the distance a wallPart's location is from the stationaryPoint of the wall.
     * This is called during WallReshapingTool's reshape function.
     * @param {go.Group} wall The wall being reshaped
     * @param {go.Point} stationaryPoint The endpoint of the wall not being reshaped
     * @param {go.Point} movingPoint The endpoint of the wall being reshaped
     * @param {go.Point} newPoint The point that movingPoint is going to
     * @param {go.Diagram} diagram The diagram belonging WallReshapingTool belongs to
     */
    reshapeWall(wall, stationaryPoint, movingPoint, newPoint, diagram) {
        const tool = this;
        const wallParts = wall.memberParts;
        const arr = [];
        const oldAngle = wall.data.startpoint.directionPoint(wall.data.endpoint);
        wallParts.iterator.each(function (part) {
            arr.push(part);
        });
        // remember the distance each wall part's location was from the stationary point; store these in a Map
        const distancesMap = new go.Map( /*"string", "number"*/);
        let closestPart = null;
        let closestDistance = Number.MAX_VALUE;
        for (let i = 0; i < arr.length; i++) {
            const part = arr[i];
            const distanceToStationaryPt = Math.sqrt(part.location.distanceSquaredPoint(stationaryPoint));
            distancesMap.add(part.data.key, distanceToStationaryPt);
            // distanceToMovingPt is determined by whichever endpoint of the wallpart is closest to movingPoint
            const endpoints = tool.getWallPartEndpoints(part);
            const distanceToMovingPt = Math.min(Math.sqrt(endpoints[0].distanceSquaredPoint(movingPoint)), Math.sqrt(endpoints[1].distanceSquaredPoint(movingPoint)));
            // find and store the closest wallPart to the movingPt
            if (distanceToMovingPt < closestDistance) {
                closestDistance = distanceToMovingPt;
                closestPart = part;
            }
        }
        // if the proposed newPoint would make it so the wall would reshape past closestPart, set newPoint to the edge point of closest part
        if (closestPart !== null) {
            const loc = closestPart.location;
            const partLength = closestPart.data.length;
            const angle = oldAngle;
            const point1 = new go.Point(loc.x + partLength / 2, loc.y);
            const point2 = new go.Point(loc.x - partLength / 2, loc.y);
            point1.offset(-loc.x, -loc.y).rotate(angle).offset(loc.x, loc.y);
            point2.offset(-loc.x, -loc.y).rotate(angle).offset(loc.x, loc.y);
            const distance1 = Math.sqrt(stationaryPoint.distanceSquaredPoint(point1));
            const distance2 = Math.sqrt(stationaryPoint.distanceSquaredPoint(point2));
            let minLength;
            let newLoc;
            if (distance1 > distance2) {
                minLength = distance1;
                newLoc = point1;
            }
            else {
                minLength = distance2;
                newLoc = point2;
            }
            const testDistance = Math.sqrt(stationaryPoint.distanceSquaredPoint(newPoint));
            if (testDistance < minLength)
                newPoint = newLoc;
        }
        // reshape the wall
        if (movingPoint === wall.data.endpoint) {
            diagram.model.setDataProperty(wall.data, 'endpoint', newPoint);
        }
        else {
            diagram.model.setDataProperty(wall.data, 'startpoint', newPoint);
        }
        const fp = diagram;
        fp.updateWall(wall);
        // for each wallPart, maintain relative distance from the stationaryPoint
        distancesMap.iterator.each(function (kvp) {
            const wallPart = diagram.findPartForKey(kvp.key);
            const distance = kvp.value;
            const wallLength = Math.sqrt(stationaryPoint.distanceSquaredPoint(movingPoint));
            const newLoc = new go.Point(stationaryPoint.x + (distance / wallLength) * (movingPoint.x - stationaryPoint.x), stationaryPoint.y + (distance / wallLength) * (movingPoint.y - stationaryPoint.y));
            wallPart.location = newLoc;
            // calculate the new angle
            const sToE = wall.data.startpoint.directionPoint(wall.data.endpoint);
            const eToS = wall.data.endpoint.directionPoint(wall.data.startpoint);
            const diffS = Math.abs(wallPart.angle - sToE);
            const diffE = Math.abs(wallPart.angle - eToS);
            const newAngle = diffS < diffE ? sToE : eToS;
            wallPart.angle = newAngle;
        });
    } // end reshapeWall()
    /**
     * Find and return an array of the endpoints of a given wallpart (window or door)
     * @param {go.Part} wallPart A Wall Part -- i.e. Door Node, Window Node
     * @return {Array<go.Point>}
     */
    getWallPartEndpoints(wallPart) {
        const loc = wallPart.location;
        const partLength = wallPart.data.length;
        let angle = 0;
        if (wallPart.containingGroup !== null)
            angle = wallPart.containingGroup.rotateObject.angle;
        else
            angle = 180;
        const point1 = new go.Point(loc.x + partLength / 2, loc.y);
        const point2 = new go.Point(loc.x - partLength / 2, loc.y);
        point1.offset(-loc.x, -loc.y).rotate(angle).offset(loc.x, loc.y);
        point2.offset(-loc.x, -loc.y).rotate(angle).offset(loc.x, loc.y);
        const arr = new Array();
        arr.push(point1);
        arr.push(point2);
        return arr;
    }
}
// export = WallReshapingTool;
