import { Response } from "express";
import { pool } from "../db/mysql";
import { AuthRequest } from "../middleware/auth";

export const listUsers = async (req: AuthRequest, res: Response) => {
  try {
    const { role } = req.query;
    
    let query = "SELECT id, username, nama_lengkap, role, no_hp, created_at FROM users WHERE is_active = 1";
    const params: any[] = [];

    if (role) {
      query += " AND role = ?";
      params.push(role);
    }
    
    query += " ORDER BY created_at DESC";

    const [rows]: any = await pool.query(query, params);
    res.json(rows);
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
