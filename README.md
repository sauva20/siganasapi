# 🍍 Nanas Grading Backend API

Backend API untuk sistem grading buah nanas multi-tier berbasis AI (YOLOv11).  
Bagian dari penelitian: **Framework Sistem Digital Berbasis AI untuk Grading Buah Nanas Multi-Tier**  
Politeknik Negeri Subang — 2026

---

## Fitur Utama

| Fitur | Keterangan |
|-------|-----------|
| **AI Grading** | Klasifikasi otomatis via YOLOv11 (Grade A/B/C/Reject) |
| **DSS** | Rekomendasi pasar + estimasi harga per grade |
| **Traceability** | QR Code per batch + blockchain hash (SHA-256) |
| **Multi-role** | petani, pengepul, eksportir, pabrik, dinas_pertanian |
| **JWT Auth** | Login dengan username & password |

---

## Struktur Project

```
nanas-grading-backend/
├── app/
│   ├── main.py                   # Entry point FastAPI
│   ├── core/
│   │   ├── config.py             # Settings dari .env
│   │   └── security.py           # Hashing password & JWT
│   ├── database/
│   │   ├── base.py               # DeclarativeBase SQLAlchemy
│   │   └── session.py            # Engine & SessionLocal
│   ├── models/                   # ORM models
│   │   ├── user.py
│   │   ├── kebun.py
│   │   ├── batch.py
│   │   ├── grading.py
│   │   └── blockchain.py
│   ├── schemas/                  # Pydantic schemas
│   │   ├── user_schema.py
│   │   ├── kebun_schema.py
│   │   ├── batch_schema.py
│   │   └── grading_schema.py
│   ├── api/
│   │   ├── deps.py               # Dependency injection
│   │   └── v1/
│   │       ├── auth_router.py    # POST /login, /register, /me
│   │       ├── batch_router.py   # CRUD batch panen
│   │       └── yolo_router.py    # POST /scan (upload + grading)
│   ├── services/
│   │   ├── yolo_engine.py        # Load model & inferensi
│   │   ├── dss_engine.py         # Algoritma penentuan grade
│   │   └── blockchain_hash.py    # SHA-256 hash & verifikasi
│   ├── middleware/
│   │   └── error_handler.py      # Global exception handler
│   └── static/uploads/           # Storage foto nanas
├── weights/
│   └── yolov11_nanas.pt          # Model weights (tidak di-commit)
├── docs/
│   └── schema.sql                # SQL schema database
├── requirements.txt
├── .env.example
└── .gitignore
```

---

## Instalasi & Menjalankan

### 1. Clone & setup environment

```bash
git clone <repo-url>
cd nanas-grading-backend

python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate

pip install -r requirements.txt
```

### 2. Konfigurasi environment

```bash
cp .env.example .env
# Edit .env sesuai konfigurasi database dan secret key Anda
```

### 3. Setup database

```bash
# Buat database di MySQL
mysql -u root -p < docs/schema.sql
```

### 4. Jalankan server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

Akses API docs: **http://localhost:8000/docs**

---

## Endpoint Utama

| Method | Endpoint | Deskripsi |
|--------|----------|-----------|
| `POST` | `/api/v1/auth/login` | Login, mendapat JWT token |
| `POST` | `/api/v1/auth/register` | Registrasi pengguna baru |
| `GET` | `/api/v1/auth/me` | Profil user yang login |
| `POST` | `/api/v1/batches/` | Buat batch panen baru |
| `GET` | `/api/v1/batches/` | Daftar batch |
| `PATCH` | `/api/v1/batches/{id}/status` | Update status distribusi |
| `POST` | `/api/v1/grading/{batch_id}/scan` | Upload foto + grading AI |
| `GET` | `/api/v1/grading/{batch_id}/results` | Hasil grading per batch |

---

## Grade & Rekomendasi Pasar

| Grade | Kualitas | Target Pasar | Estimasi Harga |
|-------|----------|-------------|----------------|
| **Grade A** | Mutu Ekspor | Timur Tengah / Internasional | Rp 8.000–12.000/kg |
| **Grade B** | Premium Lokal | Supermarket / Retail | Rp 5.000–7.500/kg |
| **Grade C** | Standar | Pasar Tradisional / Industri | Rp 2.500–4.500/kg |
| **Reject** | Tidak Layak Jual | Pakan Ternak / Kompos | Rp 0–500/kg |

---

## Tim Peneliti
- Dwi Vernanda
- Tri Herdiawan
- Desy Triastuti

Politeknik Negeri Subang — Penelitian Dasar Fundamental 2026
