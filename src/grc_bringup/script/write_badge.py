#!/usr/bin/env python3
# SPDX-License-Identifier: Apache-2.0

import json
import os
import sys
from pathlib import Path


def main():
    artifacts = Path(os.environ.get('GRC_ARTIFACTS_DIR', '/ws/artifacts'))
    report_path = artifacts / 'ci-report.json'
    if not report_path.is_file():
        print('missing report', file=sys.stderr)
        return 1
    with open(report_path, encoding='utf-8') as f:
        report = json.load(f)
    passed = sum(1 for row in report.get('scenarios', []) if row.get('pass'))
    total = 4
    label = f'{passed}/{total} expectations passed'
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" width="220" height="20">
  <rect width="220" height="20" fill="#555"/>
  <text x="10" y="14" font-family="sans-serif" font-size="12" fill="#fff">{label}</text>
</svg>
'''
    badge_path = artifacts / 'badge.svg'
    badge_path.write_text(svg, encoding='utf-8')
    return 0


if __name__ == '__main__':
    sys.exit(main())
