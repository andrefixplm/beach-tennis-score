const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('http://100.118.169.20:5175');
  await page.waitForTimeout(500);
  
  // Login
  await page.fill('input[placeholder="Usuário"]', 'admin');
  await page.fill('input[placeholder="Senha"]', 'tennis123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);
  
  console.log('URL após login:', page.url());
  
  // Selecionar modo: Duplas
  const buttons = await page.$$('button');
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Duplas')) {
      await btn.click();
      console.log('Selecionou Duplas');
      break;
    }
  }
  await page.waitForTimeout(200);
  
  // Melhor de 3
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Melhor de 3')) {
      await btn.click();
      console.log('Selecionou Melhor de 3');
      break;
    }
  }
  await page.waitForTimeout(200);
  
  // 6 games
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('6 games')) {
      await btn.click();
      console.log('Selecionou 6 games');
      break;
    }
  }
  await page.waitForTimeout(200);
  
  // Sim tiebreak
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Sim')) {
      await btn.click();
      console.log('Selecionou tiebreak');
      break;
    }
  }
  await page.waitForTimeout(200);
  
  // Começar
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    if (text?.includes('Começar')) {
      await btn.click();
      console.log('Clicou Começar');
      break;
    }
  }
  await page.waitForTimeout(1500);
  
  console.log('URL após começar:', page.url());
  
  // Verificar quadras
  const courtCards = await page.$$('[class*="court"]');
  console.log('Court cards encontrados:', courtCards.length);
  
  // Verificar selects de jogadores
  const selects = await page.$$('select');
  console.log('Selects encontrados:', selects.length);
  
  // Screenshot final
  await page.screenshot({ path: 'debug3_courts.png', fullPage: true });
  console.log('Screenshot: debug3_courts.png');
  
  await browser.close();
})();
