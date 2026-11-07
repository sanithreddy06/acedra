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
    args: ['--no-sandbox', '--disable-setuid-sandbox', '--window-size=1440,900'],
  });

  const page = await browser.newPage();
  await page.setViewport({ width: 1440, height: 900 });

  // 1. Login Page
  console.log('>>> Capturing 01_login_screen.png...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '01_login_screen.png'), fullPage: false });

  // Perform Login as Admin
  console.log('>>> Logging in as Administrator...');
  // Click on "Dr. Sarah Jenkins (Admin / HOD)" quick fill
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Sarah Jenkins') || text.includes('Admin')) {
      await btn.click();
      break;
    }
  }

  // Click submit button
  await page.click('button[type="submit"]');
  await new Promise(r => setTimeout(r, 2500));

  // 2. Student Directory Tab
  console.log('>>> Navigating to Student Directory...');
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Student Directory')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  console.log('>>> Capturing 02_student_directory.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '02_student_directory.png') });

  // 3. Open Student Profile Modal
  console.log('>>> Opening Student Profile Modal...');
  const rows = await page.$$('tbody tr');
  if (rows.length > 0) {
    await rows[0].click();
    await new Promise(r => setTimeout(r, 1500));

    // 03_student_profile_overview.png
    console.log('>>> Capturing 03_student_profile_overview.png...');
    await page.screenshot({ path: path.join(SCREENSHOT_DIR, '03_student_profile_overview.png') });

    // Click "Academic & SGPA Progression" tab
    const tabButtons = await page.$$('div.border-b button');
    for (const t of tabButtons) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text.includes('Academic')) {
        await t.click();
        await new Promise(r => setTimeout(r, 1000));
        console.log('>>> Capturing 04_student_academic_progression.png...');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '04_student_academic_progression.png') });
        break;
      }
    }

    // Click "Attendance Intelligence" tab
    for (const t of tabButtons) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text.includes('Attendance')) {
        await t.click();
        await new Promise(r => setTimeout(r, 1000));
        console.log('>>> Capturing 05_student_attendance_intelligence.png...');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '05_student_attendance_intelligence.png') });
        break;
      }
    }

    // Click "Continuous Evaluations" tab
    for (const t of tabButtons) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text.includes('Continuous') || text.includes('Evaluations')) {
        await t.click();
        await new Promise(r => setTimeout(r, 1000));
        console.log('>>> Capturing 06_student_assessments.png...');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '06_student_assessments.png') });
        break;
      }
    }

    // Click "Skill Matrix" tab
    for (const t of tabButtons) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text.includes('Skill')) {
        await t.click();
        await new Promise(r => setTimeout(r, 1000));
        console.log('>>> Capturing 07_student_skill_matrix.png...');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '07_student_skill_matrix.png') });
        break;
      }
    }

    // Click "Projects & Experience" tab
    for (const t of tabButtons) {
      const text = await page.evaluate(el => el.textContent, t);
      if (text.includes('Projects') || text.includes('Portfolio')) {
        await t.click();
        await new Promise(r => setTimeout(r, 1000));
        console.log('>>> Capturing 08_student_portfolio_experience.png...');
        await page.screenshot({ path: path.join(SCREENSHOT_DIR, '08_student_portfolio_experience.png') });
        break;
      }
    }

    // Close modal by pressing Escape
    await page.keyboard.press('Escape');
    await new Promise(r => setTimeout(r, 800));
  }

  // 4. Data Import Center
  console.log('>>> Navigating to Data Import Center...');
  const sideNavBtns = await page.$$('aside button');
  for (const btn of sideNavBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Data Import')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1200));
  console.log('>>> Capturing 09_data_import_center.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '09_data_import_center.png') });

  // 5. Institutional Analytics
  console.log('>>> Navigating to Institutional Analytics...');
  for (const btn of sideNavBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Institutional Analytics')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  console.log('>>> Capturing 10_admin_institutional_analytics.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '10_admin_institutional_analytics.png') });

  // 6. Switch to Faculty Role
  console.log('>>> Switching role to Faculty...');
  for (const btn of sideNavBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Faculty') && text.includes('Elena')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));

  // Navigate to Cohort Performance Analytics
  const facultyNavBtns = await page.$$('aside button');
  for (const btn of facultyNavBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Cohort Performance')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  console.log('>>> Capturing 11_faculty_cohort_analytics.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '11_faculty_cohort_analytics.png') });

  await browser.close();
  console.log('>>> All screenshots successfully captured in documentation/screenshots/ !');
}

capture().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
