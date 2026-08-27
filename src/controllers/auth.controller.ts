import { Request, Response } from "express";
import bcrypt from "bcryptjs";
import jwt from "jsonwebtoken";
import { prisma } from "../db/prisma";

const JWT_SECRET = process.env.JWT_SECRET || "GANTI_INI_DI_PRODUCTION";

export const login = async (req: Request, res: Response) => {
  try {
    const { username, password } = req.body;

    const user = await prisma.user.findUnique({
      where: { username }
    });

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
  } catch (error) {
    console.error("Login error:", error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const register = async (req: Request, res: Response) => {
  try {
    const { username, password, nama_lengkap, no_hp, role } = req.body;

    const existingUser = await prisma.user.findUnique({ where: { username } });
    if (existingUser) {
      return res.status(400).json({ detail: "Username sudah digunakan" });
    }

    const salt = await bcrypt.genSalt(10);
    const password_hash = await bcrypt.hash(password, salt);

    const newUser = await prisma.user.create({
      data: {
        username,
        password_hash,
        nama_lengkap,
        no_hp,
        role
      }
    });

    res.status(201).json({
      id: newUser.id,
      username: newUser.username,
      nama_lengkap: newUser.nama_lengkap,
      role: newUser.role
    });
  } catch (error) {
    console.error("Register error:", error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getMe = async (req: any, res: Response) => {
  try {
    const user = await prisma.user.findUnique({
      where: { id: req.user.id },
      select: {
        id: true,
        username: true,
        nama_lengkap: true,
        no_hp: true,
        role: true,
        is_active: true,
        created_at: true
      }
    });
    if (!user) return res.status(404).json({ detail: "User tidak ditemukan" });
    res.json(user);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
