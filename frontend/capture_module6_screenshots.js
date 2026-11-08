import puppeteer from 'puppeteer-core';
import path from 'path';
import fs from 'fs';

const CHROME_PATH = '/Applications/Google Chrome.app/Contents/MacOS/Google Chrome';
const SCREENSHOT_DIR = path.resolve('../documentation/screenshots');

if (!fs.existsSync(SCREENSHOT_DIR)) {
  fs.mkdirSync(SCREENSHOT_DIR, { recursive: true });
}

async function loginAsRole(page, roleKeyword) {
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await page.evaluate(() => localStorage.clear());
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await new Promise((r) => setTimeout(r, 1000));

  // Find demo credential pill
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes(roleKeyword)) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise((r) => setTimeout(r, 2000));
}

async function navigateSidebar(page, tabKeyword) {
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes(tabKeyword)) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));
}

async function capture() {
  console.log('>>> Launching Headless Chrome for Module 6 Screenshots...');
  const browser = await puppeteer.launch({
    executablePath: CHROME_PATH,
    headless: 'new',
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,960'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 960 });

  // -------------------------------------------------------------
  // Screenshot 28: Student Integrated Dashboard
  // -------------------------------------------------------------
  console.log('>>> 1. Capturing Screenshot 28: Student Integrated Dashboard...');
  await loginAsRole(page, 'Student');
  await navigateSidebar(page, 'Academic Dashboard');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '28_student_integrated_dashboard.png'),
    fullPage: false,
  });
  console.log('✅ Captured 28_student_integrated_dashboard.png');

  // -------------------------------------------------------------
  // Screenshot 29: Faculty Cohort Dashboard
  // -------------------------------------------------------------
  console.log('>>> 2. Capturing Screenshot 29: Faculty Cohort Dashboard...');
  await loginAsRole(page, 'Faculty');
  await navigateSidebar(page, 'Faculty Dashboard');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '29_faculty_cohort_dashboard.png'),
    fullPage: false,
  });
  console.log('✅ Captured 29_faculty_cohort_dashboard.png');

  // -------------------------------------------------------------
  // Screenshot 30: Mentor Interventions Hub
  // -------------------------------------------------------------
  console.log('>>> 3. Capturing Screenshot 30: Mentor Interventions Hub...');
  await loginAsRole(page, 'Mentor');
  await navigateSidebar(page, 'Interventions Hub');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '30_mentor_interventions_hub.png'),
    fullPage: false,
  });
  console.log('✅ Captured 30_mentor_interventions_hub.png');

  // -------------------------------------------------------------
  // Screenshot 33: Intervention Detail Dossier Modal
  // -------------------------------------------------------------
  console.log('>>> 4. Capturing Screenshot 33: Intervention Detail Dossier Modal...');
  // Click on the first intervention card in the hub
  const interventionCards = await page.$$('div.cursor-pointer');
  if (interventionCards.length > 0) {
    await interventionCards[0].click();
    await new Promise((r) => setTimeout(r, 1500));
    await page.screenshot({
      path: path.join(SCREENSHOT_DIR, '33_intervention_detail_modal.png'),
      fullPage: false,
    });
    console.log('✅ Captured 33_intervention_detail_modal.png');

    // Close modal
    const closeBtn = await page.$('button.rounded-xl');
    if (closeBtn) await closeBtn.click();
    await new Promise((r) => setTimeout(r, 500));
  }

  // -------------------------------------------------------------
  // Screenshot 31: Administrator / HOD Executive Dashboard
  // -------------------------------------------------------------
  console.log('>>> 5. Capturing Screenshot 31: Admin Executive Dashboard...');
  await loginAsRole(page, 'Admin');
  await navigateSidebar(page, 'Executive Intelligence');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '31_admin_executive_dashboard.png'),
    fullPage: false,
  });
  console.log('✅ Captured 31_admin_executive_dashboard.png');

  // -------------------------------------------------------------
  // Screenshot 34: Institutional Reports Center
  // -------------------------------------------------------------
  console.log('>>> 6. Capturing Screenshot 34: Institutional Reports Center...');
  await navigateSidebar(page, 'Reports & Audits Center');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '34_institutional_reports_center.png'),
    fullPage: false,
  });
  console.log('✅ Captured 34_institutional_reports_center.png');

  // -------------------------------------------------------------
  // Screenshot 32: Placement Officer Dashboard
  // -------------------------------------------------------------
  console.log('>>> 7. Capturing Screenshot 32: Placement Officer Dashboard...');
  await loginAsRole(page, 'Placement');
  await navigateSidebar(page, 'Placement Hub');
  await new Promise((r) => setTimeout(r, 1500));
  await page.screenshot({
    path: path.join(SCREENSHOT_DIR, '32_placement_officer_dashboard.png'),
    fullPage: false,
  });
  console.log('✅ Captured 32_placement_officer_dashboard.png');

  await browser.close();
  console.log('>>> All 7 screenshots successfully captured and saved to documentation/screenshots/!');
}

capture().catch((err) => {
  console.error('Error during capture:', err);
  process.exit(1);
});
