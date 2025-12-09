// This variation on ForceDirectedLayout does not move any selected Nodes
// but does move all other nodes (vertexes).
class ContinuousForceDirectedLayout extends go.ForceDirectedLayout {
    constructor(init) {
    super();
    if (init) Object.assign(this, init);
    }

    isFixed(v) {
    return v.node.isSelected;
    }

    // optimization: reuse the ForceDirectedNetwork rather than re-create it each time
    doLayout(coll) {
    if (!this._isObserving) {
        this._isObserving = true;
        // cacheing the network means we need to recreate it if nodes or links have been added or removed or relinked,
        // so we need to track structural model changes to discard the saved network.
        this.diagram.addModelChangedListener(e => {
        // modelChanges include a few cases that we don't actually care about, such as
        // "nodeCategory" or "linkToPortId", but we'll go ahead and recreate the network anyway.
        // Also clear the network when replacing the model.
        if (e.modelChange !== '' || (e.change === go.ChangeType.Transaction && e.propertyName === 'StartingFirstTransaction')) {
            this.network = null;
        }
        });
    }
    var net = this.network;
    if (net === null) {
        // the first time, just create the network as normal
        this.network = net = this.makeNetwork(coll);
    } else {
        // but on reuse we need to update the LayoutVertex.bounds for selected nodes
        this.diagram.nodes.each(n => {
        var v = net.findVertex(n);
        if (v !== null) v.bounds = n.actualBounds;
        });
    }
    // now perform the normal layout
    super.doLayout(coll);
    // doLayout normally discards the LayoutNetwork by setting Layout.network to null;
    // here we remember it for next time
    this.network = net;

    // in the future, don't allow nodes to move as far
    //this.initialTemperature = x => 10;
    }
}
// end ContinuousForceDirectedLayout

// Expose globally for non-module scripts
window.ContinuousForceDirectedLayout = ContinuousForceDirectedLayout;