const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  await page.goto('http://100.118.169.20:5175');
  await page.waitForTimeout(500);
  
  // Login
  const usernameInput = await page.$('input[placeholder="Usuário"]');
  const passwordInput = await page.$('input[placeholder="Senha"]');
  if (usernameInput && passwordInput) {
    await usernameInput.fill('admin');
    await passwordInput.fill('tennis123');
    await page.click('button[type="submit"]');
    await page.waitForTimeout(1500);
  }
  
  // Verificar URL atual
  console.log('URL:', page.url());
  
  // Verificar HTML da página
  const html = await page.content();
  console.log('Page content length:', html.length);
  
  // Verificar elementos na tela
  const buttons = await page.$$('button');
  console.log('Botões encontrados:', buttons.length);
  
  for (const btn of buttons) {
    const text = await btn.evaluate(el => el.textContent?.trim());
    console.log('  Button:', text);
  }
  
  // Verificar divs com texto
  const divs = await page.$$('div');
  console.log('Divs encontrados:', divs.length);
  
  // Tentar encontrar cards de quadra
  const courtCards = await page.$$('[class*="court"]');
  console.log('Court cards:', courtCards.length);
  
  // Screenshot
  await page.screenshot({ path: 'debug2.png', fullPage: true });
  console.log('Screenshot: debug2.png');
  
  await browser.close();
})();
