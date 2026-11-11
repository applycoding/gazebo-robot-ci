// SPDX-License-Identifier: Apache-2.0

import { defineConfig } from '@playwright/test';

const PORT = 4173;
const baseURL = `http://127.0.0.1:${PORT}/gazebo-robot-ci/`;

export default defineConfig({
  testDir: 'e2e',
  fullyParallel: false,
  retries: 0,
  use: {
    baseURL,
    trace: 'off',
  },
  webServer: {
    command: `npm run preview -- --port ${PORT}`,
    url: baseURL,
    reuseExistingServer: false,
  },
});
