import { Response } from "express";
import { prisma } from "../db/prisma";
import { AuthRequest } from "../middleware/auth";
import { syncBlock } from "../services/traceability_service";

export const createBatch = async (req: AuthRequest, res: Response) => {
  try {
    const { kebun_id, tanggal_panen, catatan } = req.body;
    const kebun = await prisma.kebun.findUnique({ where: { id: kebun_id } });
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    const kode_batch = `BATCH-${new Date(tanggal_panen).toISOString().split('T')[0].replace(/-/g, '')}-${Math.floor(1000 + Math.random() * 9000)}`;
    const PUBLIC_BASE_URL = process.env.PUBLIC_BASE_URL || "http://localhost:8000";
    const kode_qr = `${PUBLIC_BASE_URL}/public/trace/${kode_batch}`;

    const batch = await prisma.batchPanen.create({
      data: {
        kebun_id,
        kode_batch,
        kode_qr,
        tanggal_panen: new Date(tanggal_panen),
        catatan,
      },
    });

    await syncBlock(batch);
    res.status(201).json(batch);
  } catch (error) {
    console.error(error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const listBatches = async (req: AuthRequest, res: Response) => {
  try {
    const batches = await prisma.batchPanen.findMany({
      orderBy: { created_at: "desc" },
      include: {
        kebun: {
          include: { petani: { select: { nama_lengkap: true } } }
        }
      }
    });
    res.json(batches);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getBatch = async (req: AuthRequest, res: Response) => {
  try {
    const batch = await prisma.batchPanen.findUnique({
      where: { id: Number(req.params.id) },
      include: {
        kebun: { include: { petani: { select: { nama_lengkap: true } } } },
        gradings: true,
        blockchain: true,
      }
    });
    if (!batch) return res.status(404).json({ detail: "Batch tidak ditemukan" });
    res.json(batch);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
