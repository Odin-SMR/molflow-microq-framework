// Functions for updating overview table and plots:

function initLevel1(date) {
    $('#level1-date').html(date);

    var table = $('#level1-date-table').DataTable({
        "ajax": {
            "url": '/rest_api/v4/freqmode_info/' + date + '/',
            "dataSrc": "Info",
            },
        "columns": [
            {
                "data": "Backend",
                "title": "Backend",
            },
            {
                "data": "FreqMode",
                "title": "FreqMode",
            },
            {
                "data": "NumScan",
                "title": "NumScan",
            },
            {
                "data": "URL",
                "title": "URL",
                "render": function ( data, type, full, meta ) {
                  return '<a href="'+data+'">Get JSON data</a>';
                },
            },
            ],
        "paging":   false,
        "ordering": false,
        "info":     false,
        })

    $('#level1-date-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var date = $('#level1-date').text();
        var backend = tr.children().eq(0).text();
        var freqmode = tr.children().eq(1).text();
        if (row.child.isShown()) {
            row.child.hide();
            tr.removeClass('shown');
        }else {
            row.child( addInfo( row.data(), backend, freqmode )).show();
            tr.addClass('shown');
        }
        // The plot rows don't have the necessary attributes, so don't try to
        // update when those are clicked:
        if ((backend == "AC1") || (backend == "AC2")) {
            clearDataTable();
            updateDataTable(date, backend, freqmode);
            updatePlot(date, backend, freqmode);
        } else if (!tr.hasClass("foldablePlot")) {
            backend = tr.prev().children().eq(0).text();
            freqmode = tr.prev().children().eq(1).text();
            clearDataTable();
            updateDataTable(date, backend, freqmode);
            updatePlot(date, backend, freqmode);
        }
    });
}

function updateLevel1(date) {
    var table;
    table = $('#level1-date-table').DataTable();
    table.ajax.url('/rest_api/v4/freqmode_info/' + date + '/').load();
    $('#level1-date').html(date);
}

function clearLevel1Table() {
    var table;
    table = $('#level1-date-table').DataTable();
    table.clear();
    table.draw();
}

function addInfo (data, backend, freqmode) {
    return '<table width="100%">' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Latitudes of first spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-lat-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Longitudes of first spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-lon-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Solar zenith angles (ZD) of scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-sun-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4">Number of spectra in scans:</td>' +
        '</tr>' +
        '<tr class="foldablePlot">' +
            '<td colspan="4" id="smart-plot-scan-' + backend + '-' + freqmode +
                '" class="plotter"></td>' +
        '</tr>' +
        '</table>';
}

function updatePlot(date, back, freq) {
        var sun = []
        var lat = []
        var lon = []
        var scan = []
        var opt = {}
        var currDate = moment(date, 'YYYY-MM-DD')
        $.getJSON(
            '/rest_api/v4/freqmode_info/' + date + '/' + back + '/' + freq + '/',
            function(data) {
                xticks =[]
                $.each( data["Info"], function (index, data) {
                    time_point = moment
                    datestring = data["DateTime"]
                    var momentDate = moment(datestring);
                    sun.push( [momentDate.toDate(), data["SunZD"]] );
                    lat.push( [momentDate.toDate(), data["LatStart"]] );
                    lon.push( [momentDate.toDate(), data["LonStart"]] );
                    scan.push([momentDate.toDate(), data["NumSpec"]] );
                })
                opt={
                    "series":{
                        "color": "#2C5AA0",
                        "points":{
                            "show":true,
                        }
                    },
                    "xaxis":{
                        "mode": "time",
                        "minTickSize": [1, "hour"],
                        "min": currDate.startOf("day").toDate().getTime(),
                        "max": currDate.endOf("day").toDate().getTime()
                    },
                    "grid": {
                        "hoverable": true,
                    },
                }
                $.plot("#smart-plot-lat-"+back+'-'+freq, [lat], opt);//{series:{points: {show:true}}})
                $.plot("#smart-plot-lon-"+back+'-'+freq, [lon], opt);//{series:{points: {show:true}}})
                $.plot("#smart-plot-sun-" +back+'-'+freq, [sun], opt);
                $.plot("#smart-plot-scan-" +back+'-'+freq, [scan], opt);
            })
        }


// Functions for updating scan info table and plots:

function initDataTable(date, back, freq) {
    var table = $('#info-table').DataTable( {
        "ajax": {
            "dataSrc": "Info",
            "url": '/rest_api/v4/freqmode_info/' + date + '/' + back + '/' +
                freq + '/',
            },
        "data": [],
        "columns": [
                {
                    "data": "DateTime",
                    "title": "DateTime",
                },
                {
                    "data": "AltStart",
                    "title": "AltStart",
                },
                {
                    "data": "AltEnd",
                    "title": "AltEnd",
                },
                {
                    "data":"FreqMode",
                    "title": "FreqMode",
                },
                {
                    "data": "SunZD",
                    "title": "SunZD",
                    "render": function ( data, type, full, meta ) {
                        return parseFloat(data).toFixed(2);
                    }
                },
                {
                    "data": "URL",
                    "title": "Data URL (JSON)",
                    "render": function ( data, type, full, meta ) {
                        return '<a href="' + data.replace("v3", "v4") +
                               '">Get JSON data</a>';
                    },
                },
         ],
    });

    $('#info-table tbody').on( 'click', 'tr', function () {
        var tr = $(this).closest('tr');
        var row = table.row(tr);
        var url = $(this).children().eq(5).find('a').attr("href").replace("v4", "v4");
        var url_array = url.split('/');
        var id = url_array[url_array.length - 1];
        if (row.child.isShown()) {
            row.child.hide()
            tr.removeClass('shown')
        }else {
            row.child(addOverview(url, id)).show()
            tr.addClass('shown')
        }

        updateOverview(url, id);
    });
}

function updateOverview(url, id) {
    $('#info-image-' + id).attr('src', url.replace("rest_api/v4/scan", "browse"));
}

function addOverview(url, id) {
    return '<img id="info-image-' + id + '" class="img-responsive"' +
           ' src="{{ url_for("static", filename="images/empty.png") }}"/>'
}

function updateDataTable(date, back, freq) {
    var table;
    table = $('#info-table').DataTable();
    table.ajax.url('/rest_api/v3/freqmode_info/' + date + '/' + back + '/' +
            freq + '/').load();
}

function clearDataTable() {
    var table;
    table = $('#info-table').DataTable();
    table.clear();
    table.draw();
}


// Functions used to populate calendar view:

freqmodeColours = {
  // Websafe colours:
  '0':  '#101010', //'Black',
  '1':  '#E6E6FA', // 'Lavender',
  '2':  '#4169E1', // 'RoyalBlue',
  '8':  '#800080', // 'Purple',
  '13': '#B22222', // 'FireBrick',
  '14': '#228B22', // 'ForestGreen',
  '17': '#8B4513', // 'SaddleBrown',
  '19': '#C0C0C0', // 'Silver',
  '21': '#87CDFA', // 'LightSkyBlue',
  '22': '#000080', // 'Navy',
  '23': '#663399', // 'RebeccaPurple',
  '24': '#008080', // 'Teal',
  '25': '#FFD700', // 'Gold',
  '29': '#4682B4', // 'SteelBlue',
}

freqmodeTextColours = {
  '0': 'White',
  '1': 'Black',
  '2': 'White',
  '8': 'White',
  '13': 'White',
  '14': 'White',
  '17': 'White',
  '19': 'Black',
  '21': 'Black',
  '22': 'White',
  '23': 'White',
  '24': 'White',
  '24': 'Black',
  '29': 'Black',
}

function updateCalendar(start, end) {
    var theDate = start;
    // For ech day, get json from rest:
    if ($('#calendar').fullCalendar('clientEvents',
                theDate.format()).length == 0) {
        $.ajax({
            type: 'GET',
            url: '/rest_api/v4/period_info/' +
                start.format('YYYY/MM/DD/') ,
            dataType: "json",
            success: function(data) {
                var events = [];
                // Loop over the elements under Info and create event:
                $.each(data.Info, function(index, theInfo) {
                    theEvent = {
                        title: "FM: " + theInfo.FreqMode + " (" +
                            theInfo.Backend +  "): " +
                            theInfo.NumScan + " scans",
                        start: theInfo.Date,
                        id: theInfo.Date,
                        // This should link to the report for the day:
                        // url: theInfo.URL,
                        url: "#level1-date",
                        // Add color and textColor based on freqmode:
                        color: freqmodeColours[theInfo.FreqMode],
                        textColor: freqmodeTextColours[theInfo.FreqMode],
                        // Save some metadata:
                        FreqMode: theInfo.FreqMode,
                        Backend: theInfo.Backend,
                    };
                    events.push(theEvent);
                    // Push event to calendar:
                });
                $('#calendar').fullCalendar('removeEvents');
                $('#calendar').fullCalendar('addEventSource', events);
            }
        });
    };
}


// Functions for generating statistics plots:

monthNames = {
    1: "January",
    2: "February",
    3: "March",
    4: "April",
    5: "May",
    6: "June",
    7: "July",
    8: "August",
    9: "September",
    10: "October",
    11: "November",
    12: "December",
    12: "Undecimber"
}

function labelFormatter(label, series) {
    var shortLabel = series["shortLabel"];
    return "<div style='font-size:7pt; text-align:center; padding:2px; " +
           "color:white;'>" + shortLabel + "<br/>" + Math.round(series.percent) +
           "%</div>";
}

function drawStatistics(year) {
    var data;
    var sum;
    var plotMode;
    var temp = '';

    if (year == '') {
        plotMode = "Total";
    } else {
        plotMode = "Year";
    }

    // Generate freqmode statistics plot:
    data = [];
    sum = 0;
    $.getJSON('/rest_api/v4/statistics/freqmode/?year=' + year,
            function(rawdata) {
        $.each( rawdata["Data"], function (ind, val) {
            data[ind] = {
                color: freqmodeColours[val["freqmode"]],
                data: val["sum"],
                label: "FM " + val["freqmode"] + " (" + val["sum"] + ")",
                shortLabel: "FM " + val["freqmode"],
                longLabel: "Frequency mode " + val["freqmode"] + ": " +
                    val["sum"] + " scans",
            }
            sum += val["sum"];
        });

        $.plot($('#fmStats' + plotMode), data, {
            series: {
                pie: {
                    show: true,
                    radius: 1,
                    innerRadius: 0.382,
                    label: {
                        formatter: labelFormatter,
                        show: true,
                        threshold: 0.05,
                        radius: 0.764,
                        background: {
                            opacity: 0.236,
                            color: '#101010'
                        },
                    },
                },
            },
            grid: {
                hoverable: true,
            },
            legend: {
                show: false,
            },
        });

        if (plotMode == "Total") {
            temp = "";
            $('#totalNumberLabel').html("The data base contains a total of " +
                    sum + " scans");
        } else {
            temp = " for " + year;
        }

        $('#fmStats' + plotMode + 'Label').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans by frequency mode" + temp + ":" +
                "</span>");

        $('#fmStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp + ": " + sum + "</span>");
    });

    $('#fmStats' + plotMode).bind("plothover", function(event, pos, obj) {
        if (plotMode == "Total") {
            temp = "";
        } else {
            temp = " for " + year;
        }

        if (!obj) {
            $('#fmStats' + plotMode + 'Hover').html(
                    "<span style='font-weight:bold;'>" +
                    "Total number of scans" + temp + ": " + sum + "</span>");
            return;
        }

        var percent = parseFloat(obj.series.percent).toFixed(2);
        $('#fmStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                obj.series.longLabel + temp + " (" + percent + "%)</span>");
    });

    // Generate yearly statistics plot:
    data = [];
    xticks = [];
    $.getJSON('/rest_api/v4/statistics/freqmode/timeline/?year=' + year,
            function(rawdata) {
        $.each( rawdata["Data"], function (key, val) {
            data.push({
                data: val,
                color: freqmodeColours[key],
                shortLabel: "FM " + key,
                label: "FM " + key,
                longLabel: "Frequency mode " + key,
            });
        });

        if (plotMode == "Total") {
            xticks = rawdata["Years"];
        } else {
            xticks = rawdata["Months"];
        }

        $.plot($('#timelineStats' + plotMode), data, {
            series: {
                stack: true,
                lines: {
                    show: false,
                    fill: true,
                    steps: false,
                },
                bars: {
                    show: true,
                    barWidth: 0.618,
                    fill: 0.764,
                    color: '#101010',
                },
            },
            legend: {
                show: false,
            },
            xaxis: {
                ticks: xticks,
            },
            grid: {
                hoverable: true,
                clickable: true,
            },
        });

        if (plotMode == "Total") {
            temp = "year";
        } else {
            temp = "month for " + year;
        }

        $('#timelineStats' + plotMode + 'Label').html(
                "<span style='font-weight:bold;'>" +
                "Number of scans and frequency " +
                "mode distribution per " + temp +":" +
                "</span>");

        if (plotMode == "Total") {
            temp = "";
        } else {
            temp = " for " + year;
        }

        $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp + ": " + sum + "</span>");
    });

    $('#timelineStats' + plotMode + '').bind("plothover",
            function(event, pos, obj) {

        if (!obj) {
            if (plotMode == "Total") {
                temp = "";
            } else {
                temp = "for " + year;
            }

            $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                "Total number of scans" + temp +": " + sum + "</span>");
            return;
        }

        var scans = obj["datapoint"][1] - obj["datapoint"][2];

        if (plotMode == "Total") {
            temp = obj["datapoint"][0];
        } else {
            temp = monthNames[obj["datapoint"][0]];
        }

        $('#timelineStats' + plotMode + 'Hover').html(
                "<span style='font-weight:bold;'>" +
                obj.series.longLabel + ", " + temp + ": " +
                + scans + " scans</span>");
    });

    if (plotMode == "Total") {
        $('#timelineStats' + plotMode + '').bind("plotclick",
                function(event, pos, obj) {
            var year;

            if (!obj) {
                return;
            }

            year = obj["datapoint"][0];

            drawStatistics(year);
        });
    }
}

freqmodeInfo = {
    1: ["501.180 - 501.580, 501.980 - 502.380", "ClO, O3, N2O"],
    2: ["544.100 - 544.902", "HNO3, O3"],
    8: ["488.950 - 489.350, 488.35 - 488.750", "H2(18)O, O3, H2O"],
    13: ["556.598 - 557.398", "H2(16)O, O3"],
    14:
    ["576.062 - 576.862", "CO, O3"],
    17: ["489.950 - 490.750", "HDO, (18)O3"],
    19: ["556.550 - 557.350", "H2O, O3"],
    21: ["551.152 - 551.552, 551.752 - 552.152", "NO, O3, H2(17)O"],
    22: ["576.254 - 576.654, 577.069 - 577.469", "CO, O3, HO2, (18)O3"],
    23: ["488.350 - 488.750, 556.702 - 557.102", "H2(16)0, O3"],
    24: ["576.062 - 576.862", "CO, O3"],
    25: ["502.998 - 504.198", "H2(16)O, O3"],
}

function renderFreqmodeInfoTable () {
    theTable = "<table class='table'><tr><td></td><td><b>Frequency mode</b></td>" +
        "<td><b>Frequency range [GHz]</b></td><td><b>Species</b></td></tr>"
    $.each( freqmodeInfo, function(key, val) {
        theTable += "<tr>" +
            "<td bgcolor='" + freqmodeColours[key] + "'> </td>" +
            "<td>" + key + "</td>" +
            "<td>" + val[0] + "</td>" +
            "<td>" + val[1] + "</td>" +
            "</tr>";
    });

    theTable += "</table>";

    $('#freqmodeInfoTable').html(theTable);
}
