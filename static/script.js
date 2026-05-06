// Initialize Lucide Icons
lucide.createIcons();

// DOM Elements
const kpiTime = document.getElementById('kpi-time');
const kpiCompute = document.getElementById('kpi-compute');
const kpiOpt = document.getElementById('kpi-opt');
const historyTbody = document.getElementById('history-tbody');

// Initialize Chart.js with dark mode defaults
Chart.defaults.color = '#94a3b8';
Chart.defaults.font.family = "'Inter', sans-serif";

let optimizationChart;

async function fetchMetrics() {
    try {
        const response = await fetch('/api/metrics');
        const data = await response.json();
        
        updateKPIs(data.kpis);
        renderChart(data.history);
        renderTable(data.history);
    } catch (error) {
        console.error("Error fetching metrics:", error);
    }
}

function updateKPIs(kpis) {
    kpiTime.innerText = `${kpis.total_time_saved_hours} hrs`;
    kpiCompute.innerText = `${kpis.total_compute_saved_hours} hrs`;
    kpiOpt.innerText = `${kpis.avg_optimization}%`;
}

function renderChart(history) {
    // Take the last 30 runs for the chart, reverse them so oldest is left, newest right
    const chartData = history.slice(0, 30).reverse();
    
    const labels = chartData.map(run => run.run_id);
    const originalTimes = chartData.map(run => run.original_time);
    const optimizedTimes = chartData.map(run => run.optimized_time);

    const ctx = document.getElementById('optimizationChart').getContext('2d');
    
    if (optimizationChart) {
        optimizationChart.destroy();
    }

    // Create Gradient for Optimized Time area
    const gradientOpt = ctx.createLinearGradient(0, 0, 0, 400);
    gradientOpt.addColorStop(0, 'rgba(16, 185, 129, 0.4)');
    gradientOpt.addColorStop(1, 'rgba(16, 185, 129, 0.05)');

    optimizationChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: labels,
            datasets: [
                {
                    label: 'Original Execution Time (s)',
                    data: originalTimes,
                    borderColor: 'rgba(245, 158, 11, 0.5)',
                    backgroundColor: 'transparent',
                    borderWidth: 2,
                    borderDash: [5, 5],
                    pointRadius: 0,
                    tension: 0.4
                },
                {
                    label: 'Optimized Execution Time (s)',
                    data: optimizedTimes,
                    borderColor: '#10b981',
                    backgroundColor: gradientOpt,
                    borderWidth: 3,
                    fill: true,
                    pointBackgroundColor: '#10b981',
                    pointBorderColor: '#fff',
                    pointRadius: 4,
                    pointHoverRadius: 6,
                    tension: 0.4
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                legend: {
                    position: 'top',
                    labels: {
                        usePointStyle: true,
                        boxWidth: 8
                    }
                },
                tooltip: {
                    backgroundColor: 'rgba(15, 23, 42, 0.9)',
                    titleColor: '#fff',
                    bodyColor: '#e2e8f0',
                    borderColor: 'rgba(255,255,255,0.1)',
                    borderWidth: 1,
                    padding: 12,
                    boxPadding: 6
                }
            },
            scales: {
                y: {
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(255, 255, 255, 0.05)',
                        drawBorder: false
                    }
                },
                x: {
                    grid: {
                        display: false,
                        drawBorder: false
                    },
                    ticks: {
                        maxTicksLimit: 10
                    }
                }
            }
        }
    });
}

function renderTable(history) {
    historyTbody.innerHTML = '';
    
    // Render all 100 runs in the table
    history.forEach(run => {
        const tr = document.createElement('tr');
        
        // Cache badge styling
        const cacheBadgeClass = run.cache === 'HIT' ? 'badge-hit' : 'badge-miss';
        
        tr.innerHTML = `
            <td><strong>${run.run_id}</strong></td>
            <td><span style="color: var(--text-secondary); font-size: 0.85rem">${run.date}</span></td>
            <td><span class="badge badge-lang">${run.language}</span></td>
            <td><span class="badge ${cacheBadgeClass}">${run.cache}</span></td>
            <td><strong style="color: var(--success)">${run.opt_percentage}%</strong></td>
            <td>${run.original_time} s</td>
            <td>${run.time_saved} s</td>
        `;
        
        historyTbody.appendChild(tr);
    });
}

// Initial fetch
fetchMetrics();
