var config = {
    responsive: true,
    displaylogo: false,
}

$(document).ready(function() {

    threat_per_stride_chart = document.getElementById('threat_per_stride_chart');
    plot_chart(threat_per_stride_chart, threat_per_stride, 'Threats per STRIDE category', 'STRIDE Category', 'Number of threats');
});

function plot_chart(chart_id, input_data, chart_title, x_title, y_title) {
    var data = [{
        type: 'bar',
        x: input_data.map(item => item[0]),
        y: input_data.map(item => item[1]),
        marker: {
            color: 'rgba(55,128,191,0.7)',
            line: {
                width: 2.5,
                color: 'rgba(55,128,191,1.0)'
            }
        }
    }];

    var layout = {
        title: {
            text: chart_title,
        },
        template: 'plotly_dark',
        font: { size: 15 },
        paper_bgcolor: 'transparent',
        plot_bgcolor: 'transparent',
        xaxis: {
            title: { text: x_title },
        },
        yaxis: {
            title: { text: y_title },
        }
    };
    Plotly.newPlot(chart_id, data, layout, config);
}