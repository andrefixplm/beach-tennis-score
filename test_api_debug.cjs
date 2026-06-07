const http = require('http');

function request(method, path, body) {
  return new Promise((resolve, reject) => {
    const options = {
      hostname: '100.118.169.20',
      port: 8002,
      path: path,
      method: method,
      headers: { 'Content-Type': 'application/json' }
    };
    const req = http.request(options, res => {
      let data = '';
      res.on('data', chunk => data += chunk);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    if (body) req.write(JSON.stringify(body));
    req.end();
  });
}

(async () => {
  // Login
  const loginRes = await request('POST', '/api/auth/login', { username: 'admin', password: 'tennis123' });
  console.log('Login:', loginRes.status, loginRes.body);
  const token = loginRes.body.token;
  
  // Headers com token
  const authHeaders = { 'Authorization': `Bearer ${token}`, 'Content-Type': 'application/json' };
  
  // Listar jogadores
  const playersRes = await new Promise((resolve, reject) => {
    const req = http.request({ hostname: '100.118.169.20', port: 8002, path: '/api/players', method: 'GET', headers: authHeaders }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    req.end();
  });
  console.log('\nPlayers:', playersRes.status, playersRes.body.length);
  console.log('Primeiro jogador:', JSON.stringify(playersRes.body[0]));
  
  // Listar quadras
  const courtsRes = await new Promise((resolve, reject) => {
    const req = http.request({ hostname: '100.118.169.20', port: 8002, path: '/api/courts', method: 'GET', headers: authHeaders }, res => {
      let data = '';
      res.on('data', c => data += c);
      res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
    });
    req.on('error', reject);
    req.end();
  });
  console.log('\nCourts:', courtsRes.status, courtsRes.body.length);
  
  if (courtsRes.body.length > 0) {
    const courtId = courtsRes.body[0].id;
    console.log('Primeira quadra:', courtId, courtsRes.body[0].name);
    
    // Listar matches da quadra
    const matchesRes = await new Promise((resolve, reject) => {
      const req = http.request({ hostname: '100.118.169.20', port: 8002, path: `/api/courts/${courtId}/matches`, method: 'GET', headers: authHeaders }, res => {
        let data = '';
        res.on('data', c => data += c);
        res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
      });
      req.on('error', reject);
      req.end();
    });
    console.log('\nMatches:', matchesRes.status, matchesRes.body.length);
    
    if (matchesRes.body.length > 0) {
      const match = matchesRes.body[0];
      console.log('Match:', match.id, 'player1:', match.player1, 'player2:', match.player2);
      
      // Atualizar jogadores
      const p1Id = playersRes.body[0]?.id;
      const p2Id = playersRes.body[1]?.id;
      
      if (p1Id && p2Id) {
        console.log('\nAtualizando players:', p1Id, p2Id);
        
        const updateRes = await new Promise((resolve, reject) => {
          const req = http.request({ hostname: '100.118.169.20', port: 8002, path: `/api/matches/${match.id}/players`, method: 'PATCH', headers: authHeaders }, res => {
            let data = '';
            res.on('data', c => data += c);
            res.on('end', () => resolve({ status: res.statusCode, body: JSON.parse(data) }));
          });
          req.on('error', reject);
          req.write(JSON.stringify({ player1_id: p1Id, player2_id: p2Id }));
          req.end();
        });
        console.log('Update response:', updateRes.status, JSON.stringify(updateRes.body));
      }
    }
  }
})();
