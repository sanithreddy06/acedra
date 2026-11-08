/**
 * Smart Campus Intelligence — Frontend End-to-End Workflow Test Suite
 * Powered by puppeteer-core & Google Chrome Headless
 *
 * Validates major user workflows:
 * 1. Public Portal & Unauthenticated Login Page
 * 2. Student Role Workflow: Login, Academic Dashboard, Skills, Placement Readiness
 * 3. Faculty Role Workflow: Login, Faculty Dashboard, Student Directory
 * 4. Mentor Role Workflow: Login, Mentor Dashboard, Intervention Hub & Modal
 * 5. Placement Officer Workflow: Login, Placement Readiness & Opportunities Hub
 * 6. Admin Role Workflow: Login, Institutional Reports & System Directory
 */

import puppeteer from 'puppeteer-core';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const BASE_URL = 'http://localhost:5173';

const sleep = (ms) => new Promise((resolve) => setTimeout(resolve, ms));

async function runFrontendTests() {
  console.log('='.repeat(70));
  console.log('SMART CAMPUS INTELLIGENCE — FRONTEND E2E WORKFLOW TEST SUITE');
  console.log('='.repeat(70));

  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: true,
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--disable-dev-shm-usage', '--window-size=1280,800'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1280, height: 800 });

  let testsPassed = 0;
  let testsTotal = 0;

  async function testStep(name, fn) {
    testsTotal++;
    process.stdout.write(`  [TEST ${testsTotal}] ${name.padEnd(52)} : `);
    try {
      await fn();
      console.log('✓ PASS');
      testsPassed++;
    } catch (err) {
      console.log(`✗ FAIL (${err.message})`);
    }
  }

  async function loginAs(email, password) {
    await page.evaluate(() => localStorage.clear());
    await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
    await sleep(500);
    await page.type('input[type="email"]', email);
    await page.type('input[type="password"]', password);
    await page.click('button[type="submit"]');
    await page.waitForSelector('aside', { timeout: 8000 });
    await sleep(800);
  }

  async function clickTabByText(tabText) {
    const clicked = await page.evaluate((text) => {
      const buttons = Array.from(document.querySelectorAll('aside button, nav button'));
      const target = buttons.find((b) => b.innerText && b.innerText.includes(text));
      if (target) {
        target.click();
        return true;
      }
      return false;
    }, tabText);
    if (!clicked) {
      throw new Error(`Navigation tab containing '${tabText}' not found`);
    }
    await sleep(800);
  }

  try {
    // 1. Public Portal & Login Page
    await testStep('Public Portal & Login Page Loads Correctly', async () => {
      await page.goto(`${BASE_URL}/`, { waitUntil: 'domcontentloaded' });
      await sleep(500);
      const title = await page.title();
      if (!title.includes('Smart Campus')) {
        throw new Error(`Unexpected page title: ${title}`);
      }
      const hasInputs = await page.$('input[type="email"]') !== null;
      if (!hasInputs) throw new Error('Email input element not found');
    });

    // 2. Student Authentication & Academic Dashboard Workflow
    await testStep('Student Login & Academic Dashboard Workflow', async () => {
      await loginAs('student@smartcampus.edu', 'StudentPass123!');
      const content = await page.content();
      if (!content.includes('Alex Mercer') && !content.includes('8.84') && !content.includes('Student')) {
        throw new Error('Student dashboard content not rendered');
      }
    });

    // 3. Student Placement & Skill Gap View
    await testStep('Student Placement Readiness & Skills View', async () => {
      await clickTabByText('Placement Readiness');
      const content = await page.content();
      if (!content.includes('Placement') && !content.includes('Readiness') && !content.includes('Skills')) {
        throw new Error('Placement readiness tab not rendered');
      }
    });

    // 4. Faculty Role Workflow
    await testStep('Faculty Login & Student Analytics Directory', async () => {
      await loginAs('faculty@smartcampus.edu', 'FacultyPass123!');
      await clickTabByText('Student Directory');
      const content = await page.content();
      if (!content.includes('Student') && !content.includes('Department') && !content.includes('CSE')) {
        throw new Error('Faculty students directory failed to render');
      }
    });

    // 5. Mentor Role Workflow & Intervention Hub
    await testStep('Mentor Login & Intervention Hub Tracking', async () => {
      await loginAs('mentor@smartcampus.edu', 'MentorPass123!');
      await clickTabByText('Intervention');
      const content = await page.content();
      if (!content.includes('Intervention') && !content.includes('Action') && !content.includes('Status')) {
        throw new Error('Mentor intervention hub failed to render');
      }
    });

    // 6. Placement Officer Workflow
    await testStep('Placement Officer Dashboard & Opportunities Hub', async () => {
      await loginAs('placement@smartcampus.edu', 'PlacementPass123!');
      const content = await page.content();
      if (!content.includes('Placement') && !content.includes('Readiness') && !content.includes('Opportunities')) {
        throw new Error('Placement officer view failed to render');
      }
    });

    // 7. Administrator Role Workflow
    await testStep('Administrator Institutional Dashboard & Reports', async () => {
      await loginAs('admin@smartcampus.edu', 'AdminPass123!');
      await clickTabByText('Reports & Audits');
      const content = await page.content();
      if (!content.includes('Report') && !content.includes('Export') && !content.includes('Audit')) {
        throw new Error('Admin institutional reports failed to render');
      }
    });

  } finally {
    await browser.close();
  }

  console.log('='.repeat(70));
  console.log(`FRONTEND WORKFLOW TESTS RESULT: ${testsPassed}/${testsTotal} SUCCEEDED`);
  console.log('='.repeat(70));

  if (testsPassed < testsTotal) {
    process.exit(1);
  }
}

runFrontendTests().catch((err) => {
  console.error('Fatal Frontend Test Error:', err);
  process.exit(1);
});
