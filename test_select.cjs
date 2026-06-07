const { chromium } = require('playwright');

(async () => {
  const browser = await chromium.launch({ headless: true });
  const page = await browser.newPage();
  
  // Capture all API calls
  const apiCalls = [];
  page.on('request', req => {
    if (req.url().includes('100.118.169.20:8002/api')) {
      apiCalls.push({ method: req.method(), url: req.url(), body: req.postData() });
    }
  });
  page.on('response', res => {
    if (res.url().includes('100.118.169.20:8002/api')) {
      apiCalls.push({ status: res.status(), url: res.url(), response: 'RESPONSE' });
    }
  });
  
  console.log('Opening app...');
  await page.goto('http://100.118.169.20:5175');
  await page.waitForTimeout(1000);
  
  // Login
  console.log('Logging in...');
  await page.fill('input[placeholder="Usuário"]', 'admin');
  await page.fill('input[placeholder="Senha"]', 'tennis123');
  await page.click('button[type="submit"]');
  await page.waitForTimeout(2000);
  
  // Check we're on home screen
  const title = await page.textContent('h1');
  console.log('Title:', title);
  
  // Add a player if needed
  const playerInput = await page.$('input[placeholder="Nome do jogador"]');
  if (playerInput) {
    await playerInput.fill('Test Player');
    await page.click('button.btn-primary');
    await page.waitForTimeout(1000);
  }
  
  // Create a court
  const addCourtBtn = await page.$('button:has-text("+ Quadra")');
  if (addCourtBtn) {
    await addCourtBtn.click();
    await page.waitForTimeout(500);
    // Handle prompt
    await page.evaluate(() => {
      // Override window.prompt to return a value
      const original = window.prompt;
      window.prompt = () => 'Test Court';
    });
    await addCourtBtn.click();
    await page.waitForTimeout(1000);
  }
  
  // Click on first court
  const courtCard = await page.$('.court-card');
  if (courtCard) {
    await courtCard.click();
    await page.waitForTimeout(2000);
    console.log('On court screen');
    
    // Add a new match
    const addMatchBtn = await page.$('button:has-text("+ Nova Partida")');
    if (addMatchBtn) {
      await addMatchBtn.click();
      await page.waitForTimeout(1000);
      console.log('Match added');
    }
    
    // Check for player selects
    const selects = await page.$$('.player-select');
    console.log('Player selects found:', selects.length);
    
    if (selects.length > 0) {
      // Get options before selecting
      const optionsBefore = await selects[0].evaluate(el => {
        return Array.from(el.options).map(o => ({ value: o.value, text: o.text }));
      });
      console.log('Options before:', optionsBefore);
      
      // Select first player option (not the empty one)
      const optionCount = await selects[0].evaluate(el => el.options.length);
      if (optionCount > 1) {
        await selects[0].selectOption({ index: 1 });
        await page.waitForTimeout(1000);
        
        // Check selected value
        const selectedValue = await selects[0].evaluate(el => el.value);
        console.log('Selected value after:', selectedValue);
        
        // Check what was captured in API calls
        console.log('\nAPI Calls:');
        apiCalls.forEach((call, i) => {
          if (call.method) console.log(`${i}: ${call.method} ${call.url} - ${call.body}`);
          if (call.status) console.log(`${i}: RESPONSE ${call.status} ${call.url}`);
        });
      }
    }
  }
  
  await browser.close();
  console.log('\nTest complete');
})().catch(e => console.error('Error:', e.message));