const Database = require('better-sqlite3');
const db = new Database('app.db', { verbose: console.log });
db.pragma('journal_mode = WAL');

const sm = db.prepare('SELECT id FROM surat_masuk').all();
console.log('Surat Masuk IDs:', sm);

const maxId = sm.length > 0 ? Math.max(...sm.map(s => s.id)) : 0;
console.log('Max ID:', maxId);
