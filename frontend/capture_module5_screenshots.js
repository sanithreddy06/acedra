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
  // 2. Navigate to Smart Campus AI tab
  // -------------------------------------------------------------
  console.log('>>> Navigating to Smart Campus AI tab in sidebar...');
  await page.waitForSelector('aside');
  const navButtons = await page.$$('aside button');
  for (const btn of navButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Smart Campus AI') || text.includes('Campus AI')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2000));

  // Screenshot 24: Mode A (Public University Guide)
  console.log('>>> Switching to Mode A (Public Assistant)...');
  const modeButtons = await page.$$('button');
  for (const btn of modeButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Mode A: Public Assistant')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));

  // Click on the existing attendance inquiry conversation or prompt
  const convItems = await page.$$('div.cursor-pointer');
  if (convItems.length > 0) {
    await convItems[0].click();
  }
  await new Promise((r) => setTimeout(r, 1500));

  console.log('>>> Capturing 24_conversational_ai_public.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '24_conversational_ai_public.png') });
  console.log('✅ Captured 24_conversational_ai_public.png');

  // Screenshot 27: Citation Excerpt Preview Modal
  console.log('>>> Opening Citation Preview Modal...');
  const citButtons = await page.$$('button');
  for (const btn of citButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('REVA') || text.includes('Attendance') || text.includes('%')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));

  console.log('>>> Capturing 27_rag_retrieval_citations.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '27_rag_retrieval_citations.png') });
  console.log('✅ Captured 27_rag_retrieval_citations.png');

  // Close Citation Modal
  const closeCitBtn = await page.$$('button');
  for (const btn of closeCitBtn) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Close Excerpt') || text === '×') {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1000));

  // -------------------------------------------------------------
  // 3. Switch to Mode B (Personal Student Assistant)
  // -------------------------------------------------------------
  console.log('>>> Switching to Mode B (Personal Student Assistant)...');
  const modeBButtons = await page.$$('button');
  for (const btn of modeBButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Mode B: Personal Student')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2000));

  // Select Alex's Personal conversation
  const personalConvItems = await page.$$('div.cursor-pointer');
  for (const item of personalConvItems) {
    const text = await page.evaluate((el) => el.textContent, item);
    if (text.includes('Alex') || text.includes('Personal')) {
      await item.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 1500));

  console.log('>>> Capturing 25_conversational_ai_personal.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '25_conversational_ai_personal.png') });
  console.log('✅ Captured 25_conversational_ai_personal.png');

  // -------------------------------------------------------------
  // 4. Logout and Login as Administrator for RAG Knowledge Base
  // -------------------------------------------------------------
  console.log('>>> Switching to Administrator (Dr. Sarah Jenkins)...');
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });
  await page.evaluate(() => {
    localStorage.clear();
  });
  await page.goto('http://localhost:5173', { waitUntil: 'networkidle0' });

  const adminLoginBtns = await page.$$('button');
  for (const btn of adminLoginBtns) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('Sarah Jenkins') || text.includes('Admin')) {
      await btn.click();
      break;
    }
  }

  await page.click('button[type="submit"]');
  await new Promise((r) => setTimeout(r, 2500));

  // Navigate to RAG Knowledge Base
  console.log('>>> Navigating to RAG Knowledge Base tab in sidebar...');
  const adminNavButtons = await page.$$('aside button');
  for (const btn of adminNavButtons) {
    const text = await page.evaluate((el) => el.textContent, btn);
    if (text.includes('RAG Knowledge Base') || text.includes('Knowledge Base')) {
      await btn.click();
      break;
    }
  }
  await new Promise((r) => setTimeout(r, 2500));

  console.log('>>> Capturing 26_rag_document_management.png...');
  await page.screenshot({ path: path.join(SCREENSHOT_DIR, '26_rag_document_management.png') });
  console.log('✅ Captured 26_rag_document_management.png');

  await browser.close();
  console.log('>>> All Module 5 screenshots captured successfully!');
}

capture().catch((err) => {
  console.error('❌ Capture error:', err);
  process.exit(1);
});
