// SPDX-License-Identifier: Apache-2.0

import { describe, expect, it } from 'vitest';

import { drawTrajectories } from '../src/dashboard';

type RecordedCall =
  | { op: 'fillRect'; args: number[]; fillStyle: string }
  | { op: 'strokeRect'; args: number[]; strokeStyle: string }
  | { op: 'beginPath' }
  | { op: 'moveTo'; args: number[] }
  | { op: 'lineTo'; args: number[] }
  | { op: 'stroke'; strokeStyle: string };

describe('dashboard', () => {
  it('maps known report samples onto the canvas plot', () => {
    document.body.innerHTML = '<canvas id="traj" width="640" height="360"></canvas>';
    const traj = document.getElementById('traj') as HTMLCanvasElement;
    const calls: RecordedCall[] = [];
    const ctx = {
      fillStyle: '',
      strokeStyle: '',
      fillRect(...args: number[]) {
        calls.push({ op: 'fillRect', args, fillStyle: this.fillStyle });
      },
      strokeRect(...args: number[]) {
        calls.push({ op: 'strokeRect', args, strokeStyle: this.strokeStyle });
      },
      beginPath() {
        calls.push({ op: 'beginPath' });
      },
      moveTo(...args: number[]) {
        calls.push({ op: 'moveTo', args });
      },
      lineTo(...args: number[]) {
        calls.push({ op: 'lineTo', args });
      },
      stroke() {
        calls.push({ op: 'stroke', strokeStyle: this.strokeStyle });
      },
    };
    traj.getContext = () => ctx as unknown as CanvasRenderingContext2D;

    drawTrajectories({
      report_version: 1,
      git_sha: 'abc',
      sample: true,
      honesty: '',
      scenarios: [],
      trajectories: [
        { name: 's1', samples: [{ x: 0, y: 0 }, { x: 1, y: 0.1 }] },
        { name: 'too_short', samples: [{ x: 3, y: 0 }] },
      ],
    });

    expect(calls.find((c) => c.op === 'fillRect')).toEqual({
      op: 'fillRect',
      args: [0, 0, 640, 360],
      fillStyle: '#f8f8f8',
    });
    expect(calls.find((c) => c.op === 'strokeRect')).toEqual({
      op: 'strokeRect',
      args: [40, 20, 560, 300],
      strokeStyle: '#ccc',
    });
    // px = 40 + (x / 5) * 560, py = 320 - (y + 1) * 80
    expect(calls).toContainEqual({ op: 'moveTo', args: [40, 240] });
    expect(calls).toContainEqual({ op: 'lineTo', args: [152, 232] });
    const strokes = calls.filter((c) => c.op === 'stroke');
    expect(strokes).toEqual([{ op: 'stroke', strokeStyle: '#06c' }]);
  });
});
