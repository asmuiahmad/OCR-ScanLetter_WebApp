const Database = require('better-sqlite3');
const db = new Database('instance/app.db');
const tables = db.prepare("SELECT name FROM sqlite_master WHERE type='table'").all();
console.log('Tables:', tables);

try {
  const sm = db.prepare('SELECT count(*) as count FROM surat_masuk').get();
  console.log('Count surat_masuk:', sm.count);
} catch (e) {
  console.log('Error surat_masuk:', e.message);
}
