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
  
  // Setup: Duplas, Melhor de 3, 6 games, Sim, Começar
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
  console.log('Court cards:', courtCards.length);
  await courtCards[0].click();
  await page.waitForTimeout(1000);
  
  // Verificar selects
  const selects = await page.$$('select.player-select');
  console.log('Selects:', selects.length);
  
  if (selects.length > 0) {
    // Listar opções do primeiro select
    const options = await selects[0].$$('option');
    console.log('Opções do select 1:', options.length);
    
    // Selecionar índice 1
    await selects[0].selectOption({ index: 1 });
    await page.waitForTimeout(500);
    
    // Verificar valor
    const value = await selects[0].evaluate(el => el.value);
    const selectedText = await selects[0].evaluate(el => el.options[el.selectedIndex]?.text);
    console.log(`Valor: "${value}", Texto: "${selectedText}"`);
    
    if (value && selectedText && !selectedText.includes('Jogador')) {
      console.log('✅ SUCESSO: Jogador selecionado aparece!');
    } else {
      console.log('❌ FALHA: Select ainda vazio ou placeholder');
    }
    
    await page.screenshot({ path: 'test_fix_result.png', fullPage: true });
    console.log('Screenshot: test_fix_result.png');
  }
  
  await browser.close();
})();
