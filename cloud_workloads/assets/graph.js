function MinionGraph(nodes, edges) {
    this.nodeRadius = 20;
    this.nodeRadiusActive = 25;
    this.nodeSep = 55;
    this.edgeSep = 15;
    this.rankSep = 200;
    this.rankDir = "LR";
    this.scaleExtentMin = 0;
    this.scaleExtentMax = 5;
    this.transitionDuration = 100;
    this.labelDx = 15;
    this.labelDy = 25;
    this.labelLineSpace = 20;
    this.margin = 20;

    this.nodes = nodes;
    this.edges = edges;
    this.dag = new dagreD3.Digraph();
    this.addNodes(this.nodes);
    this.addEdges(this.edges);
}

MinionGraph.prototype.addDefs = function(svg) {
    var $defs = svg.append("svg:defs");

    var $g1 = $defs.append('radialGradient')
        .attr('id', 'node-g1')
        .attr('cx', "40%")
        .attr('cy', "40%")
        .attr("r", "50%");
    $g1.append('stop')
        .attr('stop-color', '#999')
        .attr('offset', "0%");
    $g1.append('stop')
        .attr('stop-color', "#333")
        .attr('offset', "100%");

    var $g2 = $defs.append('radialGradient')
        .attr('id', 'node-g2')
        .attr('cx', "40%")
        .attr('cy', "40%")
        .attr("r", "50%");
    $g2.append('stop')
        .attr('stop-color', "#72bbc6")
        .attr('offset', "0%");
    $g2.append('stop')
        .attr('stop-color', '#1b4f56')
        .attr('offset', "100%");
}

MinionGraph.prototype.addNodes = function(nodes) {
    for (var i = 0; i < nodes.length; i++) {
        this.dag.addNode(nodes[i].id, nodes[i]);
    }
    return this;
};

MinionGraph.prototype.addEdges = function(edges) {
    for (var i = 0; i < edges.length; i++) {
        this.dag.addEdge(null, edges[i].source, edges[i].target, {});
    }
    return this;
};

MinionGraph.prototype.postRenderNodes = function(svgNodes) {

    var style = {
        dx: this.labelDx,
        dy: this.labelDy,
        spacing: this.labelLineSpace
    }
    var dag = this.dag;

    svgNodes.each(function(nodeId) {
        var dy = style.dy;
        var nodeObj = dag._nodes[nodeId].value;
        var $this = d3.select(this);
        $this.attr('node-id', nodeId);
        $this
            .append('text')
            .attr('class', 'node-id')
            .attr('dx', style.dx)
            .attr('dy', dy)
            .text(nodeObj.id);
        $this
            .append('text')
            .attr('class', 'node-roles')
                .attr('dx', style.dx)
                .attr('dy', dy += style.spacing)
                .text(nodeObj.roles);
        });
};

MinionGraph.prototype.postRenderEdges = function(svgEdges) {
    var dag = this.dag;
    svgEdges.each(function(edgeId) {
        edge = dag._edges[edgeId];
        d3.select(this).attr('source-node', edge.u);
    });
};

MinionGraph.prototype.alignAndCenter = function(element, outer_width, outer_height, zoom) {
    var inner_width = outer_width - (2 * this.margin);
    var inner_height = outer_height - (2 * this.margin);
    var dim = element.node().getBBox();
    var scale = 1;
    var xTranslate = this.margin;
    var yTranslate = this.margin;

    
    if (dim.width > inner_width || dim.height > inner_height) {
        var wScale = inner_width / dim.width;
        var hScale = inner_height / dim.height;
        scale = Math.min(wScale, hScale);
    }

    var scaleWidth = scale * dim.width;
    if (scaleWidth < inner_width) {
        xTranslate += (inner_width - scaleWidth) / 2;
    }

    var scaleHeight = scale * dim.height;
    if (scaleHeight < inner_height) {
        yTranslate += (inner_height - scaleHeight) / 2;
    }

    var transform = "translate(" + xTranslate + "," + yTranslate + ")";
    transform += " scale(" + scale + ")";
    element.attr('transform', transform);
    zoom.scale(scale);
    zoom.translate([xTranslate, yTranslate]);
}

MinionGraph.prototype.prepTooltip = function() {
    var $tooltip = d3.select('body').select('div.tooltip');
    if ($tooltip.empty()) {
        d3.select('body').append('div').classed('tooltip', true).text("Some garbage");
    }
}

MinionGraph.prototype.showTooltip = function(node) {
    var $row;
    var $tooltip = $("div.tooltip").first();
    var $table = $('<table></table>');

    // Id row
    $row = $('<tr></tr>');
    $('<td class="label">Id</td>').appendTo($row);
    $('<td class="value"></td>').html(node.id).appendTo($row);
    $row.appendTo($table);

    // roles row
    $row = $('<tr></tr>');
    $('<td class="label">Role</td>').appendTo($row);
    $('<td class="value">').html(node.roles).appendTo($row);
    $row.appendTo($table);

    // Cpu row
    $row = $('<tr></tr>');
    $('<td class="label">Cpu</td>').appendTo($row);
    $('<td class="value">').html(node.cpu_model).appendTo($row);
    $row.appendTo($table);

    // Cores row
    $row = $('<tr></tr>');
    $('<td class="label">Cores</td>').appendTo($row);
    $('<td class="value">').html(node.num_cpus).appendTo($row);
    $row.appendTo($table);

    // Memory
    $row = $('<tr></tr>');
    $('<td class="label">Ram</td>').appendTo($row);
    $('<td class="value">').html(node.memory + " MB").appendTo($row);
    $row.appendTo($table);

    $tooltip.html($table);

    $tooltip
        .css('opacity', 0.8)
        .css('left', (d3.event.pageX - $tooltip.width() - 60) + "px")
        .css('top', (d3.event.pageY + -30) + "px");
}

MinionGraph.prototype.hideTooltip = function() {
    d3.select('body')
        .select('div.tooltip')
        .style('opacity', 0)
        .style('top', 0)
        .style('left', 0);
}

MinionGraph.prototype.render = function(selector_string) {
    // Use jquery to get width and height of container
    var style = {
        nodeSep: this.nodeSep,
        edgeSep: this.edgeSep,
        rankSep: this.rankSep,
        rankDir: this.rankDir,
        minScale: this.scaleExtentMin,
        maxScale: this.scaleExtentMax,
        radius: this.nodeRadius,
        radiusActive: this.nodeRadiusActive,
        duration: this.transitionDuration
    }
    var $container = $(selector_string);
    var width = $container.width();
    var height = $container.height();
    var svg, svgNodes, svgEdges;
    var renderer = new dagreD3.Renderer();
    renderer.layout(
        dagreD3.layout()
            .nodeSep(style.nodeSep)
            .edgeSep(style.edgeSep)
            .rankSep(style.rankSep)
            .rankDir(style.rankDir)
    );

    this.prepTooltip();

    var oldDrawNodes = renderer.drawNodes();
    var oldDrawEdges = renderer.drawEdgePaths();
    
    function zoom() {
        svg.attr('transform', "translate(" + d3.event.translate +")scale(" +d3.event.scale + ")");
    }
   
    function customDrawNodes(graph, root) {
        var nodes = oldDrawNodes(graph, root);
        nodes.each(function(n) {
            d3.select(this)
                .on('mouseover', activateNode)
                .on('mouseout', deactivateNode)
                .append('circle')
                .attr('cx', 0)
                .attr('cy', 0)
                .attr('r', style.radius)
                .attr('fill', 'url(#node-g1)');
        });
        svgNodes = nodes;
        return nodes;
    }

    function customDrawEdges(graph, root) {
        var edges = oldDrawEdges(graph, root);
        svgEdges = edges;
        return edges;
    }

    function customPostRender(graph, root) {
        if (graph.isDirected() && root.select('#arrowhead').empty()) {
            root.select('defs')
                .append('svg:marker')
                .attr('id', 'arrowhead')
                .attr('viewBox', '0 0 10 10')
                .attr('refX', 8)
                .attr('refY', 5)
                .attr('markerUnits', 'strokewidth')
                .attr('markerWidth', 8)
                .attr('markerHeight', 5)
                .attr('orient', 'auto')
                .attr('style', 'fill: #333')
                .append('svg:path')
                .attr('d', 'M 0 0 L 10 5 L 0 10 z');
        }
    }

    var dag = this.dag;
    var showTooltip = this.showTooltip;
    function activateNode() {
        var $this = d3.select(this);
        $this.classed('active', true);
        $this.select('circle')
            .attr('fill', 'url(#node-g2)')
            .transition()
            .duration(style.duration)
            .attr('r', style.radiusActive);
        var child_edges = svg.selectAll(".edgePath[source-node=" + $this.attr('node-id') + "]")
            .classed('active', true);
        showTooltip(dag._nodes[$this.attr('node-id')].value);
    }

    var hideTooltip = this.hideTooltip;
    function deactivateNode() {
        var $this = d3.select(this);
        $this.classed('active', false);
        $this.select('circle')
            .attr('fill', 'url(#node-g1)')
            .transition()
            .duration(style.duration)
            .attr('r', style.radius);
        var child_edges = svg.selectAll(".edgePath[source-node=" + $this.attr('node-id') + "]")
            .classed('active', false);
        hideTooltip();
    }

    var zoom = d3.behavior.zoom()
        .scaleExtent([this.scaleExtentMin, this.scaleExtentMax])
        .on("zoom", zoom);

    svg = d3.select(selector_string)
        .append("svg")
        .classed('minion-graph', true)
        .attr('width', width)
        .attr('height', height)
        .append('g')
        .classed('zoom-container', true)
        .call(zoom)
        .append("g");
    this.addDefs(svg);

    renderer.drawNodes(customDrawNodes);
    renderer.drawEdgePaths(customDrawEdges);
    renderer.postRender(customPostRender);
    renderer.run(this.dag, svg);
    this.postRenderNodes(svgNodes);
    this.postRenderEdges(svgEdges);
    this.alignAndCenter(svg, width, height, zoom);
};

function renderPrettyRoles(roleMap, nodes) {
    for (var i = 0; i < nodes.length; i++) {
        var prettyRoles = [];
        for (var r = 0; r < nodes[i].roles.length; r++) {
            if (roleMap[nodes[i].roles[r]] !== undefined) {
                prettyRoles.push(roleMap[nodes[i].roles[r]]);
            }
            else {
                prettyRoles.push(nodes[i].roles[r]);
            }
        }
        prettyRoles = prettyRoles.join(', ');
        nodes[i].roles = prettyRoles;
    }
    return nodes;
}
