const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('http://100.118.169.20:5175');
  await page.waitForTimeout(500);
  
  // Login e setup (Duplas, Melhor de 3, 6 games, Sim, Começar)
  await page.fill('input[placeholder="Usuário"]', 'admin');
  await page.fill('input[placeholder="Senha"]', 'tennis123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);
  
  const allButtons = await page.$$('button');
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Duplas')) { await btn.click(); await page.waitForTimeout(100); break; }
  }
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Melhor de 3')) { await btn.click(); await page.waitForTimeout(100); break; }
  }
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('6 games')) { await btn.click(); await page.waitForTimeout(100); break; }
  }
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Sim')) { await btn.click(); await page.waitForTimeout(100); break; }
  }
  for (const btn of allButtons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Começar')) { await btn.click(); await page.waitForTimeout(1500); break; }
  }
  
  // Ver estrutura da página
  const courtCards = await page.$$('.court-card');
  console.log('Court cards:', courtCards.length);
  
  if (courtCards.length > 0) {
    // Clicar na primeira quadra
    await courtCards[0].click();
    await page.waitForTimeout(1000);
    
    console.log('URL após clicar quadra:', page.url());
    
    // Verificar elementos após clicar
    const allSelects = await page.$$('select');
    console.log('Selects após clicar:', allSelects.length);
    
    for (let i = 0; i < allSelects.length; i++) {
      const sel = allSelects[i];
      const className = await sel.evaluate(el => el.className);
      const value = await sel.evaluate(el => el.value);
      const options = await sel.$$('option');
      console.log(`Select ${i}: class="${className}", value="${value}", options=${options.length}`);
    }
    
    // Verificar todos os botões
    const btns = await page.$$('button');
    console.log('Botões:', btns.length);
    for (const btn of btns) {
      const text = await btn.evaluate(el => el.textContent?.trim());
      console.log('  -', text);
    }
    
    await page.screenshot({ path: 'debug4_court_open.png', fullPage: true });
    console.log('Screenshot: debug4_court_open.png');
  }
  
  await browser.close();
})();
