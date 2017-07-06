// Functions for showing and exploring processing status


// Make a list from an array:
function objectAsList(arr) {
    'use strict';
    var list = '<ul>';

    for (var key in arr) {
        list += "<li>" + key + ": " + arr[key] + "</li>";
    }

    return list + "</ul>";
}


// Initialise the project overview, both plot and table:
function initProjectOverview(project) {
    'use strict';
    var uri;

    if (project === '') {
		project = "QSMRVDS";
    }

    $.getJSON(
        '/rest_api/v4/' + project,
        function(rawdata) {
			$("#overviewHeader").html(rawdata.Name + ': Status overview');
			// $("#overviewPrioScore").html("Priority: " + rawdata.PrioScore);
			$("#overviewDeadline").html("Deadline: " + rawdata.Deadline);
			$("#overviewETA").html("ETA: " + rawdata.ETA);
			$("#overviewTotalTime").html(
			    "Total time (s): " + rawdata.TotalProcessingTime.toFixed(0));
            var average = '<i>N/A</i>';
            var nr_done = rawdata.NrJobsFinished + rawdata.NrJobsFailed;
            if (nr_done !== 0) {
                average = (rawdata.TotalProcessingTime/nr_done).toFixed(0);
            }
            $("#overviewAverageTime").html(
			    "Average time per job (s): " + average);
            $("#overviewNrJobs").html(
			    "Nr jobs available/finished/failed: " + (rawdata.JobStates.Available || 0) + '/' + (rawdata.JobStates.Finished || 0) + '/' + (rawdata.JobStates.Failed || 0));
			if (rawdata.URLS["URL-Processing-image"]) {
                $("#overviewImage").html(
                    "Processing image: " +
                    "<a href='" + rawdata.URLS["URL-Processing-image"] +
                    "'>" + rawdata.URLS["URL-Processing-image"] + "</a>"
                );
            } else {
                $("#overviewImage").html("Processing image: <i>N/A</i>");
            }
            if (!jQuery.isEmptyObject(rawdata.Environment)) {
                $("#overviewEnv").html(
                    "Environment:" + objectAsList(rawdata.Environment));
            }

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
	    "Daily": 21600000, // 6 hours
	    "Hourly":  900000, // 15 minutes
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
        $.plot($('#overviewPlot'), [claimed, finished, failed], {
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
                "data": "Claimed",
                "title": "Duration",
                "render": function(data, type, full, meta) {
                    if (full.Finished !== null) {
                        return moment(full.Finished).diff(data, 'seconds') +
                            's';
                    } else if (full.Failed !== null) {
                        return moment(full.Failed).diff(data, 'seconds') +
                            's';
                    } else {
                        return '<i>N/A</i>';
                    }
                },
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "URLS",
                "title": "Results",
                "render": function ( data, type, full, meta ) {
                    if (data['URL-Result']) {
                        return '<a target="_blank" href="' +
                            data["URL-Result"] + '" ' +
                            'alt="' + data["URL-Output"] +
                            '">View result</a>';
                    }
                    else {
                        return '<a alt="' + data['URL-Output'] +
                            '"></a><i>N/A</i>';
                    }
                },
                "defaultContent": "<i>N/A</i>",
            },
        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
    });

    $('#jobTable tbody').on('click', 'tr td:nth-child(-n+9)', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(tr).children().last().find('a').attr("alt");
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');

        } else {
            $.getJSON(url)
                .done(function (data) {
                    row.child('<pre>' + data.Output + '</pre>').show();
                })
                .fail(function(data) {
                    row.child('<em> Request to "' + url + '" failed.</em>');
                })
                .always(function(data) {
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
