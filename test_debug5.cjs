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
  
  // Clicar na primeira quadra
  const courtCards = await page.$$('.court-card');
  await courtCards[0].click();
  await page.waitForTimeout(1000);
  
  // Pegar os selects
  const selects = await page.$$('select.player-select');
  
  // Listar opções do primeiro select
  console.log('=== Opções do Select 1 ===');
  const options0 = await selects[0].$$('option');
  for (let i = 0; i < options0.length; i++) {
    const val = await options0[i].evaluate(el => el.value);
    const text = await options0[i].evaluate(el => el.text);
    console.log(`  [${i}] value="${val}" text="${text}"`);
  }
  
  // Selecionar opção com índice 1 (o segundo jogador)
  console.log('\n=== Selecionando índice 1 ===');
  await selects[0].selectOption({ index: 1 });
  await page.waitForTimeout(1000);
  
  // Verificar valor após seleção
  const newValue = await selects[0].evaluate(el => el.value);
  const selectedText = await selects[0].evaluate(el => el.options[el.selectedIndex]?.text);
  console.log(`Após seleção: value="${newValue}", text="${selectedText}"`);
  
  // Screenshot
  await page.screenshot({ path: 'debug5_after_select.png', fullPage: true });
  console.log('Screenshot: debug5_after_select.png');
  
  await browser.close();
})();
