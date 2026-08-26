const palette = {
    navy: '#0b1f3a',
    blue: '#1d65d6',
    red: '#dc3545',
    orange: '#f59f00',
    teal: '#0f9d8a',
    slate: '#64748b',
    purple: '#7856d8'
};

const chartInstances = {};
const mapInstances = {};

const DASHBOARD_REFRESH_MS = 10000;


function chartBase(type, elementId, labels, datasets, options = {}) {
    const element = document.getElementById(elementId);

    if (!element) {
        return null;
    }

    // Destroy previous chart instance before creating a new one.
    if (chartInstances[elementId]) {
        chartInstances[elementId].destroy();
        delete chartInstances[elementId];
    }

    chartInstances[elementId] = new Chart(element, {
        type,
        data: {
            labels,
            datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,

            plugins: {
                legend: {
                    position: 'bottom',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8
                    }
                }
            },

            scales: type === 'doughnut'
                ? {}
                : {
                    y: {
                        beginAtZero: true,
                        grid: {
                            color: '#edf0f4'
                        }
                    },
                    x: {
                        grid: {
                            display: false
                        }
                    }
                },

            ...options
        }
    });

    return chartInstances[elementId];
}


function barDataset(label, values, color) {
    return {
        label,
        data: values,
        backgroundColor: color,
        borderRadius: 6,
        maxBarThickness: 36
    };
}


async function fetchSummary() {
    const response = await fetch('/analytics/api/summary', {
        cache: 'no-store'
    });

    if (!response.ok) {
        throw new Error('Analytics endpoint unavailable');
    }

    return response.json();
}


async function fetchMapData() {
    const response = await fetch('/disasters/api/map-data', {
        cache: 'no-store'
    });

    if (!response.ok) {
        throw new Error('Map endpoint unavailable');
    }

    return response.json();
}


function renderDashboardCharts(summary) {
    chartBase(
        'bar',
        'incidentTypeChart',
        summary.incident_types.labels,
        [
            barDataset(
                'Incidents',
                summary.incident_types.values,
                palette.blue
            )
        ]
    );

    chartBase(
        'doughnut',
        'severityChart',
        summary.incidents_by_severity.labels,
        [
            {
                label: 'Incidents',
                data: summary.incidents_by_severity.values,
                backgroundColor: [
                    palette.teal,
                    palette.orange,
                    palette.red,
                    '#7f1d1d'
                ],
                borderWidth: 0
            }
        ]
    );
}


function renderAnalyticsCharts(summary) {
    const avgResponseHours =
        document.getElementById('avgResponseHours');

    const unresolvedIncidents =
        document.getElementById('unresolvedIncidents');

    if (avgResponseHours) {
        avgResponseHours.textContent =
            `${summary.average_response_hours} h`;
    }

    if (unresolvedIncidents) {
        unresolvedIncidents.textContent =
            summary.unresolved_incidents;
    }

    chartBase(
        'line',
        'monthChart',
        summary.incidents_by_month.labels,
        [
            {
                label: 'Incidents',
                data: summary.incidents_by_month.values,
                borderColor: palette.blue,
                backgroundColor: 'rgba(29,101,214,.12)',
                fill: true,
                tension: 0.35
            }
        ]
    );

    chartBase(
        'line',
        'populationChart',
        summary.affected_population_trend.labels,
        [
            {
                label: 'People affected',
                data: summary.affected_population_trend.values,
                borderColor: palette.red,
                backgroundColor: 'rgba(220,53,69,.10)',
                fill: true,
                tension: 0.35
            }
        ]
    );

    chartBase(
        'doughnut',
        'responseStatusChart',
        summary.response_status.labels,
        [
            {
                label: 'Responses',
                data: summary.response_status.values,
                backgroundColor: [
                    palette.blue,
                    palette.orange,
                    palette.teal
                ],
                borderWidth: 0
            }
        ]
    );

    chartBase(
        'bar',
        'resourceUtilizationChart',
        summary.resource_utilization.labels,
        [
            barDataset(
                'Utilized %',
                summary.resource_utilization.values,
                palette.purple
            )
        ],
        {
            scales: {
                y: {
                    beginAtZero: true,
                    max: 100
                }
            }
        }
    );

    chartBase(
        'bar',
        'resourceAvailabilityChart',
        summary.resource_availability.labels,
        [
            barDataset(
                'Available',
                summary.resource_availability.available,
                palette.teal
            ),
            barDataset(
                'Total',
                summary.resource_availability.total,
                '#dbe3ef'
            )
        ]
    );
}


function markerColor(severity) {
    return {
        Critical: '#7f1d1d',
        High: '#dc3545',
        Medium: '#f59f00',
        Low: '#0f9d8a'
    }[severity] || '#1d65d6';
}


function escapeHtml(value) {
    return String(value).replace(
        /[&<>'"]/g,
        character => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            "'": '&#39;',
            '"': '&quot;'
        }[character])
    );
}


function createMarker(item) {
    const color = markerColor(item.severity);

    const icon = L.divIcon({
        className: 'custom-marker',
        html: `<span style="background:${color}"></span>`,
        iconSize: [22, 22],
        iconAnchor: [11, 11]
    });

    const marker = L.marker(
        [item.latitude, item.longitude],
        { icon }
    );

    marker.bindPopup(`
        <strong>${escapeHtml(item.title)}</strong>
        <br>
        ${escapeHtml(item.type)} · ${escapeHtml(item.severity)}
        <br>
        Population:
        ${Number(item.affected_population || 0).toLocaleString()}
        <br>
        Status:
        ${escapeHtml(item.status)}
        <br>
        Priority:
        ${Number(item.priority_score || 0).toFixed(2)}
        (${escapeHtml(item.priority_category)})
    `);

    return marker;
}


async function createMap(elementId, markerData) {
    const mapElement = document.getElementById(elementId);

    if (!mapElement || typeof L === 'undefined') {
        return null;
    }

    let map = mapInstances[elementId];

    // Create map once.
    if (!map) {
        map = L.map(elementId).setView(
            [20.5937, 78.9629],
            4.5
        );

        L.tileLayer(
            'https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png',
            {
                maxZoom: 19,
                attribution: '&copy; OpenStreetMap contributors'
            }
        ).addTo(map);

        map._incidentLayer = L.layerGroup().addTo(map);

        mapInstances[elementId] = map;
    }

    // Remove previous markers.
    map._incidentLayer.clearLayers();

    const bounds = [];

    markerData.forEach(item => {
        const marker = createMarker(item);

        marker.addTo(map._incidentLayer);

        bounds.push([
            item.latitude,
            item.longitude
        ]);
    });

    if (bounds.length) {
        map.fitBounds(
            bounds,
            {
                padding: [30, 30],
                maxZoom: 7
            }
        );
    }

    return map;
}


function updateLastUpdated() {
    const element =
        document.getElementById('dashboardLastUpdated');

    if (!element) {
        return;
    }

    element.textContent =
        `Last updated: ${new Date().toLocaleTimeString()}`;
}


async function refreshDashboard() {
    try {
        const [summary, mapData] = await Promise.all([
            fetchSummary(),
            fetchMapData()
        ]);

        renderDashboardCharts(summary);

        await createMap(
            'dashboardMap',
            mapData
        );

        updateLastUpdated();

        console.log(
            'Dashboard refreshed:',
            new Date().toLocaleTimeString()
        );

    } catch (error) {
        console.error(
            'Dashboard refresh failed:',
            error
        );
    }
}


window.initDashboard = async function () {
    await refreshDashboard();

    // Prevent duplicate timers if initDashboard is called again.
    if (window.dashboardRefreshTimer) {
        clearInterval(
            window.dashboardRefreshTimer
        );
    }

    window.dashboardRefreshTimer =
        setInterval(
            refreshDashboard,
            DASHBOARD_REFRESH_MS
        );
};


window.initAnalytics = async function () {
    try {
        const summary = await fetchSummary();

        renderAnalyticsCharts(summary);

    } catch (error) {
        console.error(
            'Analytics loading failed:',
            error
        );
    }
};


window.initDetailMap = async function (
    latitude,
    longitude,
    title,
    severity
) {
    await createMap(
        'detailMap',
        [
            {
                latitude,
                longitude,
                title,
                type: 'Incident',
                severity,
                affected_population: 0,
                status: 'Current',
                priority_score: 0,
                priority_category: '—'
            }
        ]
    );
};