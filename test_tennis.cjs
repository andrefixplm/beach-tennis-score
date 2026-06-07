const { chromium } = require('playwright');
(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  await page.setViewportSize({ width: 390, height: 844 });
  const errors = [];
  page.on('pageerror', e => errors.push('PAGE: ' + e.message));
  page.on('console', msg => { if (msg.type() === 'error') errors.push('CON: ' + msg.text()); });
  
  try {
    await page.goto('http://127.0.0.1:5175/', { waitUntil: 'domcontentloaded', timeout: 20000 });
    await page.waitForTimeout(2500);
    
    // 1. Login
    await page.locator('input[placeholder="Usuário"]').fill('admin');
    await page.locator('input[placeholder="Senha"]').fill('tennis123');
    await page.locator('.btn-login').click();
    await page.waitForTimeout(1500);
    
    // 2. Setup screen
    const setupVisible = await page.locator('.setup-form').isVisible().catch(() => false);
    console.log('1. Setup form:', setupVisible ? 'OK' : 'FAIL');
    
    // Select "Melhor de 5" (3 sets)
    const toggles = await page.locator('.toggle-btn').all();
    for (const t of toggles) {
      const text = await t.textContent();
      if (text.includes('Melhor de 5')) { await t.click(); break; }
    }
    await page.waitForTimeout(300);
    
    // Start match
    await page.locator('.btn-start-match').click();
    await page.waitForTimeout(1500);
    
    // 3. Home screen
    const homeVisible = await page.locator('.home-screen').isVisible().catch(() => false);
    console.log('2. Home screen:', homeVisible ? 'OK' : 'FAIL');
    
    // 4. Add player - use the first "+" button specifically in the players section
    await page.getByPlaceholder('Nome do jogador').fill('Rafael');
    await page.locator('.add-player-form .btn-primary').click();
    await page.waitForTimeout(500);
    
    const players = await page.locator('.player-chip').count();
    console.log('3. Players added:', players > 0 ? `OK (${players})` : 'FAIL');
    
    // 5. Add second player
    await page.getByPlaceholder('Nome do jogador').fill('André');
    await page.locator('.add-player-form .btn-primary').click();
    await page.waitForTimeout(500);
    
    const players2 = await page.locator('.player-chip').count();
    console.log('4. Second player:', players2 >= 2 ? `OK (${players2})` : 'FAIL');
    
    // 6. Add a court
    await page.locator('button:has-text("+ Quadra")').click();
    await page.waitForTimeout(500);
    
    // Handle the prompt dialog
    page.once('dialog', async dialog => {
      await dialog.accept('Quadra Central');
    });
    await page.locator('button:has-text("+ Quadra")').click();
    await page.waitForTimeout(800);
    
    const courtCards = await page.locator('.court-card').count();
    console.log('5. Court cards:', courtCards > 0 ? `OK (${courtCards})` : 'FAIL');
    
    if (courtCards > 0) {
      await page.locator('.court-card').first().click();
      await page.waitForTimeout(1000);
      
      const courtScreenVisible = await page.locator('.court-screen').isVisible().catch(() => false);
      console.log('6. Court screen:', courtScreenVisible ? 'OK' : 'FAIL');
      
      // 7. Match card
      const matchCards = await page.locator('.match-card').count();
      console.log('7. Match cards:', matchCards > 0 ? `OK (${matchCards})` : 'FAIL');
    }
    
    console.log('\nConsole errors:', errors.length > 0 ? errors.join('\n') : 'none');
    
  } catch (e) {
    console.log('Error:', e.message);
  }
  
  await browser.close();
})();