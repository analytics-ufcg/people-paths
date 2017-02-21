
function renderChart(chartId) {
    d3.select("#" + chartId).selectAll("*").remove();

    var svg = d3.select("#" + chartId),
        width = +svg.attr("width"),
        height = +svg.attr("height");

    var color = d3.scaleOrdinal(d3.schemeCategory20);

    var simulation = d3.forceSimulation()
        .force("link", d3.forceLink().id(function(d) { return d.id; }).distance(function(){return 300;}))
        .force("charge", d3.forceManyBody())
        .force("center", d3.forceCenter(width / 2, height / 2))
        .force("collide",d3.forceCollide( function(d){return d.r * 5 }).iterations(16) );

    if (chartId == "chart1"){
        if ($("#dropdown1").text() == "Low income") {
            if ($("#dropdown2").text() == "Weekday") {
                nodes_file = "../low_income_not_weekend_nodes_pagerank.csv";
                edges_file = "../low_income_not_weekend_edges.csv";
            } else {
                nodes_file = "../low_income_weekend_nodes_pagerank.csv";
                edges_file = "../low_income_weekend_edges.csv";
            }
        } else {
            if ($("#dropdown2").text() == "Weekday") {
                nodes_file = "../high_income_not_weekend_nodes_pagerank.csv";
                edges_file = "../high_income_not_weekend_edges.csv";
            } else {
                nodes_file = "../high_income_weekend_nodes_pagerank.csv";
                edges_file = "../high_income_weekend_edges.csv";
            }
        }
    } else {
        if ($("#dropdown3").text() == "Low income") {
            if ($("#dropdown4").text() == "Weekday") {
                nodes_file = "../low_income_not_weekend_nodes_pagerank.csv";
                edges_file = "../low_income_not_weekend_edges.csv";
            } else {
                nodes_file = "../low_income_weekend_nodes_pagerank.csv";
                edges_file = "../low_income_weekend_edges.csv";
            }
        } else {
            if ($("#dropdown4").text() == "Weekday") {
                nodes_file = "../high_income_not_weekend_nodes_pagerank.csv";
                edges_file = "../high_income_not_weekend_edges.csv";
            } else {
                nodes_file = "../high_income_weekend_nodes_pagerank.csv";
                edges_file = "../high_income_weekend_edges.csv";
            }
        }
    }

    console.log(nodes_file);
    console.log(edges_file);

    d3.csv(nodes_file, function(rank) {
        d3.csv(edges_file, function(edges) {
            var graph = {
                "nodes": rank,
                "links": edges
            };

            console.log(graph);

            var weightScale = d3.scaleLinear().domain(d3.extent(graph.links.map(function(item){return item.weight}))).range([1,5]);

            var link = svg.append("g")
              .attr("class", "links")
            .selectAll("line")
            .data(graph.links)
            .enter().append("line")
              .attr("stroke-width", function(d) { return weightScale(d.weight); });

            var nodeSpace = svg
                .selectAll("g")
                .data(graph.nodes)
                .enter().append("g")

            var nodeScale = d3.scaleLinear().domain(d3.extent(graph.nodes.map(function(d){return d.pageranks;}))).range([1,10]);

            var node = nodeSpace
                .append("circle")
                .attr("r", function(d) { return nodeScale(d.pageranks); })
                .attr("fill", function(d) { return "yellow"; })
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

            function ticked() {
                link
                    .attr("x1", function(d) { return d.source.x; })
                    .attr("y1", function(d) { return d.source.y; })
                    .attr("x2", function(d) { return d.target.x; })
                    .attr("y2", function(d) { return d.target.y; });

                node
                    .attr("cx", function(d) { return d.x; })
                    .attr("cy", function(d) { return d.y; });

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

$(function(){

    $("#dropdown1").html("Low income" + '<span class="caret"></span>');
    $("#dropdown2").html("Weekday" + '<span class="caret"></span>');
    $("#dropdown3").html("Low income" + '<span class="caret"></span>');
    $("#dropdown4").html("Weekday" + '<span class="caret"></span>');

    renderChart("chart1");
    renderChart("chart2");

    $("#options1").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown1").text() != text) {
            $("#dropdown1").html(text + '<span class="caret"></span>');
            renderChart("chart1");
        }
    });

    $("#options2").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown2").text() != text) {
            $("#dropdown2").html(text + '<span class="caret"></span>');
            renderChart("chart1");
        }
    });

    $("#options3").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown3").text() != text) {
            $("#dropdown3").html(text + '<span class="caret"></span>');
            renderChart("chart2");
        }
    });

    $("#options4").on('click', 'li a', function(){
        var text = $(this).text();
        if ($("#dropdown4").text() != text) {
            $("#dropdown4").html(text + '<span class="caret"></span>');
            renderChart("chart2");
        }
    });

});