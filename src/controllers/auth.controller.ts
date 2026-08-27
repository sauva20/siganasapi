import { Request, Response } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { pool } from "../db/mysql";
import { v4 as uuidv4 } from "uuid";

const JWT_SECRET = process.env.JWT_SECRET || "GANTI_INI_DI_PRODUCTION";

export const login = async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;

    const [rows]: any = await pool.query(
      "SELECT * FROM User WHERE username = ?",
      [username]
    );

    const user = rows[0];

    if (!user || !user.is_active) {
      return res.status(401).json({ detail: "Username atau password salah" });
    }

    const isValidPassword = await bcrypt.compare(password, user.password_hash);
    if (!isValidPassword) {
      return res.status(401).json({ detail: "Username atau password salah" });
    }

    const token = jwt.sign(
      { id: user.id, username: user.username, role: user.role },
      JWT_SECRET,
      { expiresIn: "24h" }
    );

    res.json({
      access_token: token,
      token_type: "bearer",
      user: {
        id: user.id,
        username: user.username,
        role: user.role,
        nama_lengkap: user.nama_lengkap
      }
    });
  } catch (error: any) {
    console.error("Login error:", error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const register = async (req: Request, res: Response) => {
  try {
    const { username, password, nama_lengkap, no_hp, role } = req.body;

    const [existing]: any = await pool.query(
      "SELECT id FROM User WHERE username = ?",
      [username]
    );
    
    if (existing.length > 0) {
      return res.status(400).json({ detail: "Username sudah digunakan" });
    }

    const salt = await bcrypt.genSalt(10);
    const password_hash = await bcrypt.hash(password, salt);
    const id = uuidv4();

    await pool.query(
      "INSERT INTO User (id, username, password_hash, nama_lengkap, no_hp, role, is_active, created_at, updated_at) VALUES (?, ?, ?, ?, ?, ?, 1, NOW(), NOW())",
      [id, username, password_hash, nama_lengkap, no_hp, role]
    );

    res.status(201).json({
      id,
      username,
      nama_lengkap,
      role
    });
  } catch (error: any) {
    console.error("Register error:", error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getMe = async (req: any, res: Response) => {
  try {
    const [rows]: any = await pool.query(
      "SELECT id, username, nama_lengkap, no_hp, role, is_active, created_at FROM User WHERE id = ?",
      [req.user.id]
    );
    
    const user = rows[0];
    if (!user) return res.status(404).json({ detail: "User tidak ditemukan" });
    res.json(user);
  } catch (error: any) {
    console.error("getMe error:", error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
