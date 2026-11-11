// SPDX-License-Identifier: Apache-2.0

import { expect, test } from '@playwright/test';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const __dirname = path.dirname(fileURLToPath(import.meta.url));

test('dashboard shows recorded CI output', async ({ page }) => {
  const errors: string[] = [];
  page.on('pageerror', (e) => errors.push(e.message));
  page.on('console', (msg) => {
    if (msg.type() === 'error') {
      errors.push(msg.text());
    }
  });

  await page.goto('./');
  await expect(page).toHaveTitle(/simulation only/i);
  await expect(page.getByText('Simulation only.')).toBeVisible();
  await expect(
    page.getByText('Recorded CI output; this page does not run Gazebo.'),
  ).toBeVisible();

  const report = await page.evaluate(async () => {
    const res = await fetch('ci-report.json');
    return res.json();
  });
  expect(report.sample).toBe(false);
  await expect(page.locator('#sha')).toContainText(report.git_sha);
  await expect(page.locator('#scenarios tbody tr')).toHaveCount(4);

  const canvas = page.locator('#traj');
  await expect(canvas).toBeVisible();
  const hasStroke = await canvas.evaluate((el: HTMLCanvasElement) => {
    const ctx = el.getContext('2d');
    if (!ctx) {
      return false;
    }
    const data = ctx.getImageData(0, 0, el.width, el.height).data;
    return data.some((v, i) => i % 4 !== 3 && v !== 248 && v !== 255);
  });
  expect(hasStroke).toBe(true);

  await page.screenshot({ path: path.join(__dirname, '../../docs/demo.png'), fullPage: true });
  expect(errors).toEqual([]);
});
