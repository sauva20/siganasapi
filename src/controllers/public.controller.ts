import { Request, Response } from "express";
import { pool } from "../db/mysql";
import { verifyBlock } from "../services/traceability_service";

export const traceBatch = async (req: Request, res: Response) => {
  try {
    const { kode_batch } = req.params;
    
    const [batchRows]: any = await pool.query(`
      SELECT b.*, k.nama_kebun, u.nama_lengkap as petani_nama
      FROM batch_panen b
      LEFT JOIN kebun k ON b.kebun_id = k.id
      LEFT JOIN users u ON k.petani_id = u.id
      WHERE b.kode_batch = ?
    `, [kode_batch]);

    const batch = batchRows[0];

    if (!batch) {
      return res.status(404).json({ detail: "Data traceability tidak ditemukan" });
    }

    batch.kebun = {
      nama_kebun: batch.nama_kebun,
      petani: { nama_lengkap: batch.petani_nama }
    };

    const [gradings]: any = await pool.query("SELECT * FROM grading_nanas WHERE batch_id = ?", [batch.id]);
    batch.gradings = gradings;

    const verifyResult = await verifyBlock(batch.id);

    res.json({
      batch_info: batch,
      blockchain_verification: verifyResult,
    });
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
