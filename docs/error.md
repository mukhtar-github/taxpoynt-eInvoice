venvmukhtar-tanimu@mtg:~/taxpoynt-eInvoice/testing/e2e$ cd /home/mukhtar-tanimu/taxpoynt-eInvoice/testing/e2e && ENV_FILE=.env.prod npx playwright test tests/odoo-to-firs-production.spec.js

Running 5 tests using 1 worker

Configuration Error: HTML reporter output folder clashes with the tests output folder:

    html reporter folder: /home/mukhtar-tanimu/taxpoynt-eInvoice/testing/e2e/test-results/html-report
    test results folder: /home/mukhtar-tanimu/taxpoynt-eInvoice/testing/e2e/test-results

HTML reporter will clear its output directory prior to being generated, which will lead to the artifact loss.
…rkflow › Step 1: Verify and retrieve specific Odoo invoice
Authenticating with API at https://taxpoynt-einvoice-production.up.railway.app/api/v1...
Making request to: https://taxpoynt-einvoice-production.up.railway.app/api/v1/auth/login
Attempt 1 failed with error: Request failed with status code 429
Retrying in 5000ms...
Making request to: https://taxpoynt-einvoice-production.up.railway.app/api/v1/auth/login
Attempt 2 failed with error: Request failed with status code 429
Retrying in 10000ms...
Making request to: https://taxpoynt-einvoice-production.up.railway.app/api/v1/auth/login
Attempt 3 failed with error: Request failed with status code 429
❌ Authentication failed: Request failed with status code 429
Response status: 429
Response data: {
  "detail": "Rate limit exceeded. Please try again later."
}
  1) [chromium] › tests/odoo-to-firs-production.spec.js:130:3 › Production Odoo to FIRS E2E Workflow › Step 1: Verify and retrieve specific Odoo invoice 

    AxiosError: Request failed with status code 429

  1 failed
    [chromium] › tests/odoo-to-firs-production.spec.js:130:3 › Production Odoo to FIRS E2E Workflow › Step 1: Verify and retrieve specific Odoo invoice 
  4 did not run

  Serving HTML report at http://localhost:9323. Press Ctrl+C to quit.
^C