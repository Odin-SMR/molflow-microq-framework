// Fuctions for showing and exploring processing status

function initOverview(project) {
    var workers = [];
    var claimed = [];
    var failed = [];
    var finished = [];
    var xticks = [];
    var data = [];
	var URLS = {
		failed: [],
		claimed: [],
		finished: [],
		workers: [],
	};

    if (project === '') {
		project = "QSMRVDS";
    }

    $.getJSON(
        '/rest_api/v4/' + project + '?period=hourly',
        function(rawdata) {
            $.each( rawdata.Status.HourlyCount, function (ind, val) {
                workers.push([moment(val.Period), val.ActiveWorkers]);
                claimed.push([moment(val.Period), val.JobsClaimed]);
                failed.push([moment(val.Period), val.JobsFailed]);
                finished.push([moment(val.Period), val.JobsFinished]);
				URLS.workers.push(val.URLS["URL-ActiveWorkers"]);
				URLS.claimed.push(val.URLS["URL-JobsClaimed"]);
				URLS.failed.push(val.URLS["URL-JobsFailed"]);
				URLS.finished.push(val.URLS["URL-JobsFinished"]);
                xticks.push(val.Period);
            });

			$("#overviewHeader").html("Project: " + rawdata.Project);
			$("#overviewETA").html("ETA: " + rawdata.Status.ETA);

			workers = {
				data: workers,
				color: '#101010',
				label: 'workers',
				bars: {
					show: true,
					order: 4,
					barWidth: 600000,
				},
			};
			claimed = {
				data: claimed,
				color: '#2c5aa0',
				label: 'claimed',
				bars: {
					show: true,
					order: 1,
					barWidth: 600000,
				},
			};
			failed = {
				data: failed,
				color: '#a02c5a',
				label: 'failed',
				bars: {
					show: true,
					order: 3,
					barWidth: 600000,
				},
			};
			finished = {
				data: finished,
				color: '#5aa02c',
				label: 'finished',
				bars: {
					show: true,
					order: 2,
					barWidth: 600000,
				},
			};

			data.push(claimed);
			data.push(finished);
			data.push(failed);
			data.push(workers);

			// Initialise overview plot:
            $.plot($('#overviewPlot'), data, {
				xaxis: {
					mode: "time",
				},
        	    grid: {
            	    hoverable: true,
                	clickable: true,
    	        },
				legend: {
					show: true,
				},
        	});

			// Initialise jobtable:
			initJobTable(URLS.claimed[0]);
        }
    );

	// Setup hovering tooltip:
	$("<div id='tooltip'></div>").css({
		position: "absolute",
		display: "none",
		border: "1px solid #fdd",
		padding: "2px",
		"background-color": "#fee",
		opacity: 0.80
	}).appendTo("body");

	// Setup hovering:
	$('#overviewPlot').bind("plothover", function (event, pos, item) {
		if (item) {
			var x = item.datapoint[0],
				y = item.datapoint[1];

        	$("#tooltip").html(xticks[item.dataIndex] + ": " + y + " " + item.series.label)
				.css({top: item.pageY+5, left: item.pageX+5})
				.fadeIn(200);
		} else {
			$("#tooltip").hide();
		}
	});

	// Setup clicking:
	$('#overviewPlot').bind("plotclick", function (event, pos, item) {
		if ((item) && item.series.label != 'workers') {
			updateJobTable(URLS[item.series.label][item.dataIndex]);
		}
	});
}


function initJobTable(url) {
    var table = $('#jobTable').DataTable({
        "ajax":{
            "url": url,
            "dataSrc": "Jobs",
        },
        "columns": [
            {
                "data": "Id",
                "title": "Job ID",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Type",
                "title": "Type",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Worker",
                "title": "Worker",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Status",
                "title": "Status",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Added",
                "title": "Added",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Claimed",
                "title": "Claimed",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Finished",
                "title": "Finished",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Failed",
                "title": "Failed",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "URLS",
                "title": "Console output",
                "render": function ( data, type, full, meta ) {
                  return '<a href="' + data["URL-Output"] + '">View output</a>';
                },
 				"defaultContent": "<i>N/A</i>",
            },
        ],
        "paging":   false,
        "ordering": false,
        "info":     false,
    });
}

function updateJobTable(url) {
    var table;
    table = $('#jobTable').DataTable();
    table.ajax.url(url).load();
}

function clearJobTable() {
    var table;
    table = $('#jobTable').DataTable();
    table.clear();
    table.draw();
}

