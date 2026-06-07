const http = require('http');

function apiRequest(method, path, body, token) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '100.118.169.20',
      port: 8002,
      path: path,
      method: method,
      headers: { 
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${token}`
      }
    };
    const req = http.request(options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => {
        try { resolve({ status: res.statusCode, body: JSON.parse(data) }); }
        catch { resolve({ status: res.statusCode, body: data }); }
      });
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

(async () => {
  // Login
  const loginRes = await apiRequest('POST', '/api/auth/login', { username: 'admin', password: 'tennis123' });
  const token = loginRes.body.token;
  console.log('Login OK, token:', token.substring(0, 20) + '...');
  
  // Criar nova partida (singles) na primeira quadra
  const courtsRes = await apiRequest('GET', '/api/courts', null, token);
  const courtId = courtsRes.body[0].id;
  console.log('Court ID:', courtId);
  
  const createRes = await apiRequest('POST', `/api/courts/${courtId}/matches`, {
    mode: 'singles',
    sets_to_win: 1,
    games_per_set: 4,
    tiebreak_at: 7,
    tiebreak_win_by: 2
  }, token);
  console.log('Create match:', createRes.status, createRes.body.id);
  const matchId = createRes.body.id;
  
  // Players
  const playersRes = await apiRequest('GET', '/api/players', null, token);
  const p1 = playersRes.body[0];
  const p2 = playersRes.body[1];
  console.log('Players:', p1.name, p2.name);
  
  // Update players via PATCH
  console.log('\nFazendo PATCH para atualizar players...');
  const patchRes = await apiRequest('PATCH', `/api/matches/${matchId}/players`, {
    player1_id: p1.id,
    player2_id: p2.id
  }, token);
  console.log('PATCH status:', patchRes.status);
  console.log('PATCH response player1:', patchRes.body.player1);
  console.log('PATCH response player1.id:', patchRes.body.player1?.id);
  
  // Agora verificar GET para ver se persistiu
  const getRes = await apiRequest('GET', `/api/courts/${courtId}/matches`, null, token);
  console.log('\nGET matches count:', getRes.body.length);
  const updatedMatch = getRes.body.find(m => m.id === matchId);
  console.log('Match player1:', updatedMatch?.player1);
  
  await apiRequest('DELETE', `/api/courts/${courtId}/matches/${matchId}`, null, token);
  console.log('Cleaned up match');
})();
