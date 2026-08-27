import { Response } from "express";
import { pool } from "../db/mysql";
import { AuthRequest } from "../middleware/auth";
import { syncBlock } from "../services/traceability_service";

export const createBatch = async (req: AuthRequest, res: Response) => {
  try {
    const { kebun_id, tanggal_panen, catatan } = req.body;
    
    const [kebunRows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [kebun_id]);
    const kebun = kebunRows[0];
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    const kode_batch = `BATCH-${new Date(tanggal_panen).toISOString().split('T')[0].replace(/-/g, '')}-${Math.floor(1000 + Math.random() * 9000)}`;
    const PUBLIC_BASE_URL = process.env.PUBLIC_BASE_URL || "http://localhost:8000";
    const kode_qr = `${PUBLIC_BASE_URL}/public/trace/${kode_batch}`;
    const tglPanenFormatted = new Date(tanggal_panen).toISOString().slice(0, 19).replace('T', ' ');

    const [result]: any = await pool.query(
      "INSERT INTO batch_panen (kebun_id, kode_batch, kode_qr, tanggal_panen, catatan, status_distribusi, total_buah, total_berat_kg, jumlah_grade_a, jumlah_grade_b, jumlah_grade_c, jumlah_reject, created_at, updated_at) VALUES (?, ?, ?, ?, ?, 'di_lahan', 0, 0, 0, 0, 0, 0, NOW(), NOW())",
      [kebun_id, kode_batch, kode_qr, tglPanenFormatted, catatan]
    );

    const [batchRows]: any = await pool.query("SELECT * FROM batch_panen WHERE id = ?", [result.insertId]);
    const batch = batchRows[0];

    await syncBlock(batch);
    res.status(201).json(batch);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const listBatches = async (req: AuthRequest, res: Response) => {
  try {
    const [batches]: any = await pool.query(`
      SELECT b.*, k.nama_kebun, u.nama_lengkap as petani_nama
      FROM batch_panen b
      LEFT JOIN kebun k ON b.kebun_id = k.id
      LEFT JOIN users u ON k.petani_id = u.id
      ORDER BY b.created_at DESC
    `);
    
    const formattedBatches = batches.map((b: any) => ({
      ...b,
      kebun: {
        nama_kebun: b.nama_kebun,
        petani: { nama_lengkap: b.petani_nama }
      }
    }));
    
    res.json(formattedBatches);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getBatch = async (req: AuthRequest, res: Response) => {
  try {
    const [batchRows]: any = await pool.query(`
      SELECT b.*, k.nama_kebun, u.nama_lengkap as petani_nama
      FROM batch_panen b
      LEFT JOIN kebun k ON b.kebun_id = k.id
      LEFT JOIN users u ON k.petani_id = u.id
      WHERE b.id = ?
    `, [Number(req.params.id)]);
    
    const batch = batchRows[0];
    if (!batch) return res.status(404).json({ detail: "Batch tidak ditemukan" });

    const [gradings]: any = await pool.query("SELECT * FROM grading_nanas WHERE batch_id = ?", [batch.id]);
    const [blockchain]: any = await pool.query("SELECT * FROM traceability_blockchain WHERE batch_id = ?", [batch.id]);

    batch.kebun = {
      nama_kebun: batch.nama_kebun,
      petani: { nama_lengkap: batch.petani_nama }
    };
    batch.gradings = gradings;
    batch.blockchain = blockchain.length > 0 ? blockchain[0] : null;

    res.json(batch);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
