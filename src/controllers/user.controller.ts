import { Response } from "express";
import { prisma } from "../db/prisma";
import { AuthRequest } from "../middleware/auth";

export const listUsers = async (req: AuthRequest, res: Response) => {
  try {
    const { role } = req.query;
    
    let whereClause: any = { is_active: true };
    if (role) {
      whereClause.role = role;
    }

    const users = await prisma.user.findMany({
      where: whereClause,
      select: {
        id: true,
        username: true,
        nama_lengkap: true,
        role: true,
        no_hp: true,
        created_at: true,
      },
      orderBy: { created_at: "desc" },
    });

    res.json(users);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
