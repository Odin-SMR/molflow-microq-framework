// Functions for rendering and navigating server status


// Initialise the server status:
function initServerStatus() {
    var table = $('#projectsTable').DataTable({
        "ajax":{
            "url": "/rest_api/v4/projects",
            "dataSrc": "Projects",
        },
        "columns": [
            {
                "data": "Name",
                "title": "Project",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "CreatedBy",
                "title": "Created by",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "CreatedAt",
                "title": "Started",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "Deadline",
                "title": "Deadline",
 				"defaultContent": "<i>N/A</i>",
            },
            /*
            {
                "data": "URLS",
                "title": "ETA",
                "render": function ( data, type, full, meta ) {
                    $.getJSON(data["URL-Status"], function (rawdata) {
                        return rawdata.ETA;
                    });
                },
 				"defaultContent": "<i>N/A</i>",
            },
            */
            {
                "data": "LastJobAddedAt",
                "title": "Last added",
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "LastJobClaimedAt",
                "title": "Last claimed",
 				"defaultContent": "<i>N/A</i>",
            },
            /*
            {
                "data": "URLS",
                "title": "Finished",
                "render": function ( data, type, full, meta ) {
                    $.getJSON(data["URL-Status"], function (rawdata) {
                        return rawdata.JobStates.Finished;
                    });
                },
 				"defaultContent": "<i>N/A</i>",
            },
            {
                "data": "URLS",
                "title": "Failed",
                "render": function ( data, type, full, meta ) {
                    $.getJSON(data["URL-Status"], function (rawdata) {
                        return rawdata.JobStates.Failed;
                    });
                },
 				"defaultContent": "<i>N/A</i>",
            },
            */
            {
                "data": "Name",
                "title": "Project details",
                "render": function ( data, type, full, meta ) {
                    return '<a href="/' + data + '">More...</a>';
                },
 				"defaultContent": "<i>N/A</i>",
            },
        ],
        "paging":   true,
        "ordering": true,
        "info":     false,
    });

    /*
    $('#projectsTable tbody').on('click', 'tr', function () {
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
    */
}

// Update the projects info table:
function updateProjectsTable(url) {
    var table;
    table = $('#projectsTable').DataTable();
    table.ajax.url(url).load();
}


// Clear the projects info table:
function clearProjectsTable() {
    var table;
    table = $('#projectsTable').DataTable();
    table.clear();
    table.draw();
}
