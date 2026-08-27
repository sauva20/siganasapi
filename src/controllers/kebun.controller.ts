import { Response } from "express";
import { pool } from "../db/mysql";
import { AuthRequest } from "../middleware/auth";

export const createKebun = async (req: AuthRequest, res: Response) => {
  try {
    const { petani_id, nama_kebun, kecamatan, varietas_nanas, jenis_bibit, jenis_pupuk, tanggal_tanam, latitude, longitude, luas_lahan_hektar } = req.body;
    
    const tglTanamFormatted = tanggal_tanam ? new Date(tanggal_tanam).toISOString().slice(0, 19).replace('T', ' ') : null;

    const [result]: any = await pool.query(
      "INSERT INTO kebun (petani_id, nama_kebun, kecamatan, varietas_nanas, jenis_bibit, jenis_pupuk, tanggal_tanam, latitude, longitude, luas_lahan_hektar, is_active, created_at) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1, NOW())",
      [petani_id, nama_kebun, kecamatan, varietas_nanas, jenis_bibit, jenis_pupuk, tglTanamFormatted, latitude, longitude, luas_lahan_hektar]
    );

    const [rows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [result.insertId]);
    res.status(201).json(rows[0]);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const listKebun = async (req: AuthRequest, res: Response) => {
  try {
    const [rows]: any = await pool.query("SELECT * FROM kebun WHERE is_active = 1 ORDER BY created_at DESC");
    res.json(rows);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getKebun = async (req: AuthRequest, res: Response) => {
  try {
    const [rows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [Number(req.params.id)]);
    const kebun = rows[0];
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });
    res.json(kebun);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const updateKebun = async (req: AuthRequest, res: Response) => {
  try {
    const [rows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [Number(req.params.id)]);
    const kebun = rows[0];
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    const updateData = { ...req.body };
    const setClauses: string[] = [];
    const values: any[] = [];

    for (const key of Object.keys(updateData)) {
      if (updateData[key] !== undefined) {
        setClauses.push(`${key} = ?`);
        if (key === 'tanggal_tanam' && updateData[key]) {
          values.push(new Date(updateData[key]).toISOString().slice(0, 19).replace('T', ' '));
        } else {
          values.push(updateData[key]);
        }
      }
    }

    if (setClauses.length > 0) {
      values.push(kebun.id);
      await pool.query(`UPDATE kebun SET ${setClauses.join(', ')} WHERE id = ?`, values);
    }

    const [updatedRows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [kebun.id]);
    res.json(updatedRows[0]);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const deactivateKebun = async (req: AuthRequest, res: Response) => {
  try {
    const [rows]: any = await pool.query("SELECT * FROM kebun WHERE id = ?", [Number(req.params.id)]);
    const kebun = rows[0];
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    await pool.query("UPDATE kebun SET is_active = 0 WHERE id = ?", [kebun.id]);
    res.status(204).send();
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
