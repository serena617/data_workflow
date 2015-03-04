alert('como estas');

function plot_1d(raw_data, anchor, options) {
    // For testing purposes, raw_data is fed in, 
    // anchor is the dialog box, and options
    // are empty {}.




    options = {};
    color = '#0077cc';
    marker_size = 2;
    height = 450;
    width = 600;
    log_scale = false;
    grid = false;
    x_label = "Q [1/\u00C5]";
    y_label = "Intensity";
    title = "what";
    // interp = (typeof options.interp ==="undefined") ? "none" : options.interp;

    var data = [];
    for (var i=0; i<raw_data.length; i++) {
        // if (raw_data[i][1]>0 && raw_data[i][2]<raw_data[i][1]) {  data.push(raw_data[i]); };
	data.push(raw_data[i]);
    }
    // alert(raw_data);
    // alert(raw_data.length);

    var margin = {top: 40, right: 100, bottom: 60, left: 60},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = log_scale ? d3.scale.log().range([height, 0]) : d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(data, function(d) { return d[0]; })).nice();
    y.domain([d3.min(data, function(d) { return d[1]-d[2]; }),
	      d3.max(data, function(d) { return d[1]+d[2]; })]).nice();

    var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(8).tickFormat(d3.format("5.2g"));
    var xAxisMinor = d3.svg.axis().scale(x).orient("bottom").ticks(4).tickSize(3,3).tickSubdivide(4).tickFormat('');
    var yAxis = d3.svg.axis().scale(y).orient("left").ticks(4).tickFormat(d3.format("5.2g"));    
    var yAxisMinor = d3.svg.axis().scale(y).orient("left").ticks(4).tickSize(3,3).tickSubdivide(4).tickFormat('');
    
    // Remove old plot
    d3.select(anchor).select("svg").remove();
    
    var svg = d3.select(anchor).append("svg")
      .attr("class", "default_1d")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxisMinor);
    svg.append("g").attr("class", "y axis").call(yAxis)
    svg.append("g").attr("class", "y axis").call(yAxisMinor)
    
    // Create X axis label   
    svg.append("text")
    .attr("x", width)
    .attr("y",  height+40)
    .attr("font-size", "12px")
    .style("text-anchor", "end")
    .text(x_label);

    // Create Y axis label
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 10-margin.left)
    .attr("x", 40-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text(y_label);

    // Create title
    svg.append("text")
    .attr("x", width/2.0 )
    .attr("y",  -10)
    .attr("font-size", "16px")
    .style("text-anchor", "middle")
    .text(title);

    // Make or remove grid
    if (grid == true){
	// If grid checkbox is checked, add grid
	xGrid = svg.append("g")
	.attr("class", "grid")
	.attr("transform", "translate(0," + height + ")")
	.call(xAxis
	.tickSize(-height, 0, 0)
	.tickFormat("")
	)
	yGrid = svg.append("g")
	.attr("class", "grid")
	.call(yAxis
	.tickSize(-width, 0, 0)
	.tickFormat("")
	)
    }
    else if (grid == false && typeof xGrid !== 'undefined' && typeof yGrid !== 'undefined'){
	// If grid checkbox is unchecked and a grid already exists, remove grid
	svg.select("xGrid").remove();
	svg.select("yGrid").remove();
    }

    // Plot the points
    svg.selectAll('circle')
	.data(data)
	.enter()
	.append('circle')
	.attr("cx", function(d) { return x(d[0]); })
	.attr("cy", function(d) { return y(d[1]); })
	.attr("r", marker_size)
	.style('fill', color);

    // Error bars
    var err = svg.selectAll('svg')
	.data(function(d) { return data; })
	.enter();
	    // Append vertical dotted line
	    err.append("line").attr("x1", function(d) { return (x(d[0])); })
		.attr("y1", function(d) { return (y(d[1]-d[2])); })
		.attr("x2", function(d) { return (x(d[0])); })
		.attr("y2", function(d) { return (y(d[1]+d[2])); })
		.attr("stroke-width", marker_size/2)
		.attr("stroke", color)
		.attr("stroke-dasharray", "2,2")
		.attr("opacity", 0.7);
	    // Append horizontal top line
	    err.append("line").attr("x1", function(d) { return (x(d[0])-parseFloat(marker_size)); })
		.attr("y1", function(d) { return (y(d[1]+d[2])); })
		.attr("x2", function(d) { return (x(d[0])+parseFloat(marker_size)); })
		.attr("y2", function(d) { return (y(d[1]+d[2])); })
		.attr("stroke-width", marker_size/2)
		.attr("stroke", color);
	    // Append horizontal bottom line
	    err.append("line").attr("x1", function(d) { return (x(d[0])-parseFloat(marker_size)); })
		.attr("y1", function(d) { return (y(d[1]-d[2])); })
		.attr("x2", function(d) { return (x(d[0])+parseFloat(marker_size)); })
		.attr("y2", function(d) { return (y(d[1]-d[2])); })
		.attr("stroke-width", marker_size/2)
		.attr("stroke", color);

    // Interpolate
    // if (interp !== 'none'){
// 	alert(interp);
	svg.select("path").remove();
	var interp_line = d3.svg.line()
	    .interpolate("linear")
	    .x(function(d) { console.log(d[0]); return x(d[0]); })
	    .y(function(d) { console.log(d[1]); return y(d[1]); });
	svg.append("path")
	    .attr("d", interp_line(data))
	    .attr("fill", "none")
	    .attr("stroke", "grey")
	    .attr("stroke-width", 1);
    // }
    // else if (interp === 'none'){
// 	svg.select("path").remove();
//    }


  // Get data values on hover event
  var bisect = d3.bisector(function(d) {return d[0];}).left;
  var focus = svg.append("g")
	.attr("class", "focus")
	.style("display", "none");
  focus.append("circle")
	.attr("r", 4.5);
  focus.append("text")
	.attr("x", 9)
	.attr("dy", "-.15em");
  svg.append("rect")
	.attr("class", "overlay")
	.attr("width", width)
	.attr("height", height)
	.on("mouseover", function() { focus.style("display", null); })
	.on("mouseout", function() { focus.style("display", "none"); })
	.on("mousemove", mousemove);
  function mousemove(){
	var x0 = x.invert(d3.mouse(this)[0]);
	var i = bisect(data, x0, 1);
	var d0 = data[i-1];
	var d1 = data[i];
	var d = x0 - d0[0] > d1[0] - x0 ? d1 : d0;
	focus.attr("transform", "translate(" + x(d[0]) + "," + y(d[1]) + ")");
	focus.select("text").text(d[0] + ", " + d[1] + "\xB1" + d[2]);
  }

}


// $("#plot_anchor").ready(function(){
// 	$("#plot_anchor").resizable();
// 	$("#plot_anchor").attr("class", "default_1d ui-widget-content");
// 	$("#plot_anchor").prepend("<h3 class='ui-widget-header'>Workspace</h3>");
// });

function get_color(i, n_max) {
    var n_divs = 4.0;
    var phase = 1.0*i/n_max;
    var max_i = 210;
    if (phase<1.0/n_divs) {
        b = max_i;
        r = 0;
        g = Math.round(max_i*Math.abs(Math.sin(Math.PI/2.0*i/n_max*n_divs)));
    } else if (phase<2.0/n_divs) {
        b = Math.round(max_i*Math.abs(Math.cos(Math.PI/2.0*i/n_max*n_divs)));
        r = 0;
        g = max_i;
    } else if (phase<3.0/n_divs) {
        b = 0;
        r = Math.round(max_i*Math.abs(Math.sin(Math.PI/2.0*i/n_max*n_divs)));
        g = max_i;
    } else if (phase<4.0/n_divs) {
        b = 0;
        r = max_i;
        g = Math.round(max_i*Math.abs(Math.cos(Math.PI/2.0*i/n_max*n_divs)));
    }
    r = r + 30;
    g = g + 30;
    return 'rgb('+r+','+g+','+b+')';
}

function plot_2d(data, qx, qy, max_iq, options) {
    options = (typeof options === "undefined") ? {} : options;
    height = (typeof options.height === "undefined") ? 400 : options.height;
    width = (typeof options.width === "undefined") ? 400 : options.width;
    log_scale = (typeof options.log_scale === "undefined") ? false : options.log_scale;
    x_label = (typeof options.x_label === "undefined") ? "Qx [1/\u00C5]" : options.x_label;
    y_label = (typeof options.y_label === "undefined") ? "Qy [1/\u00C5]" : options.y_label;
    title = (typeof options.title === "undefined") ? "what" : options.title;

    var margin = {top: 20, right: 20, bottom: 60, left: 60},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = d3.scale.linear().range([height, 0]);
    x.domain(d3.extent(qx, function(d) { return d; }));
    y.domain(d3.extent(qy, function(d) { return d; }));

    var xAxis = d3.svg.axis().scale(x).orient("bottom");
    var yAxis = d3.svg.axis().scale(y).orient("left");

    // Remove old plot
    d3.select("plot_anchor_2d").select("svg").remove();
    var svg = d3.select("plot_anchor_2d").append("svg")
      .attr("class", "Spectral")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");

    // Scale up the calculated pixel width so that we don't produce visual artifacts
    var pixel_h = 1.5*(y(qy[0])-y(qy[1]));
    var pixel_w = 1.5*(x(qx[1])-x(qx[0]));

    var n_colors = 64;
    var quantize;
    if (log_scale) {
      var bins = [];
      var step = Math.log(max_iq+1.0)/(n_colors-1);
      for (i=0; i<n_colors-1; i++) {
        bins.push(Math.exp(step*i)-1.0);
      }
      quantize = d3.scale.threshold()
      .domain(bins)
      .range(d3.range(n_colors).map(function(i) { return get_color(i, n_colors); }));
    } else {
        var quantize = d3.scale.quantize()
        .domain([0.,max_iq])
        .range(d3.range(n_colors).map(function(i) { return get_color(i, n_colors); }));
    };

    // Create X axis label   
    svg.append("text")
    .attr("x", width )
    .attr("y", height+margin.top+15)
    .attr("font-size", "12px")
    .style("text-anchor", "end")
    .text(x_label);

    // Create Y axis label
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0-margin.left)
    .attr("x", 0-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text(y_label);

    // Create title
    svg.append("text")
    .attr("transform", "rotate(-90)")
    .attr("y", 0-margin.left)
    .attr("x", 0-margin.top)
    .attr("dy", "1em")
    .style("text-anchor", "end")
    .text(title);

    svg.selectAll('g')
    .data(data)
    .enter()
    .append('g')
    .attr("transform", function(d,i) { var trans = y(qy[i])-pixel_h; return "translate(0,"+ trans + ")"; })
    .selectAll('rect')
    .data(function(d) { return d; })
    .enter()
    .append('rect')
    .attr('x', function(d,i) { return x( qx[i] ); })
    .attr('y', function(d,i) { return 0; })
    .attr('width', function(d,i) { return pixel_w; })
    .attr('height', function(d,i) { return pixel_h; })
    .style('fill', function(d) { return quantize(d); })
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "y axis").call(yAxis)

}
