import { Request, Response, NextFunction } from "express";
import jwt from "jsonwebtoken";

export interface AuthRequest extends Request {
  user?: {
    id: number;
    username: string;
    role: string;
  };
}

export const authenticateToken = (req: AuthRequest, res: Response, next: NextFunction) => {
  const authHeader = req.headers["authorization"];
  const token = authHeader && authHeader.split(" ")[1];

  if (!token) {
    return res.status(401).json({ detail: "Token tidak ditemukan" });
  }

  jwt.verify(token, process.env.JWT_SECRET || "GANTI_INI_DI_PRODUCTION", (err, user) => {
    if (err) {
      return res.status(403).json({ detail: "Token tidak valid atau sudah kedaluwarsa" });
    }
    req.user = user as any;
    next();
  });
};

export const requireRole = (roles: string[]) => {
  return (req: AuthRequest, res: Response, next: NextFunction) => {
    if (!req.user || !roles.includes(req.user.role)) {
      return res.status(403).json({ detail: "Akses ditolak. Anda tidak memiliki izin." });
    }
    next();
  };
};
