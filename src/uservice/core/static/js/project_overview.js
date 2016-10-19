// Fuctions for showing and exploring processing status


// Initialise the project overview, both plot and table:
function initProjectOverview(project) {
    var uri;

    if (project === '') {
		project = "QSMRVDS";
    }

    $.getJSON(
        '/rest_api/v4/' + project,
        function(rawdata) {
			$("#overviewHeader").html("Project: " + rawdata.Project);
			$("#overviewETA").html("ETA: " + rawdata.ETA);

			// Initialise overview plot and job table:
			uri = rawdata.URLS["URL-DailyCount"];
			updateProjectOverviewPlot(uri);
			initJobTable(rawdata.URLS["URL-Jobs"] + "?status=FAILED");
        }
    );

	// Setup hovering tooltip:
	$("<div id='tooltip'></div>").css({
		position: "absolute",
		display: "none",
		border: "1px solid #fdd",
		padding: "2px",
		"background-color": "#fee",
		opacity: 0.80,
	}).appendTo("body");

	// Setup hovering:
	$('#overviewPlot').bind("plothover", function (event, pos, item) {
		if (item) {
			var x = item.datapoint[0],
				y = item.datapoint[1];

        	$("#tooltip").html(item.series.periods[item.dataIndex] + ": " +
        	        y + " " + item.series.label)
				.css({top: item.pageY+5, left: item.pageX+5})
				.fadeIn(200);
		} else {
			$("#tooltip").hide();
		}
	});

	// Setup clicking:
	$('#overviewPlot').bind("plotclick", function (event, pos, item) {
		if ((item) && item.series.label != 'workers') {
		    // Update table:
			updateJobTable(item.series.URLS.own[item.dataIndex]);

            // Update plot:
		    if ($('#overviewPlot').hasClass("Daily")) {
		        var new_uri = item.series.URLS.zoom[item.dataIndex];
                $('#overviewPlot').toggleClass("Daily");
                updateProjectOverviewPlot(new_uri);
            }
        } else {
            // Update plot:
		    if ($('#overviewPlot').hasClass("Hourly")) {
                $('#overviewPlot').toggleClass("Hourly");
                updateProjectOverviewPlot(uri);
            }
        }
	});
}


// Update the plot showing the statisics for the project jobs:
function updateProjectOverviewPlot(uri) {
    var workers = [];
    var claimed = [];
    var failed = [];
    var finished = [];
    var xticks = [];
    var PeriodType = "";
	var URLS = {
		failed: [],
		claimed: [],
		finished: [],
		workers: [],
		zoom: [],
	};
	var barWidth = {
	    "Daily": 14400000,
	    "Hourly":  600000,
	};

    $.getJSON(uri, function(rawdata) {
        $.each(rawdata.Counts, function (ind, val) {
            workers.push([moment(val.Period), val.ActiveWorkers]);
            claimed.push([moment(val.Period), val.JobsClaimed]);
            failed.push([moment(val.Period), val.JobsFailed]);
            finished.push([moment(val.Period), val.JobsFinished]);
            URLS.workers.push(val.URLS["URL-ActiveWorkers"]);
            URLS.claimed.push(val.URLS["URL-JobsClaimed"]);
            URLS.failed.push(val.URLS["URL-JobsFailed"]);
            URLS.finished.push(val.URLS["URL-JobsFinished"]);
            URLS.zoom.push(val.URLS["URL-Zoom"]);
            xticks.push(val.Period);
        });
        PeriodType = rawdata.PeriodType;

        claimed = {
            data: claimed,
            color: '#2c5aa0',
            label: 'claimed',
            bars: {
                show: true,
                order: 1,
                barWidth: barWidth[PeriodType],
            },
            URLS: {own: URLS.claimed, zoom: URLS.zoom},
            periods: xticks,
        };
        finished = {
            data: finished,
            color: '#5aa02c',
            label: 'finished',
            bars: {
                show: true,
                order: 2,
                barWidth: barWidth[PeriodType],
            },
            URLS: {own: URLS.finished, zoom: URLS.zoom},
            periods: xticks,
        };
        failed = {
            data: failed,
            color: '#a02c5a',
            label: 'failed',
            bars: {
                show: true,
                order: 3,
                barWidth: barWidth[PeriodType],
            },
            URLS: {own: URLS.failed, zoom: URLS.zoom},
            periods: xticks,
        };
        workers = {
            data: workers,
            color: '#101010',
            label: 'workers',
            bars: {
                show: true,
                order: 4,
                barWidth: barWidth[PeriodType],
            },
            URLS: {own: URLS.workers, zoom: URLS.zoom},
            periods: xticks,
        };

        // (re)initialise overview plot:
        $.plot($('#overviewPlot'), [claimed, finished, failed, workers], {
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
        $('#overviewPlot').toggleClass(PeriodType);
    });
}


// Initialise the table showing the status of the jobs:
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
                "title": "Level2 data",
                "render": function ( data, type, full, meta ) {
                    return '<a href="' + getLevel2URI(data) + '" ' +
                           'alt="' + data["URL-Output"] + '">View output</a>';
                },
 				"defaultContent": "<i>N/A</i>",
            },
        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
    });

    $('#jobTable tbody').on('click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(this).children().eq(8).find('a').attr("alt");
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');

        } else {
            $.getJSON(url, function (data) {
                row.child(data.Output.replace(/\n/g, '<br>')).show();
                tr.addClass('shown');
            });
        }
    });
}


// Update the job info table:
function updateJobTable(url) {
    var table;
    table = $('#jobTable').DataTable();
    table.ajax.url(url).load();
}


// Clear the job info table:
function clearJobTable() {
    var table;
    table = $('#jobTable').DataTable();
    table.clear();
    table.draw();
}


// Guess the Level2 URI from the Level1 URI and metadata:
//  from:
//      http://odin.rss.chalmers.se/rest_api/v4/l1_log/21/1352690456/
//  and
//      http://malachite.rss.chalmers.se:8080/rest_api/v4/MESOVDS4/jobs/21:1352690456/output
//  to:
//      http://odin.rss.chalmers.se/rest_api/v4/level2/MESOVDS4/21/1352690456/
function getLevel2URI(data) {
    var project;
    var uri;

    data["URL-Output"].split('/').forEach(function(part, index, parts) {
        if (part == "rest_api") {
            project = parts[index + 2];
        }
    });

    uri = data["URL-Input"].replace(/l1_log/, 'level2/' + project);

    return uri;
}
