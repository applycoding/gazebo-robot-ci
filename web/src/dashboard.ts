// SPDX-License-Identifier: Apache-2.0

export type ScenarioRow = {
  name: string;
  pass: boolean;
  expected: string;
  observed: string;
};

export type CiReport = {
  report_version: number;
  git_sha: string;
  sample: boolean;
  honesty: string;
  scenarios: ScenarioRow[];
  trajectories: { name: string; samples: { x: number; y: number }[] }[];
};

export async function loadReport(url: string): Promise<CiReport> {
  const res = await fetch(url);
  if (!res.ok) {
    throw new Error(`Failed to load ${url}`);
  }
  return (await res.json()) as CiReport;
}

export function renderDashboard(
  report: CiReport,
  base: string,
  usingSampleFallback = false,
): void {
  const root = document.getElementById('app');
  if (!root) {
    return;
  }
  root.innerHTML = `
    <header>
      <h1>gazebo-robot-ci</h1>
      <p class="honesty"><strong>Simulation only.</strong> Synthetic worlds; not Nav2; not a certified safety function.</p>
      <p class="honesty">Recorded CI output; this page does not run Gazebo.</p>
      <p>Commit: <code id="sha">${report.git_sha}</code> ${report.sample ? '(sample)' : ''}</p>
      ${usingSampleFallback ? '<p id="fallback">Local preview uses sample-report.json</p>' : ''}
      <img src="${base}badge.svg" alt="CI badge" width="220" height="20" />
    </header>
    <canvas id="traj" width="640" height="360"></canvas>
    <table id="scenarios">
      <thead><tr><th>Scenario</th><th>Pass</th><th>Expected</th><th>Observed</th></tr></thead>
      <tbody></tbody>
    </table>
  `;
  const tbody = root.querySelector('#scenarios tbody');
  for (const row of report.scenarios) {
    const tr = document.createElement('tr');
    tr.innerHTML = `<td>${row.name}</td><td>${row.pass}</td><td>${row.expected}</td><td>${row.observed}</td>`;
    tbody?.appendChild(tr);
  }
  drawTrajectories(report);
}

export function drawTrajectories(report: CiReport): void {
  const canvas = document.getElementById('traj') as HTMLCanvasElement | null;
  if (!canvas) {
    return;
  }
  const ctx = canvas.getContext('2d');
  if (!ctx) {
    return;
  }
  ctx.fillStyle = '#f8f8f8';
  ctx.fillRect(0, 0, canvas.width, canvas.height);
  ctx.strokeStyle = '#ccc';
  ctx.strokeRect(40, 20, 560, 300);
  const colors = ['#06c', '#c60', '#090', '#900'];
  report.trajectories.forEach((traj, i) => {
    if (traj.samples.length < 2) {
      return;
    }
    ctx.strokeStyle = colors[i % colors.length] ?? '#333';
    ctx.beginPath();
    traj.samples.forEach((s, j) => {
      const px = 40 + (s.x / 5) * 560;
      const py = 320 - (s.y + 1) * 80;
      if (j === 0) {
        ctx.moveTo(px, py);
      } else {
        ctx.lineTo(px, py);
      }
    });
    ctx.stroke();
  });
}
