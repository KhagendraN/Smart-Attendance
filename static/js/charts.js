// Initialize charts when document is ready
document.addEventListener('DOMContentLoaded', function() {
    // Dashboard Overview Chart
    const dashboardChart = document.getElementById('attendanceChart');
    if (dashboardChart) {
        new Chart(dashboardChart, {
            type: 'line',
            data: {
                labels: getLast7Days(),
                datasets: [{
                    label: 'Attendance Rate',
                    data: [85, 88, 92, 87, 90, 89, 91],
                    borderColor: 'rgb(75, 192, 192)',
                    tension: 0.1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }

    // Reports Page Charts
    const averageChart = document.getElementById('averageAttendanceChart');
    if (averageChart) {
        new Chart(averageChart, {
            type: 'doughnut',
            data: {
                labels: ['Present', 'Absent'],
                datasets: [{
                    data: [85, 15],
                    backgroundColor: [
                        'rgb(75, 192, 192)',
                        'rgb(255, 99, 132)'
                    ]
                }]
            },
            options: {
                responsive: true
            }
        });
    }

    const trendChart = document.getElementById('attendanceTrendChart');
    if (trendChart) {
        new Chart(trendChart, {
            type: 'bar',
            data: {
                labels: getLast7Days(),
                datasets: [{
                    label: 'Daily Attendance',
                    data: [92, 88, 95, 85, 90, 89, 91],
                    backgroundColor: 'rgba(75, 192, 192, 0.5)'
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true,
                        max: 100
                    }
                }
            }
        });
    }
});

function getLast7Days() {
    const days = [];
    for (let i = 6; i >= 0; i--) {
        const date = new Date();
        date.setDate(date.getDate() - i);
        days.push(date.toLocaleDateString('en-US', { month: 'short', day: 'numeric' }));
    }
    return days;
}
