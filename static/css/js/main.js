// Use a gradient stroke for better look
const ctx = document.getElementById('sensorChart').getContext('2d');
const gradientTemp = ctx.createLinearGradient(0, 0, 0, 200);
gradientTemp.addColorStop(0, 'rgba(255, 99, 132, 0.7)');
gradientTemp.addColorStop(1, 'rgba(255, 99, 132, 0.1)');

const gradientHumid = ctx.createLinearGradient(0, 0, 0, 200);
gradientHumid.addColorStop(0, 'rgba(54, 162, 235, 0.7)');
gradientHumid.addColorStop(1, 'rgba(54, 162, 235, 0.1)');

const gradientMoist = ctx.createLinearGradient(0, 0, 0, 200);
gradientMoist.addColorStop(0, 'rgba(75, 192, 192, 0.7)');
gradientMoist.addColorStop(1, 'rgba(75, 192, 192, 0.1)');

// Chart setup
const sensorChart = new Chart(ctx, {
  type: 'line',
  data: {
    labels: [],
    datasets: [
      {
        label: 'Temperature (°C)',
        data: [],
        borderColor: 'red',
        backgroundColor: gradientTemp,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Humidity (%)',
        data: [],
        borderColor: 'blue',
        backgroundColor: gradientHumid,
        fill: true,
        tension: 0.4
      },
      {
        label: 'Soil Moisture',
        data: [],
        borderColor: 'green',
        backgroundColor: gradientMoist,
        fill: true,
        tension: 0.4
      }
    ]
  },
  options: {
    animation: false,
    responsive: true,
    plugins: {
      tooltip: {
        enabled: true
      },
      legend: {
        labels: {
          color: '#333'
        }
      }
    },
    scales: {
      x: {
        title: { display: true, text: 'Time' },
        ticks: { color: '#555' }
      },
      y: {
        beginAtZero: true,
        ticks: { color: '#555' }
      }
    }
  }
});
