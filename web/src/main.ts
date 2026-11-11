// SPDX-License-Identifier: Apache-2.0

import { loadReport, renderDashboard } from './dashboard';

async function boot(): Promise<void> {
  const base = import.meta.env.BASE_URL;
  const urlParams = new URLSearchParams(window.location.search);
  const defaultReport = import.meta.env.PROD ? 'ci-report.json' : 'sample-report.json';
  const reportName = urlParams.get('report') ?? defaultReport;
  const reportPath = `${base}${reportName}`.replace(/\/\//g, '/');
  try {
    const report = await loadReport(reportPath);
    renderDashboard(report, base, report.sample === true);
  } catch (err) {
    const root = document.getElementById('app');
    if (root) {
      root.textContent = `Failed to load report: ${String(err)}`;
    }
  }
}

void boot();
