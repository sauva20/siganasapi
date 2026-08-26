-- ============================================================
-- DATABASE: db_nanas_grading
-- Sistem Grading Buah Nanas Multi-Tier Berbasis AI (YOLOv11)
-- Versi: 2.0 (Revisi)
-- ============================================================

CREATE DATABASE IF NOT EXISTS db_nanas_grading
    CHARACTER SET utf8mb4
    COLLATE utf8mb4_unicode_ci;

USE db_nanas_grading;

-- ============================================================
-- 1. TABEL USERS
-- Semua pengguna sistem dalam satu tabel dengan role-based access.
-- Role menentukan fitur yang bisa diakses di aplikasi.
-- ============================================================
CREATE TABLE users (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    username        VARCHAR(50)     NOT NULL UNIQUE,
    password_hash   VARCHAR(255)    NOT NULL,
    nama_lengkap    VARCHAR(100)    NOT NULL,
    no_hp           VARCHAR(15),
    role            ENUM(
                        'petani',
                        'pengepul',
                        'eksportir',
                        'pabrik',
                        'dinas_pertanian'
                    ) NOT NULL,
    is_active       BOOLEAN         DEFAULT TRUE,
    created_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP
) ENGINE=InnoDB COMMENT='Tabel pengguna sistem semua role';


-- ============================================================
-- 2. TABEL KEBUN
-- Data kebun milik petani. Satu petani bisa punya banyak kebun.
-- Menyimpan data GPS dan info agrikultur untuk traceability.
-- ============================================================
CREATE TABLE kebun (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    petani_id           INT             NOT NULL,
    nama_kebun          VARCHAR(100)    NOT NULL,
    kecamatan           VARCHAR(50),                    -- cth: Jalancagak, Cijambe, Cirangkong
    varietas_nanas      VARCHAR(50)     DEFAULT 'Simadu',
    jenis_bibit         VARCHAR(50)     DEFAULT 'Lokal',
    jenis_pupuk         VARCHAR(100),
    tanggal_tanam       DATE,
    latitude            DECIMAL(10, 8)  NOT NULL,
    longitude           DECIMAL(11, 8)  NOT NULL,
    luas_lahan_hektar   DECIMAL(5, 2),
    is_active           BOOLEAN         DEFAULT TRUE,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (petani_id) REFERENCES users(id) ON DELETE CASCADE,
    INDEX idx_petani_id (petani_id),
    INDEX idx_kecamatan (kecamatan)
) ENGINE=InnoDB COMMENT='Data kebun milik petani beserta koordinat GPS';


-- ============================================================
-- 3. TABEL BATCH PANEN
-- Satu batch = satu sesi panen dari satu kebun.
-- Setiap batch menghasilkan satu QR Code untuk traceability.
-- ============================================================
CREATE TABLE batch_panen (
    id                  INT AUTO_INCREMENT PRIMARY KEY,
    kebun_id            INT             NOT NULL,
    pengepul_id         INT,                            -- Bisa NULL jika belum ada pengepul
    kode_batch          VARCHAR(20)     UNIQUE NOT NULL, -- Format: BATCH-YYYYMMDD-XXXX
    kode_qr             VARCHAR(255)    UNIQUE NOT NULL, -- URL atau data yang di-encode ke QR
    tanggal_panen       DATE            NOT NULL,
    catatan             TEXT,                           -- Catatan tambahan dari petani/pengepul
    status_distribusi   ENUM(
                            'di_lahan',
                            'di_pengepul',
                            'terkirim_industri',
                            'terekspor'
                        )               DEFAULT 'di_lahan',
    -- Rekapitulasi otomatis dihitung dari tabel grading_nanas
    total_buah          INT             DEFAULT 0,
    total_berat_kg      DECIMAL(10, 2)  DEFAULT 0.00,
    jumlah_grade_a      INT             DEFAULT 0,
    jumlah_grade_b      INT             DEFAULT 0,
    jumlah_grade_c      INT             DEFAULT 0,
    jumlah_reject       INT             DEFAULT 0,
    created_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at          TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (kebun_id)    REFERENCES kebun(id) ON DELETE CASCADE,
    FOREIGN KEY (pengepul_id) REFERENCES users(id) ON DELETE SET NULL,
    INDEX idx_kebun_id (kebun_id),
    INDEX idx_tanggal_panen (tanggal_panen),
    INDEX idx_status (status_distribusi)
) ENGINE=InnoDB COMMENT='Batch panen, satu batch = satu QR Code traceability';


-- ============================================================
-- 4. TABEL GRADING NANAS
-- Menyimpan hasil inferensi YOLOv11 per buah nanas.
-- Kolom dibagi menjadi: input manual + output AI + output DSS.
-- ============================================================
CREATE TABLE grading_nanas (
    id                      INT AUTO_INCREMENT PRIMARY KEY,
    batch_id                INT             NOT NULL,

    -- === INPUT: Data dari kamera (wajib) ===
    foto_url                VARCHAR(255)    NOT NULL,   -- Path file foto di server

    -- === INPUT: Data manual opsional (bisa diisi atau NULL) ===
    -- Diisi manual jika ada alat refraktometer, bukan dari YOLO
    input_brix_manual       DECIMAL(4, 1),              -- Tingkat kemanisan dari refraktometer
    input_berat_manual_kg   DECIMAL(4, 2),              -- Berat aktual dari timbangan

    -- === OUTPUT AI: Hasil inferensi YOLOv11 ===
    confidence_score        DECIMAL(5, 4)   NOT NULL,   -- Confidence YOLO, contoh: 0.9412
    yolo_raw_output         JSON,                       -- Raw prediction JSON untuk audit/debug
    -- Atribut yang dideteksi YOLO secara visual:
    deteksi_ukuran          ENUM('Kecil', 'Sedang', 'Besar'),
    deteksi_warna_kulit     ENUM('Hijau', 'Kuning_Kehijauan', 'Kuning', 'Oranye'),
    deteksi_kematangan_pct  INT,                        -- Estimasi % kematangan dari visual
    kondisi_mahkota         ENUM('Sempurna', 'Cacat_Rusak') DEFAULT 'Sempurna',
    kondisi_defect          VARCHAR(200)    DEFAULT 'Tidak Ada Cacat',

    -- === OUTPUT DSS: Hasil Decision Support System ===
    grade_mutu              ENUM(
                                'Grade A',  -- Mutu Ekspor
                                'Grade B',  -- Mutu Premium Lokal (Supermarket)
                                'Grade C',  -- Mutu Standar (Pasar Tradisional/Industri)
                                'Reject'    -- Pakan Ternak / Kompos
                            ) NOT NULL,
    rekomendasi_pasar       VARCHAR(150),               -- Contoh: "Ekspor - Timur Tengah"
    estimasi_harga_min      DECIMAL(10, 0),             -- Estimasi harga per kg (Rp)
    estimasi_harga_max      DECIMAL(10, 0),

    scanned_at              TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (batch_id) REFERENCES batch_panen(id) ON DELETE CASCADE,
    INDEX idx_batch_id (batch_id),
    INDEX idx_grade_mutu (grade_mutu),
    INDEX idx_scanned_at (scanned_at)
) ENGINE=InnoDB COMMENT='Hasil grading per buah nanas dari YOLOv11 + DSS';


-- ============================================================
-- 5. TABEL TRACEABILITY BLOCKCHAIN
-- Menyimpan hash SHA-256 untuk integritas data per batch.
-- Setiap batch memiliki satu block. Chain dibangun secara global
-- (previous_hash merujuk ke hash batch sebelumnya secara kronologis).
-- ============================================================
CREATE TABLE traceability_blockchain (
    id              INT AUTO_INCREMENT PRIMARY KEY,
    batch_id        INT             UNIQUE NOT NULL,

    -- Data yang di-hash (snapshot saat block dibuat)
    block_data      JSON            NOT NULL,   -- Snapshot: info batch + kebun + petani + grading summary

    -- Chain integrity
    block_hash      VARCHAR(64)     NOT NULL,   -- SHA-256 dari block_data + previous_hash
    previous_hash   VARCHAR(64)     NOT NULL DEFAULT '0000000000000000000000000000000000000000000000000000000000000000',
    block_index     INT             NOT NULL,   -- Urutan block dalam chain (0 = genesis)

    -- Status validasi
    is_valid        BOOLEAN         DEFAULT TRUE,   -- FALSE jika data dimanipulasi
    validated_at    TIMESTAMP       DEFAULT CURRENT_TIMESTAMP,
    updated_at      TIMESTAMP       DEFAULT CURRENT_TIMESTAMP ON UPDATE CURRENT_TIMESTAMP,

    FOREIGN KEY (batch_id) REFERENCES batch_panen(id) ON DELETE CASCADE,
    INDEX idx_block_index (block_index),
    INDEX idx_is_valid (is_valid)
) ENGINE=InnoDB COMMENT='Blockchain hash per batch untuk traceability data integrity';


-- ============================================================
-- DATA SEED: Akun awal untuk testing
-- Hash di bawah ini adalah hash bcrypt ASLI (bukan placeholder),
-- di-generate dengan bcrypt rounds=12. Password login untuk tiap akun:
--   dinas_admin     -> admin123
--   petani_demo     -> petani123
--   pengepul_demo   -> pengepul123
-- WAJIB GANTI/HAPUS akun-akun ini sebelum deploy ke production!
-- ============================================================
INSERT INTO users (username, password_hash, nama_lengkap, no_hp, role) VALUES
('dinas_admin', '$2b$12$Vj4qezD8baGOXaTQFTmt6.ARWSg/tEu1bDhfo0RZq80LBI57feksW', 'Admin Dinas Pertanian Subang', '081234567890', 'dinas_pertanian'),
('petani_demo', '$2b$12$n7e/fFc3TbmcJktUxF.pMeYlSJMUrdg/JN5nFXtjZQbdnYKWkQU2O', 'Petani Demo Jalancagak', '081234567891', 'petani'),
('pengepul_demo', '$2b$12$kNVRB5fryETWBzvDb0xAtuyG9naYiDKiwK1urnBtq3M./nbqaQwvK', 'Pengepul Demo Subang', '081234567892', 'pengepul');

-- Tambahan petani untuk 3 lokasi sesuai proposal (password sementara: petani123, hash sama seperti petani_demo)
INSERT INTO users (username, password_hash, nama_lengkap, no_hp, role) VALUES
('petani_cijambe', '$2b$12$n7e/fFc3TbmcJktUxF.pMeYlSJMUrdg/JN5nFXtjZQbdnYKWkQU2O', 'Petani Demo Cijambe', '081234567893', 'petani'),
('petani_cirangkong', '$2b$12$n7e/fFc3TbmcJktUxF.pMeYlSJMUrdg/JN5nFXtjZQbdnYKWkQU2O', 'Petani Demo Cirangkong', '081234567894', 'petani');
