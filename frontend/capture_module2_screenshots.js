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

  // 1. Login as Admin
  console.log('>>> Logging in as Administrator...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Sarah Jenkins') || text.includes('Admin')) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise(r => setTimeout(r, 2000));

  // 2. Early-Warning & Risk Dashboard
  console.log('>>> Navigating to Early-Warning & Risk Dashboard...');
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Early-Warning & Risk')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '12_risk_early_warning_dashboard.png') });
  console.log('✅ Captured 12_risk_early_warning_dashboard.png');

  // 3. Open Policy Rule Configuration Modal
  console.log('>>> Opening Policy Rule Configuration Modal...');
  const configButtons = await page.$$('button');
  for (const btn of configButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Configure Rules')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '14_risk_policy_rule_configuration.png') });
  console.log('✅ Captured 14_risk_policy_rule_configuration.png');

  // Close Rule Modal
  const closeBtn = await page.$('button svg.lucide-x');
  if (closeBtn) {
    await page.evaluate(el => el.closest('button').click(), closeBtn);
  }
  await new Promise(r => setTimeout(r, 1000));

  // 4. Open Alert Detail Modal
  console.log('>>> Opening Alert Detail Modal...');
  const reviewButtons = await page.$$('button');
  for (const btn of reviewButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Review')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '13_risk_alert_detail_modal.png') });
  console.log('✅ Captured 13_risk_alert_detail_modal.png');

  // Close Alert Detail Modal
  const closeAlertBtn = await page.$('button svg.lucide-x');
  if (closeAlertBtn) {
    await page.evaluate(el => el.closest('button').click(), closeAlertBtn);
  }
  await new Promise(r => setTimeout(r, 1000));

  // 5. Navigate to Student Directory and open Student Dossier Early-Warning Tab
  console.log('>>> Navigating to Student Directory...');
  const navBtns2 = await page.$$('aside button');
  for (const btn of navBtns2) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Student Directory')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));

  // Click View Dossier on first student
  console.log('>>> Opening Student Dossier Modal...');
  const dossierBtns = await page.$$('button');
  for (const btn of dossierBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('View Dossier')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));

  // Switch to Early-Warning Alerts Tab
  console.log('>>> Switching to Early-Warning Alerts Tab...');
  const tabBtns = await page.$$('div.border-b button');
  for (const btn of tabBtns) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Early-Warning Alerts')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '15_student_dossier_early_warning_tab.png') });
  console.log('✅ Captured 15_student_dossier_early_warning_tab.png');

  await browser.close();
  console.log('🎉 All Module 2 screenshots captured successfully!');
}

capture().catch(err => {
  console.error('Error capturing screenshots:', err);
  process.exit(1);
});
