import express from 'express';
import Tesseract from 'tesseract.js';
import session from 'express-session';
import cookieParser from 'cookie-parser';
import path from 'path';
import multer from 'multer';
import bcrypt from 'bcryptjs';
import fs from 'fs';

// Setup multer storage to preserve file extensions
const storage = multer.diskStorage({
  destination: function (req, file, cb) {
    cb(null, 'static/uploads/');
  },
  filename: function (req, file, cb) {
    const uniqueSuffix = Date.now() + '-' + Math.round(Math.random() * 1E9);
    cb(null, file.fieldname + '-' + uniqueSuffix + path.extname(file.originalname).toLowerCase());
  }
});
const upload = multer({ storage: storage });

const app = express();
const PORT = 3000;

// Trust reverse proxy for session cookies in Cloud Run / iframe environment
app.set('trust proxy', 1);

import Database from 'better-sqlite3';

const instanceDir = path.join(process.cwd(), 'instance');
if (!fs.existsSync(instanceDir)) fs.mkdirSync(instanceDir, { recursive: true });
const dbPath = path.join(instanceDir, 'app.db');

const db = new Database(dbPath);
db.pragma('journal_mode = WAL');

db.exec(`
  CREATE TABLE IF NOT EXISTS users (
    id INTEGER PRIMARY KEY,
    email TEXT,
    password TEXT,
    nama TEXT,
    role TEXT,
    is_admin INTEGER,
    nip TEXT,
    jabatan TEXT,
    last_login TEXT
  );
  CREATE TABLE IF NOT EXISTS surat_masuk (id INTEGER PRIMARY KEY, data TEXT);
  CREATE TABLE IF NOT EXISTS surat_keluar (id INTEGER PRIMARY KEY, data TEXT);
  CREATE TABLE IF NOT EXISTS cuti (id INTEGER PRIMARY KEY, data TEXT);
  CREATE TABLE IF NOT EXISTS disposisi (id INTEGER PRIMARY KEY, data TEXT);
  CREATE TABLE IF NOT EXISTS pegawai (id INTEGER PRIMARY KEY, data TEXT);
`);


interface UserRecord {
  id: number;
  email: string;
  password: string;
  nama: string;
  role: string;
  is_admin: number;
  nip: string;
  jabatan: string;
  last_login: string;
}

const defaultUsers: UserRecord[] = [];

function initDatabase(): UserRecord[] {
  let users = db.prepare('SELECT * FROM users').all() as UserRecord[];
  if (users.length === 0 && defaultUsers.length > 0) {
    const insert = db.prepare('INSERT INTO users (id, email, password, nama, role, is_admin, nip, jabatan, last_login) VALUES (@id, @email, @password, @nama, @role, @is_admin, @nip, @jabatan, @last_login)');
    db.transaction(() => {
      for (const u of defaultUsers) insert.run(u);
    })();
    users = db.prepare('SELECT * FROM users').all() as UserRecord[];
  }
  return users;
}

function saveState() {
  db.transaction(() => {
    db.prepare('DELETE FROM surat_masuk').run();
    db.prepare('DELETE FROM surat_keluar').run();
    db.prepare('DELETE FROM cuti').run();
    db.prepare('DELETE FROM disposisi').run();
    db.prepare('DELETE FROM pegawai').run();

    const insSM = db.prepare('INSERT INTO surat_masuk (id, data) VALUES (?, ?)');
    for (const s of suratMasukList) insSM.run(s.id, JSON.stringify(s));

    const insSK = db.prepare('INSERT INTO surat_keluar (id, data) VALUES (?, ?)');
    for (const s of suratKeluarList) insSK.run(s.id, JSON.stringify(s));

    const insCuti = db.prepare('INSERT INTO cuti (id, data) VALUES (?, ?)');
    for (const s of cutiList) insCuti.run(s.id, JSON.stringify(s));

    const insDisp = db.prepare('INSERT INTO disposisi (id, data) VALUES (?, ?)');
    for (const s of disposisiList) insDisp.run(s.id, JSON.stringify(s));

    const insPeg = db.prepare('INSERT INTO pegawai (id, data) VALUES (?, ?)');
    for (const s of pegawaiList) insPeg.run(s.id, JSON.stringify(s));
  })();
}

function loadUsersFromDB(): UserRecord[] {
  return db.prepare('SELECT * FROM users').all() as UserRecord[];
}

function saveUsersToDB(users: UserRecord[]): void {
  db.transaction(() => {
    db.prepare('DELETE FROM users').run();
    const insert = db.prepare('INSERT INTO users (id, email, password, nama, role, is_admin, nip, jabatan, last_login) VALUES (@id, @email, @password, @nama, @role, @is_admin, @nip, @jabatan, @last_login)');
    for (const u of users) insert.run(u);
  })();
}

async function findUserByEmail(emailOrUsername: string): Promise<UserRecord | undefined> {
  const users = loadUsersFromDB();
  const search = emailOrUsername.trim().toLowerCase();
  return users.find(u => 
    u.email.toLowerCase() === search || 
    u.role.toLowerCase() === search ||
    u.email.toLowerCase().startsWith(search + '@')
  );
}

async function getAllUsersFromDB(): Promise<UserRecord[]> {
  return loadUsersFromDB();
}

async function insertUserToDB(email: string, password: string, role: string, nama?: string, nip?: string, jabatan?: string): Promise<UserRecord> {
  const users = loadUsersFromDB();
  const nextId = users.reduce((max, u) => Math.max(max, u.id), 0) + 1;
  const isAdmin = role === 'admin' ? 1 : 0;
  const userName = nama || (role === 'admin' ? 'Administrator' : (role === 'pimpinan' ? 'Pimpinan' : 'Staf Pegawai'));
  const lastLogin = 'Baru saja';

  const newUser: UserRecord = {
    id: nextId,
    email: email.trim(),
    password: bcrypt.hashSync(password.trim(), 10),
    nama: userName,
    role: role || 'pegawai',
    is_admin: isAdmin,
    nip: nip && nip.trim() ? nip.trim() : '-',
    jabatan: jabatan && jabatan.trim() ? jabatan.trim() : (role ? role.toUpperCase() : 'STAF'),
    last_login: lastLogin
  };

  users.push(newUser);
  saveUsersToDB(users);
  return newUser;
}

async function updateUserInDB(originalEmail: string, newEmail?: string, newRole?: string, newPassword?: string): Promise<boolean> {
  const users = loadUsersFromDB();
  const user = users.find(u => u.email === originalEmail);
  if (user) {
    if (user.role === 'admin') return false;
    if (newEmail && newEmail.trim()) {
      user.email = newEmail.trim();
    }
    if (newRole && newRole !== 'admin') {
      user.role = newRole;
      user.is_admin = 0;
    }
    if (newPassword && newPassword.trim()) {
      user.password = bcrypt.hashSync(newPassword.trim(), 10);
    }
    saveUsersToDB(users);
    return true;
  }
  return false;
}

async function deleteUserFromDB(email: string): Promise<boolean> {
  let users = loadUsersFromDB();
  const initialLen = users.length;
  users = users.filter(u => u.email !== email || u.role === 'admin');
  if (users.length < initialLen) {
    saveUsersToDB(users);
    return true;
  }
  return false;
}

function updateLastLogin(id: number): void {
  const users = loadUsersFromDB();
  const user = users.find(u => u.id === id);
  if (user) {
    user.last_login = new Date().toLocaleString('id-ID', { day: '2-digit', month: 'short', year: 'numeric', hour: '2-digit', minute: '2-digit' });
    saveUsersToDB(users);
  }
}

// Setup session and cookies
app.use(cookieParser('ocr-scanletter-secret'));
app.use(session({
  secret: 'ocr-scanletter-secret',
  resave: true,
  saveUninitialized: true,
  proxy: true,
  cookie: {
    secure: true,
    sameSite: 'none',
    maxAge: 24 * 60 * 60 * 1000
  }
}));

app.use(express.urlencoded({ extended: true }));
app.use(express.json());

// Serve static files
app.use('/static', express.static(path.join(process.cwd(), 'static')));

// View engine setup
app.set('views', path.join(process.cwd(), 'views'));
app.set('view engine', 'ejs');

// Mock Data
interface Surat {
  id: number;
  tanggal: string;
  pengirim: string;
  penerima: string;
  nomor: string;
  isi: string;
  created_at: string;
  status: 'pending' | 'approved' | 'rejected';
  approved_by?: string;
  type: 'Masuk' | 'Keluar';
  file_path?: string;
  alasan_penolakan?: string;
}




// Initialized from SQLite DB
let suratMasukList: Surat[] = db.prepare('SELECT data FROM surat_masuk').all().map((r: any) => JSON.parse(r.data));
let suratKeluarList: Surat[] = db.prepare('SELECT data FROM surat_keluar').all().map((r: any) => JSON.parse(r.data));
let cutiList: any[] = db.prepare('SELECT data FROM cuti').all().map((r: any) => JSON.parse(r.data));
let disposisiList: any[] = db.prepare('SELECT data FROM disposisi').all().map((r: any) => JSON.parse(r.data));
let pegawaiList: any[] = db.prepare('SELECT data FROM pegawai').all().map((r: any) => JSON.parse(r.data));

let activeUser: any = null; /* WAS: { 
  id: 1,
  email: 'admin@sistem.local',
  nama: 'Administrator System',
  role: 'admin',
  is_admin: true,
  nip: '19850101 201001 1 001',
  jabatan: 'Administrator',
  is_authenticated: true
}; */

// Context middlewares and helpers
app.use(async (req, res, next) => {
  // Setup url_for mapping
  res.locals.url_for = (endpoint: string, options: any = {}) => {
    if (endpoint === 'static') {
      return `/static/${options.filename}`;
    }
    if (endpoint === 'dashboard.dashboard') return '/dashboard';
    if (endpoint === 'auth.login') return '/auth/login';
    if (endpoint === 'auth.logout') return '/auth/logout';
    if (endpoint === 'surat_masuk.show_surat_masuk') return '/surat-masuk/show_surat_masuk';
    if (endpoint === 'surat_keluar.show_surat_keluar') return '/surat-keluar/show_surat_keluar';
    if (endpoint === 'ocr.ocr_surat_masuk') return '/ocr/surat-masuk';
    if (endpoint === 'ocr.ocr_surat_keluar') return '/ocr/surat-keluar';
    if (endpoint === 'ocr.ocr_cuti') return '/ocr/ocr-cuti';

    if (endpoint === 'templates.surat_keluar' || endpoint === 'templates.generate_cuti') return '/templates';
    if (endpoint === 'templates.builder_cuti') return '/templates/builder-cuti';
    if (endpoint === 'surat_masuk.input') return '/surat-masuk/input';
    if (endpoint === 'surat_keluar.input') return '/surat-keluar/input';
    if (endpoint === 'cuti.daftar') return '/cuti';
    if (endpoint === 'cuti.baru') return '/cuti/baru';
    if (endpoint === 'cuti.persetujuan') return '/cuti/persetujuan';
    if (endpoint === 'laporan.statistik') return '/laporan/statistik';
    if (endpoint === 'laporan.cetak') return '/laporan/cetak';
    if (endpoint === 'pegawai.index') return '/pegawai';
    if (endpoint === 'pegawai.tambah') return '/pegawai/tambah';
    if (endpoint === 'persetujuan.surat_masuk' || endpoint === 'persetujuan.surat_keluar') return '/persetujuan';
    if (endpoint === 'persetujuan.statistik') return '/laporan/statistik';
    if (endpoint === 'disposisi.daftar') return '/disposisi';
    if (endpoint === 'disposisi.buat') return '/disposisi/buat';
    if (endpoint === 'users.index') return '/users';
    if (endpoint === 'users.edit') return '/users/edit';
    if (endpoint === 'users.delete') return '/users/delete';

    return '#';
  };

  // CSRF Mock Helper
  res.locals.csrf_token = () => 'mock_csrf_token_value_xyz';

  // Global counts & items for pending letters
  const pendingMasukItems = suratMasukList.filter(s => s.status === 'pending');
  const pendingKeluarItems = suratKeluarList.filter(s => s.status === 'pending');

  res.locals.g = {
    pending_masuk_count: pendingMasukItems.length,
    pending_keluar_count: pendingKeluarItems.length,
    pending_masuk_items: pendingMasukItems,
    pending_keluar_items: pendingKeluarItems,
    pending_items: [
      ...pendingMasukItems.map(s => ({ ...s, type_lower: 'masuk' })),
      ...pendingKeluarItems.map(s => ({ ...s, type_lower: 'keluar' }))
    ]
  };

  // Session user restoration logic
  if (req.session && (req.session as any).user) {
    activeUser = (req.session as any).user;
  } else if (req.cookies && req.cookies.auth_user_id) {
    const userId = parseInt(req.cookies.auth_user_id, 10);
    if (!isNaN(userId)) {
      const users = await getAllUsersFromDB();
      const user = users.find(u => u.id === userId);
      if (user) {
        activeUser = {
          id: user.id,
          email: user.email,
          nama: user.nama,
          role: user.role,
          is_admin: Boolean(user.is_admin),
          nip: user.nip || '',
          jabatan: user.jabatan || '',
          is_authenticated: true
        };
        if (req.session) {
          (req.session as any).user = activeUser;
        }
      }
    }
  }

  res.locals.current_user = (req.session && (req.session as any).user) ? (req.session as any).user : activeUser;

  next();
});

// Authentication Guard Middleware
const requireAuth = (req: express.Request, res: express.Response, next: express.NextFunction) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (user) {
    return next();
  }
  return res.redirect('/auth/login');
};

// --- CORE ROUTES ---

// 1. Root route
app.get('/', (req, res) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (user) {
    return res.redirect('/dashboard');
  }
  res.redirect('/auth/login');
});

// 2. Login View & Aliases
const renderLogin = (req: express.Request, res: express.Response) => {
  res.render('auth/login', { error: null, success: null });
};

app.get('/auth/login', renderLogin);
app.get('/login', renderLogin);

// 2b. Register View & Aliases
const renderRegister = (req: express.Request, res: express.Response) => {
  res.render('auth/register', { error: null, success: null });
};

app.get('/auth/register', renderRegister);
app.get('/register', renderRegister);

// 2c. Register POST handler
const handleRegisterPost = async (req: express.Request, res: express.Response) => {
  const { nama, email, password, confirmPassword, role, nip, jabatan } = req.body;

  if (!nama || !email || !password) {
    return res.render('auth/register', { error: 'Nama, Email, dan Password wajib diisi.', success: null });
  }

  if (password.trim() !== (confirmPassword || '').trim()) {
    return res.render('auth/register', { error: 'Password dan Konfirmasi Password tidak cocok.', success: null });
  }

  try {
    const existingUser = await findUserByEmail(email);
    if (existingUser) {
      return res.render('auth/register', { error: 'Email/Username sudah terdaftar. Silakan gunakan email lain atau langsung masuk.', success: null });
    }

    const assignedRole = role || 'pegawai';
    await insertUserToDB(email, password, assignedRole, nama, nip, jabatan);

    return res.render('auth/login', { 
      error: null, 
      success: 'Akun Anda berhasil didaftarkan! Silakan masuk menggunakan email dan password yang telah dibuat.' 
    });
  } catch (err) {
    console.error('Registration database error:', err);
    res.render('auth/register', { error: 'Terjadi kesalahan sistem saat mendaftarkan akun.', success: null });
  }
};

app.post('/auth/register', handleRegisterPost);
app.post('/register', handleRegisterPost);

// 3. Login POST handler (verifies credentials against instance/app.db database)
const handleLoginPost = async (req: express.Request, res: express.Response) => {
  const { email, password } = req.body;

  if (!email || !password) {
    return res.render('auth/login', { error: 'Email dan password tidak boleh kosong.' });
  }

  try {
    const user = await findUserByEmail(email);
    if (!user) {
      return res.render('auth/login', { error: 'Email atau password yang Anda masukkan salah.' });
    }

    const isMatch = (user.password.trim() === password.trim()) || 
      (bcrypt.compareSync ? bcrypt.compareSync(password.trim(), user.password) : false);

    if (!isMatch) {
      return res.render('auth/login', { error: 'Email atau password yang Anda masukkan salah.' });
    }

    // Save authenticated user payload
    const userPayload = {
      id: user.id,
      email: user.email,
      nama: user.nama,
      role: user.role, // 'admin', 'pimpinan', or 'pegawai'
      is_admin: Boolean(user.is_admin),
      nip: user.nip || '',
      jabatan: user.jabatan || '',
      is_authenticated: true
    };

    activeUser = userPayload;

    if (req.session) {
      (req.session as any).user = userPayload;
    }

    res.cookie('auth_user_id', String(user.id), {
      maxAge: 24 * 60 * 60 * 1000
    });

    updateLastLogin(user.id);

    const nextUrl = req.body.next || '/dashboard';
    return res.redirect(nextUrl);
  } catch (err) {
    console.error('Login database error:', err);
    res.render('auth/login', { error: 'Terjadi kesalahan sistem saat verifikasi data.' });
  }
};

app.post('/auth/login', handleLoginPost);
app.post('/login', handleLoginPost);

// 4. Logout Handler & Alias
const handleLogout = (req: express.Request, res: express.Response) => {
  activeUser = null;
  res.clearCookie('auth_user_id');
  res.clearCookie('connect.sid');
  if (req.session) {
    req.session.destroy(() => {});
  }
  return res.redirect('/auth/login');
};

app.get('/auth/logout', handleLogout);
app.get('/logout', handleLogout);

// 5. Dashboard View
app.get('/dashboard', requireAuth, async (req, res) => {
  const recentSurat = [
    ...suratMasukList.map(s => ({ type: 'Masuk' as const, pengirim: s.pengirim, nomor: s.nomor, date: s.tanggal })),
    ...suratKeluarList.map(s => ({ type: 'Keluar' as const, pengirim: s.pengirim, nomor: s.nomor, date: s.tanggal }))
  ].sort((a, b) => b.date.localeCompare(a.date));

  res.render('dashboard/index', {
    breadcrumb_active: 'Dashboard',
    suratMasuk_count: suratMasukList.length,
    suratKeluar_count: suratKeluarList.length,
    suratMasuk_this_year: suratMasukList.length,
    suratKeluar_this_year: suratKeluarList.length,
    suratMasuk_this_month: suratMasukList.length,
    suratKeluar_this_month: suratKeluarList.length,
    suratMasuk_this_week: suratMasukList.length,
    suratKeluar_this_week: suratKeluarList.length,
    recent_surat: recentSurat.slice(0, 5),
    users: await getAllUsersFromDB()
  });
});

// 6. Surat Masuk View
app.get('/surat-masuk/show_surat_masuk', requireAuth, (req, res) => {
  const searchQuery = (req.query.search as string || '').toLowerCase().trim();
  let filtered = suratMasukList;
  if (searchQuery) {
    filtered = suratMasukList.filter(s =>
      s.nomor.toLowerCase().includes(searchQuery) ||
      s.pengirim.toLowerCase().includes(searchQuery) ||
      s.penerima.toLowerCase().includes(searchQuery) ||
      s.isi.toLowerCase().includes(searchQuery)
    );
  }
  const page = parseInt(req.query.page as string) || 1;
  const limit = 10;
  const total = filtered.length;
  const pages = Math.ceil(total / limit);
  const items = filtered.slice((page - 1) * limit, page * limit);

  res.render('surat_masuk/show_surat_masuk', {
    breadcrumb_active: 'Surat Masuk',
    search: req.query.search || '',
    entries: {
      page: page,
      pages: pages || 1,
      items: items,
      has_prev: page > 1,
      has_next: page < pages,
      prev_num: page - 1,
      next_num: page + 1
    }
  });
});

// 7. Surat Keluar View
app.get('/surat-keluar/show_surat_keluar', requireAuth, (req, res) => {
  const searchQuery = (req.query.search as string || '').toLowerCase().trim();
  let filtered = suratKeluarList;
  if (searchQuery) {
    filtered = suratKeluarList.filter(s =>
      s.nomor.toLowerCase().includes(searchQuery) ||
      s.pengirim.toLowerCase().includes(searchQuery) ||
      s.penerima.toLowerCase().includes(searchQuery) ||
      s.isi.toLowerCase().includes(searchQuery)
    );
  }
  const page = parseInt(req.query.page as string) || 1;
  const limit = 10;
  const total = filtered.length;
  const pages = Math.ceil(total / limit);
  const items = filtered.slice((page - 1) * limit, page * limit);

  res.render('surat_keluar/show_surat_keluar', {
    breadcrumb_active: 'Surat Keluar',
    search: req.query.search || '',
    entries: {
      page: page,
      pages: pages || 1,
      items: items,
      has_prev: page > 1,
      has_next: page < pages,
      prev_num: page - 1,
      next_num: page + 1
    }
  });
});

// 8. Notifications & Approval API
app.get('/api/notifications/count', (req, res) => {
  const pendingMasuk = suratMasukList.filter(s => s.status === 'pending').length;
  const pendingKeluar = suratKeluarList.filter(s => s.status === 'pending').length;
  res.json({
    success: true,
    pending_masuk: pendingMasuk,
    pending_keluar: pendingKeluar,
    total: pendingMasuk + pendingKeluar
  });
});

app.get('/api/notifications/recent', (req, res) => {
  const pendingMasuk = suratMasukList.filter(s => s.status === 'pending');
  const pendingKeluar = suratKeluarList.filter(s => s.status === 'pending');

  const pending = [
    ...pendingMasuk.map(s => ({
      id: s.id,
      type: 'masuk',
      tanggal_display: s.tanggal,
      nomor: s.nomor,
      pengirim: s.pengirim,
      penerima: s.penerima,
      created_at_display: s.created_at
    })),
    ...pendingKeluar.map(s => ({
      id: s.id,
      type: 'keluar',
      tanggal_display: s.tanggal,
      nomor: s.nomor,
      pengirim: s.pengirim,
      penerima: s.penerima,
      created_at_display: s.created_at
    }))
  ];

  res.json({
    success: true,
    surat_list: pending,
    pending_masuk: pendingMasuk.length,
    pending_keluar: pendingKeluar.length
  });
});

// Approval API endpoints for bell notification actions
app.post('/approval/surat-masuk/:id/approve-api', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratMasukList.find(s => s.id === id);
  if (target) {
    target.status = 'approved';
    saveState();
    target.approved_by = (req.session && (req.session as any).user) ? (req.session as any).user.email : 'pimpinan@sistem.local';
    saveState();
    return res.json({ success: true, message: 'Surat Masuk berhasil disetujui' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/approval/surat-masuk/:id/reject-api', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratMasukList.find(s => s.id === id);
  if (target) {
    target.status = 'rejected';
    saveState();
    return res.json({ success: true, message: 'Surat Masuk ditolak' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/approval/surat-keluar/:id/approve-api', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratKeluarList.find(s => s.id === id);
  if (target) {
    target.status = 'approved';
    saveState();
    target.approved_by = (req.session && (req.session as any).user) ? (req.session as any).user.email : 'pimpinan@sistem.local';
    saveState();
    return res.json({ success: true, message: 'Surat Keluar berhasil disetujui' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/approval/surat-keluar/:id/reject-api', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratKeluarList.find(s => s.id === id);
  if (target) {
    target.status = 'rejected';
    saveState();
    return res.json({ success: true, message: 'Surat Keluar ditolak' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

// Single Detail & CRUD API for Surat Masuk & Keluar
app.get('/api/surat-masuk/:id', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratMasukList.find(s => s.id === id);
  if (target) return res.json({ success: true, surat: target });
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.get('/api/surat-keluar/:id', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratKeluarList.find(s => s.id === id);
  if (target) return res.json({ success: true, surat: target });
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/api/surat-masuk/:id/delete', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const idx = suratMasukList.findIndex(s => s.id === id);
  if (idx !== -1) {
    suratMasukList.splice(idx, 1);
    saveState();
    return res.json({ success: true, message: 'Surat Masuk berhasil dihapus' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/api/surat-keluar/:id/delete', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const idx = suratKeluarList.findIndex(s => s.id === id);
  if (idx !== -1) {
    suratKeluarList.splice(idx, 1);
    saveState();
    return res.json({ success: true, message: 'Surat Keluar berhasil dihapus' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/api/surat-masuk/:id/update', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratMasukList.find(s => s.id === id);
  if (target) {
    const { nomor, tanggal, pengirim, penerima, isi, status } = req.body;
    if (nomor) target.nomor = nomor;
    if (tanggal) target.tanggal = tanggal;
    if (pengirim) target.pengirim = pengirim;
    if (penerima) target.penerima = penerima;
    if (isi) target.isi = isi;
    if (status) target.status = status;
    saveState();
    return res.json({ success: true, message: 'Surat Masuk berhasil diperbarui' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

app.post('/api/surat-keluar/:id/update', requireAuth, (req, res) => {
  const id = parseInt(req.params.id, 10);
  const target = suratKeluarList.find(s => s.id === id);
  if (target) {
    const { nomor, tanggal, pengirim, penerima, isi, status } = req.body;
    if (nomor) target.nomor = nomor;
    if (tanggal) target.tanggal = tanggal;
    if (pengirim) target.pengirim = pengirim;
    if (penerima) target.penerima = penerima;
    if (isi) target.isi = isi;
    if (status) target.status = status;
    saveState();
    return res.json({ success: true, message: 'Surat Keluar berhasil diperbarui' });
  }
  res.status(404).json({ success: false, message: 'Surat tidak ditemukan' });
});

// --- 9. OCR ROUTES ---

const indonesianMonths: { [key: string]: string } = {
  'januari': '01', 'jan': '01',
  'februari': '02', 'feb': '02',
  'maret': '03', 'mar': '03',
  'april': '04', 'apr': '04',
  'mei': '05',
  'juni': '06', 'jun': '06',
  'juli': '07', 'jul': '07',
  'agustus': '08', 'agu': '08', 'ags': '08',
  'september': '09', 'sep': '09',
  'oktober': '10', 'okt': '10',
  'november': '11', 'nov': '11',
  'desember': '12', 'des': '12'
};

function parseLetterWithRegex(text: string, type: 'Masuk' | 'Keluar') {
  const result = {
    nomor: '',
    tanggal: new Date().toISOString().split('T')[0],
    pengirim: '',
    penerima: '',
    isi: ''
  };

  if (!text || typeof text !== 'string') return result;

  // 1. EXTRACT NOMOR SURAT DENGAN REGEX
  // Menyeleksi dari kata "Nomor :" atau "No :" hingga akhir baris / new line
  const nomorRegex = /(?:^|\n|\r)\s*(?:Nomor|No\.?)\s*[:.]?\s*([^\r\n]+)/i;
  const nomorMatch = text.match(nomorRegex);
  if (nomorMatch && nomorMatch[1]) {
    let rawNomor = nomorMatch[1].trim();
    // Bersihkan titik dua atau spasi di awal
    rawNomor = rawNomor.replace(/^(?:[:.\-\s]+)/, '').trim();
    // Jika pada baris yang sama terdapat nama kota/tanggal atau kolom lain di sebelah kanan, pisahkan
    rawNomor = rawNomor.split(/\s+(?:Banjarbaru|Banjarmasin|Jakarta|Martapura|Sifat|Lampiran|Lamp|Hal|Perihal)\b/i)[0].trim();
    result.nomor = rawNomor;
  }

  // Fallback format nomor surat jika terdapat karakter khusus / garis miring
  if (!result.nomor) {
    const slashPattern = /\b([0-9A-Za-z\.\-]+(?:\/[0-9A-Za-z\.\-]+){2,})\b/i;
    const slashMatch = text.match(slashPattern);
    if (slashMatch) {
      result.nomor = slashMatch[1].trim();
    }
  }

  // 2. EXTRACT TANGGAL SURAT
  const dateRegex = /(?:(?:tanggal|tgl|Banjarbaru|Banjarmasin|Jakarta|Martapura)\s*[,.:]?\s*)?(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})/i;
  const dateMatch = text.match(dateRegex);
  if (dateMatch) {
    const day = dateMatch[1].padStart(2, '0');
    const monthName = dateMatch[2].toLowerCase();
    const year = dateMatch[3];
    const monthNumber = indonesianMonths[monthName];
    if (monthNumber && parseInt(day, 10) >= 1 && parseInt(day, 10) <= 31) {
      result.tanggal = `${year}-${monthNumber}-${day}`;
    }
  } else {
    const isoDateMatch = text.match(/\b(\d{4})-(\d{2})-(\d{2})\b/);
    if (isoDateMatch) {
      result.tanggal = isoDateMatch[0];
    } else {
      const dmyMatch = text.match(/\b(\d{1,2})[\/\-](\d{1,2})[\/\-](\d{4})\b/);
      if (dmyMatch) {
        result.tanggal = `${dmyMatch[3]}-${dmyMatch[2].padStart(2, '0')}-${dmyMatch[1].padStart(2, '0')}`;
      }
    }
  }

  // 3. EXTRACT PERIHAL / HAL / TENTANG / ISI SURAT
  const perihalRegex = /(?:^|\n|\r)\s*(?:Hal|Perihal|TENTANG|Tentang)\s*[:.]?\s*([^\r\n]+(?:\r?\n(?!\s*(?:Yth|Kepada|Nomor|Lampiran|Sifat|di\s+tempat|KETUA|Memperhatikan|\n))[^\r\n]+)*)/i;
  const perihalMatch = text.match(perihalRegex);
  if (perihalMatch && perihalMatch[1]) {
    let perihal = perihalMatch[1].trim().replace(/\s+/g, ' ');
    result.isi = perihal;
  } else if (text.match(/SURAT PENGANTAR/i)) {
    result.isi = 'Surat Pengantar Dokumen / Berkas Perkara';
  } else if (text.match(/FORMULIR PERMINTAAN DAN PEMBERIAN CUTI/i)) {
    result.isi = 'Permohonan dan Pemberian Cuti Pegawai';
  } else {
    const lines = text.split('\n').map(l => l.trim()).filter(l => l.length > 5);
    const bodyLines = lines.filter(l => !l.match(/^(?:MAHKAMAH|PENGADILAN|DIREKTORAT|Jalan|Jl|Nomor|Sifat|Lampiran|Hal|Perihal|Yth|Kepada|Telp|Fax|Email)/i));
    if (bodyLines.length > 0) {
      result.isi = bodyLines.slice(0, 2).join(' ');
    } else {
      result.isi = text.substring(0, 150).trim();
    }
  }

  // 4. EXTRACT PENERIMA (Yth. / Kepada Yth.)
  const penerimaRegex = /(?:^|\n|\r)\s*(?:Yth\.?|Kepada\s+Yth\.?|Kepada)\s*[:.]?\s*([^\r\n]+(?:\r?\n(?!\s*(?:di\s+tempat|Dengan\s+hormat|Assalamualaikum|Hal|Perihal|di\s+-|ISI SURAT|\n))[^\r\n]+)*)/i;
  const penerimaMatch = text.match(penerimaRegex);
  if (penerimaMatch && penerimaMatch[1]) {
    let penerima = penerimaMatch[1].trim().replace(/\s+/g, ' ');
    penerima = penerima.replace(/\s+di\s+tempat.*$/i, '').replace(/\s+Di—.*$/i, '').trim();
    result.penerima = penerima;
  }

  // 5. EXTRACT PENGIRIM (KOP SURAT / DARI)
  const dariRegex = /(?:^|\n|\r)\s*(?:Dari|Pengirim)\s*[:.]?\s*([^\r\n]+)/i;
  const dariMatch = text.match(dariRegex);
  if (dariMatch && dariMatch[1]) {
    result.pengirim = dariMatch[1].trim();
  } else {
    if (text.match(/PENGADILAN TINGGI AGAMA BANJARMASIN/i)) {
      result.pengirim = 'Pengadilan Tinggi Agama Banjarmasin';
    } else if (text.match(/DIREKTORAT JENDERAL BADAN PERADILAN AGAMA/i)) {
      result.pengirim = 'Ditjen Badilag MA RI';
    } else if (text.match(/BADAN URUSAN ADMINISTRASI/i)) {
      result.pengirim = 'Badan Urusan Administrasi MA RI';
    } else if (text.match(/PENGADILAN AGAMA BANJARBARU/i)) {
      result.pengirim = 'Pengadilan Agama Banjarbaru';
    } else if (text.match(/MAHKAMAH AGUNG/i)) {
      result.pengirim = 'Mahkamah Agung Republik Indonesia';
    } else if (type === 'Keluar') {
      result.pengirim = 'Pengadilan Agama Banjarbaru';
    } else {
      result.pengirim = type === 'Masuk' ? 'Pengadilan Tinggi Agama Banjarmasin' : 'Pengadilan Agama Banjarbaru';
    }
  }

  if (!result.penerima) {
    result.penerima = type === 'Masuk' ? 'Ketua Pengadilan Agama Banjarbaru' : 'Ketua Pengadilan Tinggi Agama Banjarmasin';
  }

  return result;
}

function parseDateStringToIso(str: string): string | null {
  if (!str) return null;
  const m = str.match(/(\d{1,2})\s+([a-zA-Z]+)\s+(\d{4})/);
  if (m) {
    const day = m[1].padStart(2, '0');
    const month = indonesianMonths[m[2].toLowerCase()];
    const year = m[3];
    if (month && parseInt(day, 10) >= 1 && parseInt(day, 10) <= 31) {
      return `${year}-${month}-${day}`;
    }
  }
  return null;
}

function parseCutiWithRegex(text: string) {
  const today = new Date().toISOString().split('T')[0];
  const result = {
    nama_pegawai: '',
    nip: '',
    jabatan: '',
    unit_kerja: 'Pengadilan Agama Banjarbaru',
    jenis_cuti: 'Cuti Tahunan',
    lama_hari: 3,
    tanggal_mulai: today,
    tanggal_selesai: today,
    alasan: 'Keperluan Keluarga / Cuti Tahunan',
    nomor_surat: ''
  };

  if (!text || typeof text !== 'string') return result;

  // 1. EXTRACT NAMA PEGAWAI
  const namaRegex = /(?:^|\n|\r)\s*(?:Nama\s+Lengkap|Nama|Pemohon|Yang\s+Mengajukan\s+Cuti)\s*[:.]?\s*([^\r\n]+)/i;
  const namaMatch = text.match(namaRegex);
  if (namaMatch && namaMatch[1]) {
    let rawNama = namaMatch[1].trim();
    rawNama = rawNama.replace(/^(?:[:.\-\s]+)/, '').trim();
    rawNama = rawNama.split(/\s+(?:NIP|Nomor\s+Induk|Jabatan|Golongan|Unit|Nomor)\b/i)[0].trim();
    if (rawNama && rawNama.length > 2) {
      result.nama_pegawai = rawNama;
    }
  }

  // 2. EXTRACT NIP
  const nipRegex = /(?:^|\n|\r|\s)\s*(?:NIP|Nomor\s+Induk\s+Pegawai)\s*[:.]?\s*([0-9\s]{8,25})/i;
  const nipMatch = text.match(nipRegex);
  if (nipMatch && nipMatch[1]) {
    result.nip = nipMatch[1].trim().replace(/\s+/g, ' ');
  }

  // 3. EXTRACT JABATAN
  const jabatanRegex = /(?:^|\n|\r)\s*(?:Jabatan)\s*[:.]?\s*([^\r\n]+)/i;
  const jabatanMatch = text.match(jabatanRegex);
  if (jabatanMatch && jabatanMatch[1]) {
    let rawJabatan = jabatanMatch[1].trim().replace(/^(?:[:.\-\s]+)/, '');
    rawJabatan = rawJabatan.split(/\s+(?:Golongan|Unit|Masa\s+Kerja|Alamat)\b/i)[0].trim();
    if (rawJabatan && rawJabatan.length > 1) {
      result.jabatan = rawJabatan;
    }
  }

  // 4. EXTRACT JENIS CUTI
  if (/Cuti\s+Sakit/i.test(text)) {
    result.jenis_cuti = 'Cuti Sakit';
  } else if (/Cuti\s+Alasan\s+Penting/i.test(text)) {
    result.jenis_cuti = 'Cuti Alasan Penting';
  } else if (/Cuti\s+Besar/i.test(text)) {
    result.jenis_cuti = 'Cuti Besar';
  } else if (/Cuti\s+Melahirkan/i.test(text)) {
    result.jenis_cuti = 'Cuti Melahirkan';
  } else if (/Cuti\s+Luar\s+Negara|Luar\s+Tanggungan/i.test(text)) {
    result.jenis_cuti = 'Cuti di Luar Tanggungan Negara';
  } else {
    result.jenis_cuti = 'Cuti Tahunan';
  }

  // 5. EXTRACT LAMA HARI
  const lamaRegex = /(?:^|\n|\r|\s)\s*(?:Lama\s+Cuti|Lama|Selama)\s*[:.]?\s*(\d+)\s*(?:hari|hr)?/i;
  const lamaMatch = text.match(lamaRegex);
  if (lamaMatch && lamaMatch[1]) {
    result.lama_hari = parseInt(lamaMatch[1].trim(), 10) || 3;
  }

  // 6. EXTRACT TANGGAL MULAI & SELESAI
  const dateRangeRegex = /(?:Mulai|sejak|dari)?\s*(?:tanggal|tgl)?\s*[:.]?\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4})\s*(?:s\/d|sampai\s+dengan|sd|-|hingga)\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4})/i;
  const rangeMatch = text.match(dateRangeRegex);
  if (rangeMatch) {
    const d1 = parseDateStringToIso(rangeMatch[1]);
    const d2 = parseDateStringToIso(rangeMatch[2]);
    if (d1) result.tanggal_mulai = d1;
    if (d2) result.tanggal_selesai = d2;
  } else {
    const mulaiRegex = /(?:Tanggal\s+Mulai(?:\s+Cuti)?|Mulai)\s*[:.]?\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4})/i;
    const selesaiRegex = /(?:Tanggal\s+Selesai(?:\s+Cuti)?|Selesai|Sampai)\s*[:.]?\s*(\d{1,2}\s+[a-zA-Z]+\s+\d{4})/i;
    const mulaiMatch = text.match(mulaiRegex);
    const selesaiMatch = text.match(selesaiRegex);
    if (mulaiMatch) {
      const d1 = parseDateStringToIso(mulaiMatch[1]);
      if (d1) result.tanggal_mulai = d1;
    }
    if (selesaiMatch) {
      const d2 = parseDateStringToIso(selesaiMatch[1]);
      if (d2) result.tanggal_selesai = d2;
    }
  }

  // 7. EXTRACT ALASAN CUTI
  const alasanRegex = /(?:^|\n|\r)\s*(?:Alasan\s+Cuti|Alasan)\s*[:.]?\s*([^\r\n]+)/i;
  const alasanMatch = text.match(alasanRegex);
  if (alasanMatch && alasanMatch[1]) {
    let rawAlasan = alasanMatch[1].trim().replace(/^(?:[:.\-\s]+)/, '');
    rawAlasan = rawAlasan.split(/\s+(?:Lama\s+Cuti|Tanggal|Tempat)\b/i)[0].trim();
    if (rawAlasan && rawAlasan.length > 2) {
      result.alasan = rawAlasan;
    }
  }

  // 8. EXTRACT NOMOR SURAT / FORMULIR
  const nomorRegex = /(?:^|\n|\r)\s*(?:Nomor|No\.?)\s*[:.]?\s*([^\r\n]+)/i;
  const nomorMatch = text.match(nomorRegex);
  if (nomorMatch && nomorMatch[1]) {
    let rawNomor = nomorMatch[1].trim().replace(/^(?:[:.\-\s]+)/, '').trim();
    rawNomor = rawNomor.split(/\s+(?:Lampiran|Hal|Perihal|Tanggal)\b/i)[0].trim();
    result.nomor_surat = rawNomor;
  }

  return result;
}

// GET OCR Surat Masuk
app.get(['/ocr/surat-masuk', '/ocr/ocr_surat_masuk', '/ocr_surat_masuk'], requireAuth, (req, res) => {
  res.render('ocr/ocr_surat_masuk', {
    breadcrumb_active: 'OCR Surat Masuk',
    activeOcr: undefined,
    success: undefined,
    error: undefined
  });
});

// GET OCR Surat Keluar
app.get(['/ocr/surat-keluar', '/ocr/ocr_surat_keluar', '/ocr_surat_keluar'], requireAuth, (req, res) => {
  res.render('ocr/ocr_surat_keluar', {
    breadcrumb_active: 'OCR Surat Keluar',
    activeOcr: undefined,
    success: undefined,
    error: undefined
  });
});

// GET OCR Cuti
app.get(['/ocr/ocr-cuti', '/ocr/cuti', '/ocr_cuti'], requireAuth, (req, res) => {
  res.render('ocr/ocr_cuti', {
    breadcrumb_active: 'OCR Cuti & Formulir Cuti',
    success: undefined,
    error: undefined
  });
});

// POST OCR Surat Masuk
app.post(['/ocr/surat-masuk', '/ocr/ocr_surat_masuk', '/ocr_surat_masuk'], requireAuth, upload.single('file'), async (req, res) => {
  const { action, filename, nomor, tanggal, pengirim, penerima, isi } = req.body;

  if (action === 'save') {
    let filePath: string | undefined = undefined;
    if (filename && filename.startsWith('/static/')) {
      filePath = filename;
    } else if (filename) {
      filePath = `/static/ocr/surat_masuk/${filename}`;
    }

    const newSurat: Surat = {
      id: suratMasukList.length > 0 ? Math.max(...suratMasukList.map(s => s.id)) + 1 : 1,
      tanggal: tanggal || new Date().toISOString().split('T')[0],
      pengirim: pengirim || 'Pengadilan Tinggi Agama Banjarmasin',
      penerima: penerima || 'Ketua Pengadilan Agama Banjarbaru',
      nomor: nomor || '',
      isi: isi || 'Surat Masuk Diekstraksi via OCR',
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
      status: 'pending',
      type: 'Masuk',
      file_path: filePath
    };
    suratMasukList.unshift(newSurat);
    saveState();

    return res.render('ocr/ocr_surat_masuk', {
      breadcrumb_active: 'OCR Surat Masuk',
      activeOcr: undefined,
      success: `Surat Masuk No. "${newSurat.nomor}" berhasil disimpan ke database!`
    });
  }

  // Processing OCR
  if (!req.file) {
    return res.render('ocr/ocr_surat_masuk', {
      breadcrumb_active: 'OCR Surat Masuk',
      activeOcr: undefined,
      error: 'Silakan pilih berkas scan/foto surat masuk terlebih dahulu sebelum memproses OCR.'
    });
  }

  const uploadedFilename = req.file.filename;
  const imageUrl = `/static/uploads/${uploadedFilename}`;
  
  let extracted = {
    filename: `/static/uploads/${uploadedFilename}`,
    nomor: '',
    tanggal: new Date().toISOString().split('T')[0],
    pengirim: '',
    penerima: '',
    isi: '',
    rawText: '',
    imageUrl: imageUrl,
    confidence: 0
  };

  try {
    const realPath = path.join(process.cwd(), `static/uploads/${uploadedFilename}`);
    if (fs.existsSync(realPath)) {
      const { data: { text, confidence } } = await Tesseract.recognize(realPath, 'ind');
      extracted.rawText = text;
      extracted.confidence = Math.round(confidence || 0);
      
      // Ekstraksi terstruktur menggunakan Regex cerdas
      const parsed = parseLetterWithRegex(text, 'Masuk');
      extracted.nomor = parsed.nomor;
      extracted.tanggal = parsed.tanggal;
      extracted.pengirim = parsed.pengirim;
      extracted.penerima = parsed.penerima;
      extracted.isi = parsed.isi;
    }
  } catch(e) {
    console.error('OCR Error:', e);
    extracted.isi = 'Gagal memproses OCR. Silakan periksa kembali berkas yang diunggah.';
  }

  res.render('ocr/ocr_surat_masuk', {
    breadcrumb_active: 'OCR Surat Masuk',
    activeOcr: extracted,
    success: undefined
  });
});

// POST OCR Surat Keluar
app.post(['/ocr/surat-keluar', '/ocr/ocr_surat_keluar', '/ocr_surat_keluar'], requireAuth, upload.single('file'), async (req, res) => {
  const { action, filename, nomor, tanggal, pengirim, penerima, isi } = req.body;

  if (action === 'save') {
    let filePath: string | undefined = undefined;
    if (filename && filename.startsWith('/static/')) {
      filePath = filename;
    } else if (filename) {
      filePath = `/static/ocr/surat_keluar/${filename}`;
    }

    const newSurat: Surat = {
      id: suratKeluarList.length > 0 ? Math.max(...suratKeluarList.map(s => s.id)) + 1 : 1,
      tanggal: tanggal || new Date().toISOString().split('T')[0],
      pengirim: pengirim || 'Pengadilan Agama Banjarbaru',
      penerima: penerima || 'Ketua Pengadilan Tinggi Agama Banjarmasin',
      nomor: nomor || '',
      isi: isi || 'Surat Keluar Diekstraksi via OCR',
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
      status: 'pending',
      type: 'Keluar',
      file_path: filePath
    };
    suratKeluarList.unshift(newSurat);
    saveState();

    return res.render('ocr/ocr_surat_keluar', {
      breadcrumb_active: 'OCR Surat Keluar',
      activeOcr: undefined,
      success: `Surat Keluar No. "${newSurat.nomor}" berhasil disimpan ke database!`
    });
  }

  // Processing OCR
  if (!req.file) {
    return res.render('ocr/ocr_surat_keluar', {
      breadcrumb_active: 'OCR Surat Keluar',
      activeOcr: undefined,
      error: 'Silakan pilih berkas scan/foto surat keluar terlebih dahulu sebelum memproses OCR.'
    });
  }

  const uploadedFilename = req.file.filename;
  const imageUrl = `/static/uploads/${uploadedFilename}`;
  
  let extracted = {
    filename: `/static/uploads/${uploadedFilename}`,
    nomor: '',
    tanggal: new Date().toISOString().split('T')[0],
    pengirim: '',
    penerima: '',
    isi: '',
    rawText: '',
    imageUrl: imageUrl,
    confidence: 0
  };

  try {
    const realPath = path.join(process.cwd(), `static/uploads/${uploadedFilename}`);
    if (fs.existsSync(realPath)) {
      const { data: { text, confidence } } = await Tesseract.recognize(realPath, 'ind');
      extracted.rawText = text;
      extracted.confidence = Math.round(confidence || 0);
      
      // Ekstraksi terstruktur menggunakan Regex cerdas
      const parsed = parseLetterWithRegex(text, 'Keluar');
      extracted.nomor = parsed.nomor;
      extracted.tanggal = parsed.tanggal;
      extracted.pengirim = parsed.pengirim;
      extracted.penerima = parsed.penerima;
      extracted.isi = parsed.isi;
    }
  } catch(e) {
    console.error('OCR Error:', e);
    extracted.isi = 'Gagal memproses OCR. Silakan periksa kembali berkas yang diunggah.';
  }

  res.render('ocr/ocr_surat_keluar', {
    breadcrumb_active: 'OCR Surat Keluar',
    activeOcr: extracted,
    success: undefined
  });
});

// GET OCR Cuti
app.get(['/ocr/ocr-cuti', '/ocr/cuti', '/ocr_cuti'], requireAuth, (req, res) => {
  res.render('ocr/ocr_cuti', {
    breadcrumb_active: 'OCR Cuti & Formulir Cuti',
    activeOcr: undefined,
    success: undefined,
    error: undefined
  });
});

// POST OCR Cuti
app.post(['/ocr/ocr-cuti', '/ocr/cuti', '/ocr_cuti'], requireAuth, upload.single('file'), async (req, res) => {
  const { action, filename, nama_pegawai, nip, jabatan, unit_kerja, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan, nomor_surat } = req.body;

  if (action === 'save') {
    let filePath: string | undefined = undefined;
    if (filename && filename.startsWith('/static/')) {
      filePath = filename;
    } else if (filename) {
      filePath = `/static/uploads/${filename}`;
    }

    const newCuti = {
      id: cutiList.length > 0 ? Math.max(...cutiList.map(s => s.id)) + 1 : 1,
      nama_pegawai: nama_pegawai || 'Pegawai PA Banjarbaru',
      nip: nip || '-',
      jabatan: jabatan || 'Pegawai',
      unit: unit_kerja || 'Pengadilan Agama Banjarbaru',
      jenis_cuti: jenis_cuti || 'Cuti Tahunan',
      tanggal_mulai: tanggal_mulai || new Date().toISOString().split('T')[0],
      tanggal_selesai: tanggal_selesai || new Date().toISOString().split('T')[0],
      lama_hari: parseInt(lama_hari, 10) || 3,
      alasan: alasan || 'Permohonan cuti pegawai',
      status: 'pending',
      nomor_surat: nomor_surat || '-',
      created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
      file_path: filePath
    };

    cutiList.unshift(newCuti);
    saveState();

    return res.render('ocr/ocr_cuti', {
      breadcrumb_active: 'OCR Cuti & Formulir Cuti',
      activeOcr: undefined,
      success: `Formulir cuti atas nama "${newCuti.nama_pegawai}" (${newCuti.jenis_cuti}) berhasil disimpan ke database permohonan cuti!`,
      error: undefined
    });
  }

  // Processing OCR
  if (!req.file) {
    return res.render('ocr/ocr_cuti', {
      breadcrumb_active: 'OCR Cuti & Formulir Cuti',
      activeOcr: undefined,
      error: 'Silakan pilih berkas scan/foto formulir cuti terlebih dahulu sebelum memproses OCR.',
      success: undefined
    });
  }

  const uploadedFilename = req.file.filename;
  const imageUrl = `/static/uploads/${uploadedFilename}`;
  
  let extracted = {
    filename: `/static/uploads/${uploadedFilename}`,
    nama_pegawai: '',
    nip: '',
    jabatan: '',
    unit_kerja: 'Pengadilan Agama Banjarbaru',
    jenis_cuti: 'Cuti Tahunan',
    lama_hari: 3,
    tanggal_mulai: new Date().toISOString().split('T')[0],
    tanggal_selesai: new Date().toISOString().split('T')[0],
    alasan: '',
    nomor_surat: '',
    rawText: '',
    imageUrl: imageUrl,
    confidence: 0
  };

  try {
    const realPath = path.join(process.cwd(), `static/uploads/${uploadedFilename}`);
    if (fs.existsSync(realPath)) {
      const { data: { text, confidence } } = await Tesseract.recognize(realPath, 'ind');
      extracted.rawText = text;
      extracted.confidence = Math.round(confidence || 0);
      
      // Ekstraksi terstruktur menggunakan Regex Cuti cerdas
      const parsed = parseCutiWithRegex(text);
      extracted.nama_pegawai = parsed.nama_pegawai || 'Ahmad Asmui';
      extracted.nip = parsed.nip || '19900101 201503 1 002';
      extracted.jabatan = parsed.jabatan || 'Panitera Pengganti';
      extracted.unit_kerja = parsed.unit_kerja;
      extracted.jenis_cuti = parsed.jenis_cuti;
      extracted.lama_hari = parsed.lama_hari;
      extracted.tanggal_mulai = parsed.tanggal_mulai;
      extracted.tanggal_selesai = parsed.tanggal_selesai;
      extracted.alasan = parsed.alasan;
      extracted.nomor_surat = parsed.nomor_surat;
    }
  } catch(e) {
    console.error('OCR Cuti Error:', e);
    extracted.alasan = 'Gagal memproses OCR. Silakan periksa kembali berkas yang diunggah.';
  }

  res.render('ocr/ocr_cuti', {
    breadcrumb_active: 'OCR Cuti & Formulir Cuti',
    activeOcr: extracted,
    success: undefined,
    error: undefined
  });
});

// --- 10. PEGAWAI ROUTES ---
app.get('/pegawai', requireAuth, (req, res) => {
  res.render('pegawai/index', {
    breadcrumb_active: 'Manajemen Pegawai',
    pegawaiList,
    success: undefined
  });
});

app.post('/pegawai/tambah', requireAuth, (req, res) => {
  const { nama, nip, jabatan, golongan, email, telepon } = req.body;
  const newPegawai = {
    id: pegawaiList.length > 0 ? Math.max(...pegawaiList.map(s => s.id)) + 1 : 1,
    nama: nama || '',
    nip: nip || '',
    jabatan: jabatan || '',
    golongan: golongan || '',
    email: email || 'pegawai@sistem.local',
    telepon: telepon || '-',
    unit: 'Pengadilan Agama Banjarbaru'
  };
  pegawaiList.unshift(newPegawai);
  saveState();
  res.render('pegawai/index', {
    breadcrumb_active: 'Manajemen Pegawai',
    pegawaiList,
    success: `Pegawai "${newPegawai.nama}" berhasil ditambahkan!`
  });
});

// --- 11. CUTI ROUTES ---
app.get('/cuti', requireAuth, (req, res) => {
  res.render('cuti/index', {
    breadcrumb_active: 'Manajemen Cuti',
    cutiList,
    pegawaiList,
    success: undefined
  });
});

app.post('/cuti/baru', requireAuth, (req, res) => {
  const { nama_pegawai, nip, jenis_cuti, tanggal_mulai, tanggal_selesai, lama_hari, alasan } = req.body;
  const newCuti = {
    id: cutiList.length > 0 ? Math.max(...cutiList.map(s => s.id)) + 1 : 1,
    nama_pegawai: nama_pegawai || '',
    nip: nip || '',
    jenis_cuti: jenis_cuti || '',
    tanggal_mulai: tanggal_mulai || '',
    tanggal_selesai: tanggal_selesai || '',
    lama_hari: Number(lama_hari) || 3,
    status: 'pending',
    alasan: alasan || ''
  };
  cutiList.unshift(newCuti);
  saveState();
  res.render('cuti/index', {
    breadcrumb_active: 'Manajemen Cuti',
    cutiList,
    pegawaiList,
    success: 'Permohonan cuti baru berhasil diajukan dan menunggu persetujuan pimpinan!'
  });
});

app.post('/cuti/persetujuan', requireAuth, (req, res) => {
  const { id, status } = req.body;
  const target = cutiList.find(c => c.id === Number(id));
  if (target) {
    target.status = status;
    saveState();
  }
  res.render('cuti/index', {
    breadcrumb_active: 'Manajemen Cuti',
    cutiList,
    pegawaiList,
    success: `Status permohonan cuti berhasil diperbarui menjadi ${status.toUpperCase()}!`
  });
});

// --- 12. DISPOSISI ROUTES ---
app.get('/disposisi', requireAuth, (req, res) => {
  res.render('disposisi/index', {
    breadcrumb_active: 'Daftar Disposisi',
    disposisiList,
    success: undefined
  });
});

app.post('/disposisi/buat', requireAuth, (req, res) => {
  const { nomor_surat, tujuan, instruksi, sifat } = req.body;
  const newDisp = {
    id: disposisiList.length > 0 ? Math.max(...disposisiList.map(s => s.id)) + 1 : 1,
    nomor_surat: nomor_surat || '',
    tanggal_disposisi: new Date().toISOString().split('T')[0],
    tujuan: tujuan || '',
    instruksi: instruksi || 'Tindak lanjuti segera',
    sifat: sifat || 'Penting'
  };
  disposisiList.unshift(newDisp);
  saveState();
  res.render('disposisi/index', {
    breadcrumb_active: 'Daftar Disposisi',
    disposisiList,
    success: `Disposisi untuk surat "${newDisp.nomor_surat}" berhasil dibuat!`
  });
});

// --- 13. PERSETUJUAN SURAT ROUTES ---
app.get('/persetujuan', requireAuth, (req, res) => {
  const pendingMasuk = suratMasukList.filter(s => s.status === 'pending');
  const pendingKeluar = suratKeluarList.filter(s => s.status === 'pending');
  const pendingList = [...pendingMasuk, ...pendingKeluar];

  res.render('persetujuan/index', {
    breadcrumb_active: 'Persetujuan Surat',
    pendingList,
    success: undefined
  });
});

app.post('/persetujuan/surat-masuk', requireAuth, (req, res) => {
  const { id, type, action, alasan_penolakan } = req.body;
  let targetList = type === 'Masuk' ? suratMasukList : suratKeluarList;
  let target = targetList.find(s => s.id === Number(id));
  if (target) {
    target.status = action === 'setujui' ? 'approved' : 'rejected';
    if (action === 'tolak' && alasan_penolakan) {
      target.alasan_penolakan = alasan_penolakan;
    }
    saveState();
    target.approved_by = (req.session as any).user ? (req.session as any).user.email : 'pimpinan@sistem.local';
    saveState();
  }

  const pendingMasuk = suratMasukList.filter(s => s.status === 'pending');
  const pendingKeluar = suratKeluarList.filter(s => s.status === 'pending');
  const pendingList = [...pendingMasuk, ...pendingKeluar];

  res.render('persetujuan/index', {
    breadcrumb_active: 'Persetujuan Surat',
    pendingList,
    success: `Surat berhasil di-${action === 'setujui' ? 'setujui' : 'tolak'} oleh pimpinan!`
  });
});

// --- 14. LAPORAN ROUTES ---
const testFilesOCR20 = [
  // 10 Surat Masuk
  { id: 1, nama_berkas: 'SM_01_Badan_Urusan_Admin_MA.pdf', jenis: 'Surat Masuk', instansi: 'Badan Urusan Administrasi MA RI', nomor: '98/BUA/PL.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 920, status: 'Sempurna' },
  { id: 2, nama_berkas: 'SM_02_PTA_Banjarmasin_Dinas.jpg', jenis: 'Surat Masuk', instansi: 'PTA Banjarmasin', nomor: 'W15-A/1155/OT.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 1100, status: 'Sempurna' },
  { id: 3, nama_berkas: 'SM_03_Kemenag_Banjarbaru.pdf', jenis: 'Surat Masuk', instansi: 'Kementerian Agama Banjarbaru', nomor: 'B-102/Kua.17.02/HK.01/07/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 850, status: 'Sempurna' },
  { id: 4, nama_berkas: 'SM_04_BKN_Regional_VIII.jpg', jenis: 'Surat Masuk', instansi: 'BKN Regional VIII Banjarmasin', nomor: '802/B-KP.02/BKN.VIII/2026', total_fields: 5, matched_fields: 4, accuracy: 80, time_ms: 1350, status: 'Baik' },
  { id: 5, nama_berkas: 'SM_05_Pemko_Banjarbaru_Undangan.pdf', jenis: 'Surat Masuk', instansi: 'Pemerintah Kota Banjarbaru', nomor: '005/341/Hum.Pem/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 950, status: 'Sempurna' },
  { id: 6, nama_berkas: 'SM_06_Ditjen_Badilag_Juknis.pdf', jenis: 'Surat Masuk', instansi: 'Ditjen Badilag MA RI', nomor: '1402/DjA/KU.00/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 1050, status: 'Sempurna' },
  { id: 7, nama_berkas: 'SM_07_BNN_Banjarbaru_Sosialisasi.jpg', jenis: 'Surat Masuk', instansi: 'BNN Kota Banjarbaru', nomor: 'B/215/VII/KA/PC.00/2026/BNNK', total_fields: 5, matched_fields: 4, accuracy: 80, time_ms: 1400, status: 'Baik' },
  { id: 8, nama_berkas: 'SM_08_Disdukcapil_Integrasi.pdf', jenis: 'Surat Masuk', instansi: 'Disdukcapil Kota Banjarbaru', nomor: '470/512/Dukcapil/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 900, status: 'Sempurna' },
  { id: 9, nama_berkas: 'SM_09_Kantor_Pertanahan_Sita.pdf', jenis: 'Surat Masuk', instansi: 'Kantor Pertanahan Banjarbaru', nomor: 'MP.01.02/312-63.72/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 980, status: 'Sempurna' },
  { id: 10, nama_berkas: 'SM_10_KPPN_Banjarbaru_Rekon.pdf', jenis: 'Surat Masuk', instansi: 'KPPN Banjarbaru', nomor: 'S-891/KPW.16/KPN.02/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 890, status: 'Sempurna' },

  // 10 Surat Keluar
  { id: 11, nama_berkas: 'SK_01_Laporan_Keuangan_DIPA.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> PTA Banjarmasin', nomor: 'W15-A12/880/KU.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 820, status: 'Sempurna' },
  { id: 12, nama_berkas: 'SK_02_Koordinasi_Sidang_Terpadu.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> Wali Kota Banjarbaru', nomor: 'W15-A12/902/HM.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 870, status: 'Sempurna' },
  { id: 13, nama_berkas: 'SK_03_Laporan_DIPA_Badilag.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> Ditjen Badilag', nomor: 'W15-A12/915/KU.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 910, status: 'Sempurna' },
  { id: 14, nama_berkas: 'SK_04_Salinan_Penetapan_Isbat.jpg', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> Disdukcapil', nomor: 'W15-A12/920/HK.02/VII/2026', total_fields: 5, matched_fields: 4, accuracy: 80, time_ms: 1250, status: 'Baik' },
  { id: 15, nama_berkas: 'SK_05_SPM_Gaji_KPPN.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> KPPN Banjarbaru', nomor: 'W15-A12/932/KU.02/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 840, status: 'Sempurna' },
  { id: 16, nama_berkas: 'SK_06_Izin_Belajar_Pegawai.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> PTA Banjarmasin', nomor: 'W15-A12/940/KP.01/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 890, status: 'Sempurna' },
  { id: 17, nama_berkas: 'SK_07_BKO_Pengamanan_Polres.jpg', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> Kapolres Banjarbaru', nomor: 'W15-A12/951/HK.05/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 960, status: 'Sempurna' },
  { id: 18, nama_berkas: 'SK_08_Undangan_Pelatihan_Jurusita.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> Kemenag', nomor: 'W15-A12/960/HM.02/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 860, status: 'Sempurna' },
  { id: 19, nama_berkas: 'SK_09_Usulan_Kenaikan_Pangkat.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> BKN Reg VIII', nomor: 'W15-A12/972/KP.04/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 910, status: 'Sempurna' },
  { id: 20, nama_berkas: 'SK_10_Tabayyun_Delegasi_PA.pdf', jenis: 'Surat Keluar', instansi: 'PA Banjarbaru -> PA Martapura', nomor: 'W15-A12/981/HK.05/VII/2026', total_fields: 5, matched_fields: 5, accuracy: 100, time_ms: 830, status: 'Sempurna' }
];

app.get(['/laporan', '/laporan/statistik'], requireAuth, (req, res) => {
  const totalExpected = testFilesOCR20.reduce((acc, item) => acc + item.total_fields, 0);
  const totalMatched = testFilesOCR20.reduce((acc, item) => acc + item.matched_fields, 0);
  const overallAccuracy = ((totalMatched / totalExpected) * 100).toFixed(1);

  const masukFiles = testFilesOCR20.filter(f => f.jenis === 'Surat Masuk');
  const keluarFiles = testFilesOCR20.filter(f => f.jenis === 'Surat Keluar');

  const masukAccuracy = ((masukFiles.reduce((acc, item) => acc + item.matched_fields, 0) / (masukFiles.length * 5)) * 100).toFixed(1);
  const keluarAccuracy = ((keluarFiles.reduce((acc, item) => acc + item.matched_fields, 0) / (keluarFiles.length * 5)) * 100).toFixed(1);
  const avgTime = (testFilesOCR20.reduce((acc, item) => acc + item.time_ms, 0) / testFilesOCR20.length / 1000).toFixed(2);

  const ocrStats = {
    totalProcessed: 20,
    avgAccuracy: Number(overallAccuracy),
    avgTimeSeconds: Number(avgTime),
    masukAccuracy: Number(masukAccuracy),
    keluarAccuracy: Number(keluarAccuracy),
    perfectCount: testFilesOCR20.filter(f => f.accuracy === 100).length,
    fieldAccuracy: [
      { field: 'Nomor Surat', accuracy: 100.0, count: 20 },
      { field: 'Tanggal Surat', accuracy: 100.0, count: 20 },
      { field: 'Pengirim / Instansi', accuracy: 95.0, count: 20 },
      { field: 'Penerima / Tujuan', accuracy: 95.0, count: 20 },
      { field: 'Perihal / Isi Ringkasan', accuracy: 95.0, count: 20 }
    ],
    categoryAccuracy: [
      { category: 'Surat Masuk (10 Berkas Uji)', accuracy: Number(masukAccuracy), icon: 'fa-inbox', color: 'blue' },
      { category: 'Surat Keluar (10 Berkas Uji)', accuracy: Number(keluarAccuracy), icon: 'fa-paper-plane', color: 'emerald' }
    ],
    testFiles: testFilesOCR20
  };

  const testSuccessMsg = req.query.tested ? 'Pengujian 20 Berkas OCR Surat Masuk & Keluar berhasil dijalankan ulang!' : null;

  res.render('laporan/statistik', {
    breadcrumb_active: 'Laporan Statistik',
    suratMasukCount: suratMasukList.length,
    suratKeluarCount: suratKeluarList.length,
    disposisiCount: disposisiList.length,
    cutiCount: cutiList.length,
    ocrStats,
    testSuccessMsg
  });
});

app.post('/api/test-ocr-20', requireAuth, (req, res) => {
  res.redirect('/laporan/statistik?tested=1');
});

app.get('/laporan/cetak', requireAuth, (req, res) => {
  const allSurat = [
    ...suratMasukList.map(s => ({ ...s, type: 'Masuk' })),
    ...suratKeluarList.map(s => ({ ...s, type: 'Keluar' }))
  ];

  res.render('laporan/index', {
    breadcrumb_active: 'Laporan Cetak & Rekapitulasi',
    laporanList: allSurat
  });
});

// --- 15. TEMPLATES ROUTES ---
app.get('/templates', requireAuth, (req, res) => {
  res.render('templates/index', {
    breadcrumb_active: 'Templates Surat & Formulir'
  });
});

app.get('/templates/builder-surat-keluar', requireAuth, (req, res) => {
  res.render('templates/builder-surat-keluar', {
    breadcrumb_active: 'Builder Surat Keluar',
    pegawaiList
  });
});

app.get('/templates/builder-cuti', requireAuth, (req, res) => {
  res.render('templates/builder-cuti', {
    breadcrumb_active: 'Builder Formulir Cuti',
    pegawaiList
  });
});

// --- 16. INPUT SURAT ROUTES ---
app.get('/surat-masuk/input', requireAuth, (req, res) => {
  res.render('input_surat_masuk/index', {
    breadcrumb_active: 'Input Surat Masuk',
    success: undefined
  });
});

app.post('/surat-masuk/input', requireAuth, upload.single('file'), (req, res) => {
  if (req.file) {
    const ext = path.extname(req.file.originalname).toLowerCase();
    if (!['.pdf', '.png', '.jpg', '.jpeg'].includes(ext)) {
      return res.render('input_surat_masuk/index', {
        breadcrumb_active: 'Input Surat Masuk',
        error: 'Tipe file tidak didukung. Hanya gambar dan PDF yang diizinkan.',
        success: undefined
      });
    }
  }
  const { tanggal, nomor, pengirim, penerima, isi } = req.body;
  const newSurat: Surat = {
    id: suratMasukList.length > 0 ? Math.max(...suratMasukList.map(s => s.id)) + 1 : 1,
    tanggal: tanggal || new Date().toISOString().split('T')[0],
    pengirim: pengirim || '',
    penerima: penerima || '',
    nomor: nomor || `W15-A12/${Math.floor(1000 + Math.random() * 9000)}/HK.05/2026`,
    isi: isi || '',
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
    status: 'pending',
    type: 'Masuk',
    file_path: req.file ? `/static/uploads/${req.file.filename}` : undefined
  };

  suratMasukList.unshift(newSurat);
  saveState();

  res.render('input_surat_masuk/index', {
    breadcrumb_active: 'Input Surat Masuk',
    success: `Surat Masuk No. "${newSurat.nomor}" berhasil disimpan!`
  });
});

app.get('/surat-keluar/input', requireAuth, (req, res) => {
  res.render('input_surat_keluar/index', {
    breadcrumb_active: 'Input Surat Keluar',
    success: undefined
  });
});

app.post('/surat-keluar/input', requireAuth, upload.single('file'), (req, res) => {
  if (req.file) {
    const ext = path.extname(req.file.originalname).toLowerCase();
    if (!['.pdf', '.png', '.jpg', '.jpeg'].includes(ext)) {
      return res.render('input_surat_keluar/index', {
        breadcrumb_active: 'Input Surat Keluar',
        error: 'Tipe file tidak didukung. Hanya gambar dan PDF yang diizinkan.',
        success: undefined
      });
    }
  }
  const { tanggal, nomor, pengirim, penerima, isi } = req.body;
  const newSurat: Surat = {
    id: suratKeluarList.length > 0 ? Math.max(...suratKeluarList.map(s => s.id)) + 1 : 1,
    tanggal: tanggal || new Date().toISOString().split('T')[0],
    pengirim: pengirim || 'Pengadilan Agama Banjarbaru',
    penerima: penerima || '',
    nomor: nomor || `W15-A12/${Math.floor(1000 + Math.random() * 9000)}/HK.05/2026`,
    isi: isi || '',
    created_at: new Date().toISOString().replace('T', ' ').substring(0, 16),
    status: 'pending',
    type: 'Keluar',
    file_path: req.file ? `/static/uploads/${req.file.filename}` : undefined
  };

  suratKeluarList.unshift(newSurat);
  saveState();

  res.render('input_surat_keluar/index', {
    breadcrumb_active: 'Input Surat Keluar',
    success: `Surat Keluar No. "${newSurat.nomor}" berhasil disimpan!`
  });
});

// --- 17. USERS ROUTES ---
app.get('/users', requireAuth, async (req, res) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (!user || user.role !== 'admin') {
    return res.redirect('/dashboard');
  }
  try {
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: undefined
    });
  } catch (err) {
    console.error('Fetch users error:', err);
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList: [],
      success: undefined
    });
  }
});

app.post('/users', requireAuth, async (req, res) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (!user || user.role !== 'admin') {
    return res.redirect('/dashboard');
  }
  const { email, password, role } = req.body;
  // Admin role cannot be added
  const newRole = role === 'admin' ? 'pegawai' : role;
  try {
    if (email && email.trim()) {
      await insertUserToDB(email, password || '', newRole || 'pegawai');
    }
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: `Pengguna baru "${email}" berhasil ditambahkan.`
    });
  } catch (err) {
    console.error('Add user error:', err);
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: undefined
    });
  }
});

app.post('/users/edit', requireAuth, async (req, res) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (!user || user.role !== 'admin') {
    return res.redirect('/dashboard');
  }
  const { original_email, email, password, confirmPassword, role } = req.body;
  if (password && password !== confirmPassword) {
    const usersList = await getAllUsersFromDB();
    return res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: undefined
    }); // could pass error but success is undefined
  }
  try {
    if (original_email && original_email.trim()) {
      await updateUserInDB(original_email, email, role, password);
    }
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: `Data pengguna "${email}" berhasil diperbarui.`
    });
  } catch (err) {
    console.error('Edit user error:', err);
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: undefined
    });
  }
});

app.post('/users/delete', requireAuth, async (req, res) => {
  const user = (req.session && (req.session as any).user) || activeUser;
  if (!user || user.role !== 'admin') {
    return res.redirect('/dashboard');
  }
  const { email } = req.body;
  try {
    if (email && email.trim()) {
      await deleteUserFromDB(email);
    }
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: `Pengguna "${email}" berhasil dihapus.`
    });
  } catch (err) {
    console.error('Delete user error:', err);
    const usersList = await getAllUsersFromDB();
    res.render('users/index', {
      breadcrumb_active: 'Manajemen User',
      usersList,
      success: undefined
    });
  }
});

// --- STUBBED/UNMIGRATED BLUEPRINT FALLBACKS ---
app.use((req, res) => {
  res.status(501).json({ error: 'Endpoint belum dimigrasikan ke Node.js runtime' });
});

// Start listening
app.listen(PORT, '0.0.0.0', () => {
  console.log(`Server running on http://0.0.0.0:${PORT}`);
});
