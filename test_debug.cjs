const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Login
  await page.goto('http://100.118.169.20:5175');
  await page.fill('input[placeholder="Usuário"]', 'admin');
  await page.fill('input[placeholder="Senha"]', 'tennis123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(1000);
  
  // Ir para a tela de partidas (clicar em qualquer quadra)
  const courts = await page.$$('.court-card');
  if (courts.length > 0) {
    await courts[0].click();
    await page.waitForTimeout(500);
    
    // Capturar screenshot
    await page.screenshot({ path: 'debug_court.png', fullPage: true });
    console.log('Screenshot salvo: debug_court.png');
    
    // Verificar os selects de jogadores
    const selects = await page.$$('select.player-select');
    console.log(`Encontrados ${selects.length} selects de jogadores`);
    
    // Verificar os valores dos selects
    for (let i = 0; i < selects.length; i++) {
      const value = await selects[i].evaluate(el => el.value);
      const selectedText = await selects[i].evaluate(el => el.options[el.selectedIndex]?.text);
      console.log(`Select ${i}: value="${value}", text="${selectedText}"`);
    }
    
    // Tentar selecionar um jogador no primeiro select
    if (selects.length > 0) {
      const options = await selects[0].$$('option');
      console.log(`Select 1 tem ${options.length} opções`);
      
      // Selecionar a segunda opção (índice 1, se existir)
      if (options.length > 1) {
        const optionValue = await options[1].evaluate(el => el.value);
        const optionText = await options[1].evaluate(el => el.text);
        console.log(`Selecionando: value="${optionValue}", text="${optionText}"`);
        
        await selects[0].selectOption({ index: 1 });
        await page.waitForTimeout(500);
        
        // Verificar valor após seleção
        const newValue = await selects[0].evaluate(el => el.value);
        const newText = await selects[0].evaluate(el => el.options[el.selectedIndex]?.text);
        console.log(`Após seleção: value="${newValue}", text="${newText}"`);
        
        await page.screenshot({ path: 'debug_after_select.png', fullPage: true });
        console.log('Screenshot após seleção: debug_after_select.png');
      }
    }
  } else {
    console.log('Nenhuma quadra encontrada');
  }
  
  await browser.close();
})();
