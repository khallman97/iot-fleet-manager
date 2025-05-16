'use client';

import { useEffect, useState } from 'react';

export default function HomePage() {
  const [devices, setDevices] = useState({});

  useEffect(() => {
    fetch('http://localhost:8000/api/status')  // <-- Docker Compose service hostname here
      .then(res => res.json())
      .then(data => setDevices(data))
      .catch(console.error);
  }, []);

  function formatBytes(bytes) {
    const sizes = ['B', 'KB', 'MB', 'GB', 'TB'];
    if (bytes === 0) return '0 B';
    const i = Math.floor(Math.log(bytes) / Math.log(1024));
    return (bytes / Math.pow(1024, i)).toFixed(2) + ' ' + sizes[i];
  }

  function DeviceRow({ deviceId, info }) {
    const { payload, last_seen, ip_from_request } = info;
    const { hostname, ip, metrics } = payload || {};
    if (!metrics) return null;

    return (
      <tr key={deviceId}>
        <td>{hostname || deviceId}</td>
        <td>{last_seen}</td>
        <td>{ip_from_request}</td>
        <td>{ip}</td>
        <td>{metrics.cpu_percent}%</td>
        <td>
          {formatBytes(metrics.memory.used)} / {formatBytes(metrics.memory.total)}
        </td>
        <td>
          {formatBytes(metrics.disk.used)} / {formatBytes(metrics.disk.total)}
        </td>
        <td>{metrics.uptime} seconds</td>
      </tr>
    );
  }

  return (
    <main style={{ padding: '2rem', fontFamily: 'Arial, sans-serif' }}>
      <h1>Pi Fleet Status</h1>
      <table border="1" cellPadding="8" style={{ borderCollapse: 'collapse' }}>
        <thead>
          <tr>
            <th>Hostname</th>
            <th>Last Seen</th>
            <th>Reported IP</th>
            <th>Payload IP</th>
            <th>CPU %</th>
            <th>Memory Used / Total</th>
            <th>Disk Used / Total</th>
            <th>Uptime</th>
          </tr>
        </thead>
        <tbody>
          {Object.entries(devices).map(([hostname, info]) => (
            <DeviceRow key={hostname} deviceId={hostname} info={info} />
          ))}
        </tbody>
      </table>
    </main>
  );
}
