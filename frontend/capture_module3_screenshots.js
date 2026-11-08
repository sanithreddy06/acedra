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

  // 1. Login as Student (or Admin) to view recommendations
  console.log('>>> Logging in as Student (Alex Mercer)...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Alex Mercer') || text.includes('Student')) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise(r => setTimeout(r, 2000));

  // 2. Navigate to Personalized Roadmap
  console.log('>>> Navigating to Personalized Roadmap tab...');
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Personalized Roadmap') || text.includes('Recommendations') || text.includes('Roadmap')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 2000));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '16_recommendations_dashboard.png') });
  console.log('✅ Captured 16_recommendations_dashboard.png');

  // 3. Open Career Profile & Goals Modal
  console.log('>>> Opening Edit Career Goals Modal...');
  const careerButtons = await page.$$('button');
  for (const btn of careerButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Edit Career Goals') || text.includes('Career Goals')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '18_career_goals_interests_modal.png') });
  console.log('✅ Captured 18_career_goals_interests_modal.png');

  // Close Career Goals Modal
  const closeBtn1 = await page.$('button svg.lucide-x');
  if (closeBtn1) {
    await page.evaluate(el => el.closest('button').click(), closeBtn1);
  }
  await new Promise(r => setTimeout(r, 1000));

  // 4. Open Resource Catalogue Browser Modal
  console.log('>>> Opening Resource Catalogue Browser Modal...');
  const catButtons = await page.$$('button');
  for (const btn of catButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Resource Catalogue')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '19_catalogue_browser_modal.png') });
  console.log('✅ Captured 19_catalogue_browser_modal.png');

  // Close Catalogue Browser Modal
  const closeBtn2 = await page.$('button svg.lucide-x');
  if (closeBtn2) {
    await page.evaluate(el => el.closest('button').click(), closeBtn2);
  }
  await new Promise(r => setTimeout(r, 1000));

  // 5. Open Recommendation Detail Modal
  console.log('>>> Opening Recommendation Detail Modal...');
  const detailButtons = await page.$$('button');
  for (const btn of detailButtons) {
    const text = await page.evaluate(el => el.textContent, btn);
    if (text.includes('Details')) {
      await btn.click();
      break;
    }
  }
  await new Promise(r => setTimeout(r, 1500));
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '17_recommendation_detail_modal.png') });
  console.log('✅ Captured 17_recommendation_detail_modal.png');

  await browser.close();
  console.log('🎉 All Module 3 screenshots captured successfully!');
}

capture().catch(err => {
  console.error('Error during screenshot capture:', err);
  process.exit(1);
});
