import { Request, Response } from "express";
import { prisma } from "../db/prisma";
import { verifyBlock } from "../services/traceability_service";

export const traceBatch = async (req: Request, res: Response) => {
  try {
    const { kode_batch } = req.params;
    
    const batch = await prisma.batchPanen.findUnique({
      where: { kode_batch },
      include: {
        kebun: { include: { petani: { select: { nama_lengkap: true } } } },
        gradings: true,
      }
    });

    if (!batch) {
      return res.status(404).json({ detail: "Data traceability tidak ditemukan" });
    }

    const verifyResult = await verifyBlock(batch.id);

    res.json({
      batch_info: batch,
      blockchain_verification: verifyResult,
    });
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
