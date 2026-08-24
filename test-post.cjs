const http = require('http');

const options = {
  hostname: 'localhost',
  port: 3000,
  path: '/surat-masuk/input',
  method: 'POST',
  headers: {
    'Content-Type': 'application/x-www-form-urlencoded',
    'Cookie': 'connect.sid=fake_session_here' // We might need a real session, but let's see if it redirects or hangs
  }
};

const req = http.request(options, (res) => {
  console.log(`STATUS: ${res.statusCode}`);
  res.on('data', (chunk) => {
    console.log(`BODY: ${chunk.length} bytes`);
  });
  res.on('end', () => {
    console.log('No more data in response.');
  });
});

req.on('error', (e) => {
  console.error(`problem with request: ${e.message}`);
});

req.write('tanggal=2026-08-24&nomor=123&pengirim=Test&penerima=Test&isi=Test');
req.end();
