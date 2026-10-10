// 验证 trend.html 渲染: 抓 console 错误 + pageerror + 统计 canvas 是否有内容
const { chromium } = require('playwright-core');

(async () => {
  const browser = await chromium.launch({ channel: 'msedge' });
  const page = await browser.newPage();
  const errors = [];
  page.on('console', m => { if (m.type() === 'error') errors.push('[console.error] ' + m.text()); });
  page.on('pageerror', e => errors.push('[pageerror] ' + e.message));

  await page.goto('file:///C:/Users/xlean/WorkBuddy/2026-09-02-13-57-28/AppAutoTest/reports/pipeline/trend.html');
  await page.waitForTimeout(2500);

  const info = await page.evaluate(() => {
    const canvases = [...document.querySelectorAll('canvas')];
    return {
      chartDefined: typeof Chart !== 'undefined',
      canvasCount: canvases.length,
      // canvas 有内容 = 宽高 >0 且非空白 (Chart.js 会设置 width/height 属性)
      canvasSizes: canvases.map(c => c.width + 'x' + c.height),
      kpiText: (document.querySelector('.kpis,#kpis,.verdict,h1') || {}).textContent?.trim().slice(0, 80) || '(无)',
      bodyChildren: document.body.children.length,
      tableRows: document.querySelectorAll('tr').length,
    };
  });

  console.log('=== 渲染检查 ===');
  console.log(JSON.stringify(info, null, 2));
  console.log('=== JS 错误 (' + errors.length + ') ===');
  errors.slice(0, 10).forEach(e => console.log(e));
  if (!errors.length) console.log('(无错误)');

  await page.screenshot({ path: 'logs/_trend_verify.png', fullPage: false });
  await browser.close();
})();
