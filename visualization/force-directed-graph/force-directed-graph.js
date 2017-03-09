
function renderChart(chartId, nodes_file, edges_file, edgesScale) {
    d3.select("#" + chartId).selectAll("*").remove();

    var svg = d3.select("#" + chartId),
        width = $( document ).width() / 2,
        height = $( document ).height() - 200;

    var color;

    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(function(){return 100;}))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide",d3.forceCollide( function(d){return d.r * 3 }).iterations(2) );

    if (chartId == "chart1"){
        color = "#d95f02";
    } else {
        color = "#1b9e77";
    }

    d3.csv(nodes_file, function(rank) {
        d3.csv(edges_file, function(edges) {
            edges.sort(function(e1, e2){
                return e2.weight - e1.weight;
            });

            edges = edges.filter(function(d){return d.source != d.target;}).slice(0, 200);

            console.log(edges);

            var usedNodes = new Set();
            for (var i = 0; i < edges.length; i++) {
                usedNodes.add(edges[i].source);
                usedNodes.add(edges[i].target);
            }

            var graph = {
                "nodes": rank.filter(function(d){return usedNodes.has(d.id);}),
                "links": edges
            };

            var nodes = graph.nodes,
                nodeById = d3.map(nodes, function(d) { return d.id; }),
                links = graph.links,
                bilinks = [];

            links.forEach(function(link) {
                var s = link.source = nodeById.get(link.source),
                    t = link.target = nodeById.get(link.target),
                    i = {}, // intermediate node
                    w = link.weight;
                nodes.push(i);
                links.push({source: s, target: i}, {source: i, target: t});
                bilinks.push([s, i, t, w]);
            });

            var link = svg
                .style("width", width)
                .style("height", height)
            .append("g")
              .attr("class", "links")
            .selectAll("line")
            .data(bilinks)
            .enter().append("path")
              .attr("stroke-width", function(d) { return edgesScale(+d[3]); });
              //.attr("opacity", 0.2);

            var nodesNotNull = graph.nodes.filter(function(d) { return d.id; });

            var nodeSpace = svg
                .selectAll("g1")
                .data(nodesNotNull)
                .enter().append("g");

            var nodeScale = d3.scaleLinear().domain(d3.extent(nodesNotNull.map(function(d){return +d.pageranks;}))).range([3, 15]);

            var node = nodeSpace
                .append("circle")
                .attr("r", function(d) { return nodeScale(+d.pageranks); })
                .attr("fill", color)
                .call(d3.drag()
                    .on("start", dragstarted)
                    .on("drag", dragged)
                    .on("end", dragended));

            node.append("title")
              .text(function(d) { return d.id; });

            var nodeText = nodeSpace.append("text")
                .text(function(d){return d.id;})
                .attr("font-family", "sans-serif")
                .attr("font-size", "10px");

            simulation
              .nodes(graph.nodes)
              .on("tick", ticked);

            simulation.force("link")
              .links(graph.links);

            function positionLink(d) {
                return "M" + d[0].x + "," + d[0].y
                     + "S" + d[1].x + "," + d[1].y
                     + " " + d[2].x + "," + d[2].y;
            }

            function positionNode(d) {
                return "translate(" + d.x + "," + d.y + ")";
            }


            function ticked() {
                link.attr("d", positionLink);
                node.attr("transform", positionNode);

                /*link
                    .attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node
                    .attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });*/

                nodeText
                    .attr("dx", function(d) { return d.x; })
                    .attr("dy", function(d) { return d.y; });
            }
        });
    });

    function dragstarted(d) {
      if (!d3.event.active) simulation.alphaTarget(0.3).restart();
      d.fx = d.x;
      d.fy = d.y;
    }

    function dragged(d) {
      d.fx = d3.event.x;
      d.fy = d3.event.y;
    }

    function dragended(d) {
      if (!d3.event.active) simulation.alphaTarget(0);
      d.fx = null;
      d.fy = null;
    }
}

function getFiles() {
        if ($("#dropdown1").text() == "Low income") {
            if ($("#dropdown2").text() == "Weekday") {
                nodes_file1 = "low_income_not_weekend_nodes_pagerank.csv";
                edges_file1 = "low_income_not_weekend_edges.csv";
            } else {
                nodes_file1 = "low_income_weekend_nodes_pagerank.csv";
                edges_file1 = "low_income_weekend_edges.csv";
            }
        } else {
            if ($("#dropdown2").text() == "Weekday") {
                nodes_file1 = "high_income_not_weekend_nodes_pagerank.csv";
                edges_file1 = "high_income_not_weekend_edges.csv";
            } else {
                nodes_file1 = "high_income_weekend_nodes_pagerank.csv";
                edges_file1 = "high_income_weekend_edges.csv";
            }
        }

        if ($("#dropdown3").text() == "Low income") {
            if ($("#dropdown4").text() == "Weekday") {
                nodes_file2 = "low_income_not_weekend_nodes_pagerank.csv";
                edges_file2 = "low_income_not_weekend_edges.csv";
            } else {
                nodes_file2 = "low_income_weekend_nodes_pagerank.csv";
                edges_file2 = "low_income_weekend_edges.csv";
            }
        } else {
            if ($("#dropdown4").text() == "Weekday") {
                nodes_file2 = "high_income_not_weekend_nodes_pagerank.csv";
                edges_file2 = "high_income_not_weekend_edges.csv";
            } else {
                nodes_file2 = "high_income_weekend_nodes_pagerank.csv";
                edges_file2 = "high_income_weekend_edges.csv";
            }
        }

        return { "nodes_file1": nodes_file1, "edges_file1": edges_file1, "nodes_file2": nodes_file2, "edges_file2": edges_file2}
}

function renderBothCharts() {
    files = getFiles();

    d3.queue()
        .defer(d3.csv, files.edges_file1)
        .defer(d3.csv, files.edges_file2)
        .await(function(error, edges1, edges2){
            if (error) throw error;
            edges1.sort(function(e1, e2){
                return e2.weight - e1.weight;
            });

            edges1 = edges1.filter(function(d){return d.source != d.target;}).slice(0, 200);

            edges2.sort(function(e1, e2){
                return e2.weight - e1.weight;
            });

            edges2 = edges2.filter(function(d){return d.source != d.target;}).slice(0, 200);

            edges = edges1.concat(edges2);

            var edgesScale = d3.scaleLinear().domain(d3.extent(edges.map(function(item){return +item.weight}))).range([1,5]);

            renderChart("chart1", files.nodes_file1, files.edges_file1, edgesScale);
            renderChart("chart2", files.nodes_file2, files.edges_file2, edgesScale);
        });
}

$(function(){

    $("#dropdown1").html("Low income" + '<span class="caret"></span>');
    $("#dropdown2").html("Weekday" + '<span class="caret"></span>');
    $("#dropdown3").html("Low income" + '<span class="caret"></span>');
    $("#dropdown4").html("Weekday" + '<span class="caret"></span>');

    renderBothCharts();

    $("#options1").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown1").text() != text) {
            $("#dropdown1").html(text + '<span class="caret"></span>');
            renderBothCharts();
        }
    });

    $("#options2").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown2").text() != text) {
            $("#dropdown2").html(text + '<span class="caret"></span>');
            renderBothCharts();
        }
    });

    $("#options3").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown3").text() != text) {
            $("#dropdown3").html(text + '<span class="caret"></span>');
            renderBothCharts();
        }
    });

    $("#options4").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown4").text() != text) {
            $("#dropdown4").html(text + '<span class="caret"></span>');
            renderBothCharts();
        }
    });

});