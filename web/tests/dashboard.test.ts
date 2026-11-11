// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from 'vitest';

import { drawTrajectories } from '../src/dashboard';

describe('dashboard', () => {
  it('draws trajectory samples on canvas', () => {
    document.body.innerHTML = '<canvas id="traj" width="100" height="100"></canvas>';
    const traj = document.getElementById('traj') as HTMLCanvasElement;
    traj.getContext = () =>
      ({
        fillRect: () => undefined,
        strokeRect: () => undefined,
        beginPath: () => undefined,
        moveTo: () => undefined,
        lineTo: () => undefined,
        stroke: () => undefined,
        fillStyle: '',
        strokeStyle: '',
      }) as unknown as CanvasRenderingContext2D;
    drawTrajectories({
      report_version: 1,
      git_sha: 'abc',
      sample: true,
      honesty: '',
      scenarios: [],
      trajectories: [
        { name: 's1', samples: [{ x: 0, y: 0 }, { x: 1, y: 0.1 }] },
      ],
    });
    expect(traj.width).toBe(100);
  });
});
