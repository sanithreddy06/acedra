import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SCREENSHOT_DIR = path.resolve('../documentation/screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function capture() {
  console.log('>>> Launching Headless Chrome from:', CHROME_PATH);
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,960'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 960 });

  // -------------------------------------------------------------
  // 1. Login as Student (Alex Mercer)
  // -------------------------------------------------------------
  console.log('>>> 1. Logging in as Student...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Alex Mercer') || text.includes('Student')) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise((r) => setTimeout(r, 2000));

  // -------------------------------------------------------------
  // 2. Navigate to Placement Readiness
  // -------------------------------------------------------------
  console.log('>>> Navigating to Placement Readiness tab...');
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Placement Readiness') || text.includes('Readiness')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2500));

  // Screenshot 20: Placement Readiness Dashboard (Skill Gap Analysis active)
  console.log('>>> Capturing 20_placement_readiness_dashboard.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '20_placement_readiness_dashboard.png') });
  console.log('✅ Captured 20_placement_readiness_dashboard.png');

  // -------------------------------------------------------------
  // 3. Switch to Benchmark Comparison Chart
  // -------------------------------------------------------------
  console.log('>>> Switching to Benchmark Comparison Chart subtab...');
  const subtabs = await page.$$('button');
  for (const tab of subtabs) {
    const text = await page.evaluate((el) => el.textContent, tab);
    if (text.includes('Benchmark Comparison Chart')) {
      await tab.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2000));

  // Screenshot 21: Skill Gap Benchmark Comparison Chart
  console.log('>>> Capturing 21_skill_gap_analysis.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '21_skill_gap_analysis.png') });
  console.log('✅ Captured 21_skill_gap_analysis.png');

  // -------------------------------------------------------------
  // 4. Switch to Matching Corporate Opportunities & Click Apply
  // -------------------------------------------------------------
  console.log('>>> Navigating to Matching Corporate Opportunities subtab...');
  for (const tab of subtabs) {
    const text = await page.evaluate((el) => el.textContent, tab);
    if (text.includes('Matching Corporate Opportunities')) {
      await tab.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));

  // Click on "Apply" button to open application portal modal
  console.log('>>> Opening Student Application Modal...');
  const applyButtons = await page.$$('button');
  for (const btn of applyButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.trim() === 'Apply' || text.includes('Apply Now')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));

  // Screenshot 23: Student Application Portal
  console.log('>>> Capturing 23_student_application_portal.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '23_student_application_portal.png') });
  console.log('✅ Captured 23_student_application_portal.png');

  // Close Application Modal
  const closeBtn = await page.$('button svg.lucide-x');
  if (closeBtn) {
    await page.evaluate((el) => el.closest('button').click(), closeBtn);
  }
  await new Promise((r) => setTimeout(r, 1000));

  // -------------------------------------------------------------
  // 5. Logout and Login as Placement Officer (Marcus Vance)
  // -------------------------------------------------------------
  console.log('>>> Logging out and switching to Placement Officer...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    localStorage.clear();
  });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  // Quick fill placement officer
  const loginBtns = await page.$$('button');
  for (const btn of loginBtns) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Marcus Vance') || text.includes('Placement')) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise((r) => setTimeout(r, 2500));

  // Navigate to Recruitment & Placement
  console.log('>>> Navigating to Placement Officer Recruitment console...');
  const poNavButtons = await page.$$('aside button');
  for (const btn of poNavButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Recruitment') || text.includes('Placement')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2500));

  // Screenshot 22: Placement Officer Operations Console
  console.log('>>> Capturing 22_placement_officer_opportunities.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '22_placement_officer_opportunities.png') });
  console.log('✅ Captured 22_placement_officer_opportunities.png');

  await browser.close();
  console.log('>>> All Module 4 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('❌ Capture error:', err);
  process.exit(1);
});
