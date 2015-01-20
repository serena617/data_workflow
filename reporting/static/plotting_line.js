

// ********************************************** //
// ********* code for line plots **************** //
// ********************************************** //
function plot_1d(raw_data, anchor, options) {
    // For testing purposes, raw_data is fed in, 
    // anchor is the dialog box, and options
    // are empty {}.

    // options = {};
    //alert(options);
    color = '#0077cc';
    marker_size = 2;
    height = 350;
    width = 630;
    log_scale = options.log_scale;
    grid = true;
    x_label = "time elapsed [minutes]";
    y_label = "";
    title = "";
    // interp = (typeof options.interp ==="undefined") ? "none" : options.interp;
    //alert(options.log_scale);

    var data = [];
    for (var i=0; i<raw_data.length; i++) {
        // if (raw_data[i][1]>0 && raw_data[i][2]<raw_data[i][1]) {  data.push(raw_data[i]); };
	data.push(raw_data[i]);
    }
    
    var tid = $(".live_plots").parent().attr("id");
    //alert($("#" + tid).width());
    //alert($("#" + tid).height());
    //alert(anchor)
    //alert(tid);
    //alert($("#" + tid).width);
    //alert($("#" + tid).height);

    var margin = {top: 30, right: 15, bottom: 50, left: 65},
    width = width - margin.left - margin.right,
    height = height - margin.top - margin.bottom;

    var x = d3.scale.linear().range([0, width]);
    var y = log_scale ? d3.scale.log().range([height, 0]) : d3.scale.linear().range([height, 0]);
    var y_min = d3.min(data, function(d) { return d[1]; }) // for a better display of a constant function
    var y_max = d3.max(data, function(d) { return d[1]; })
    x.domain(d3.extent(data, function(d) { return d[0]; }));
    if ( y_min === y_max ){
	y.domain([y_min-1, y_max+1]);
	}
    else{
	y.domain([y_min, y_max]);
    }
    //alert(y_min + ", " + y_max);

    var xAxis = d3.svg.axis().scale(x).orient("bottom").ticks(8).tickFormat(d3.format("5.7g"));
    var xAxisMinor = d3.svg.axis().scale(x).orient("bottom").ticks(4).tickSize(3,3).tickSubdivide(4).tickFormat('');
    var yAxis = d3.svg.axis().scale(y).orient("left").ticks(4).tickFormat(d3.format("5.9g"));    
    var yAxisMinor = d3.svg.axis().scale(y).orient("left").ticks(4).tickSize(3,3).tickSubdivide(4).tickFormat('');
    
    // Remove old plot
    d3.select("#" + anchor).select("svg").remove();
    
    var svg = d3.select("#" + anchor).append("svg")
      .attr("class", "default_1d")
      .attr("width", width + margin.left + margin.right)
      .attr("height", height + margin.top + margin.bottom)
      .append("g")
      .attr("id", anchor + "_g")
      .attr("transform", "translate(" + margin.left + "," + margin.top + ")");
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxis);
    svg.append("g").attr("class", "x axis").attr("transform", "translate(0," + height + ")").call(xAxisMinor);
    svg.append("g").attr("class", "y axis").call(yAxis)
    svg.append("g").attr("class", "y axis").call(yAxisMinor)
    
    // Create X axis label   
    svg.append("text")
    .attr("x", width)
    .attr("y",  height+40)
    .attr("font-size", "11px")
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

    // Interpolate
    // if (interp !== 'none'){
// 	alert(interp);
	svg.select("path").remove();
	var interp_line = d3.svg.line()
	    .interpolate("step-after")
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


    // Tooltip obj
    var tooltip = d3.select("body")
	.append("text")
	.attr("class", "tooltip")
	.style("position", "absolute")
	.style("z-index", "2010")
	.style("visibility", "hidden")
	.style("color", "black");

    // Circle obj with colored outline
    var circle_ol = d3.select("#" + anchor + "_g")
		.append("circle")
		.attr("cx", "0")
		.attr("cy", "0")
		.attr("r", marker_size+5)
		.style("z-index", "2020")
		.style("visibility", "hidden")
		.style("fill", "white")
		.style("fill-opacity", "0")
		.style("stroke", color);

    // Points obj with data
    var points = svg.selectAll("circle")
	.data(data)
	.enter();

    // Little points
    var little_pt = points.append('circle')
	.attr("class", "datapt")
	.attr("cx", function(d) { return x(d[0]); })
	.attr("cy", function(d) { return y(d[1]); })
	.attr("r", marker_size)
	.style('fill', color);

    // This is used to get coordinates on mouseover
    var circle_ar = points.append("circle")
	.attr("class", anchor + "_focus")
	.attr("cx", function(d) { return x(d[0]); })
	.attr("cy", function(d) { return y(d[1]); })
	.attr("r", marker_size+5)
	.style("fill", "white")
	.style("fill-opacity", "0");

    // Get data values on hover event
    svg.selectAll("." + anchor + "_focus")
	.on("mouseover", function(d){ mouseover(d); })
	.on("mousemove", function(d){ mousemove(d); })
	.on("mouseout", function(d){ mouseout(d); });
    function mouseover(d){
	circle_ol.attr("cx", x(d[0]))
		.attr("cy", y(d[1]))
		.style("visibility", "visible");
	return tooltip.style("visibility", "visible");
    }
    function mousemove(d){
	tooltip.text(d[0] + ", " + d[1]); 
	return tooltip.style("top", (event.pageY-10)+"px").style("left",(event.pageX+10)+"px");
    }1
    function mouseout(d){
	circle_ol.style("visibility", "hidden");
	return tooltip.style("visibility", "hidden");
    }
}

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
