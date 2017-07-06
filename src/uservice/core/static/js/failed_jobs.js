// Functions for showing and exploring failed jobs

FAILED_DATA = {};
ROWNR2JOBIDS = {};
ROWNR2LINE = {};
ROWNR2LINES = {};

function initFailedJobs(project) {
    var table = $('#linesTable').DataTable({
        "ajax":{
            "url": "/rest_api/v4/" + project + '/failures',
            "dataSrc": function(json) {
                FAILED_DATA = json;
                return json.Lines;
            },
        },
        "columns": [
            {
                "data": "Score",
                "title": "Score",
                "render": function ( data, type, full, meta ) {
                    return Number(data.toFixed(3));
                },
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Line",
                "title": "Output lines",
                "render": function ( data, type, full, meta ) {
                    return data + ' (' + full.CommonLines.length + ')';
                },
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Jobs",
                "title": "Nr jobs",
                "render": function ( data, type, full, meta ) {
                    return data.length;
                },
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Jobs",
                "title": "",
                "render": function ( data, type, full, meta ) {
                    ROWNR2JOBIDS[meta.row] = data;
                    ROWNR2LINE[meta.row] = full.Line;
                    ROWNR2LINES[meta.row] = full.CommonLines;
                    return '<a href="#" onclick="javascript:updateFailedJobsTable(' + meta.row + '); return false;">Show&nbsp;jobs</a>';
                },
                "defaultContent": "<i>N/A</i>",
            },
        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
    });
    table.order([0, 'desc']).draw();

    $('#linesTable tbody').on('click', 'tr td:nth-child(-n+3)', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var lines = ROWNR2LINES[row.index()];
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');

        } else {
            var txt = '';
            var line;
            for (var i=0; i < lines.length; i++) {
                line = lines[i];
                txt += Number(line.Score.toFixed(3)) + '\t' + line.Line + '\n';
            }
            row.child('<pre>' + txt + '</pre>').show();
            tr.addClass('shown');
        }
    });

}

function updateFailedJobsTable(rownr) {
    $('#jobTableHeader').text('Failed jobs');
    $('#jobTableInfo').html('Jobs with console output line: <i>' +
                            ROWNR2LINE[rownr] + '</i>');
    var jobids = ROWNR2JOBIDS[rownr];
    var jobs = [];
    for (var i=0; i < jobids.length; i++)
        jobs.push(FAILED_DATA.Jobs[jobids[i]]);
    var table = $('#jobTable').DataTable({
        "data": jobs,
        "columns": [
            {
                "data": "Id",
                "title": "Job ID",
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "ProcessingTime",
                "title": "Processing time (s)",
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Worker",
                "title": "Worker",
                "defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Failed",
                "title": "Failed",
                "defaultContent": "<i>N/A</i>",
            },

        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
        "destroy": true,
    });

    $('#jobTable tbody').on('click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var jobid = $(this).children().eq(0).text();
        var url = '/rest_api/v4/' + FAILED_DATA.Project + '/jobs/' +
            jobid + '/output';
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');

        } else {
            $.getJSON(url, function (data) {
                row.child('<pre>' + data.Output + '</pre>').show();
                tr.addClass('shown');
            });
        }
    });
}
