import { Response } from "express";
import { prisma } from "../db/prisma";
import { AuthRequest } from "../middleware/auth";

export const createKebun = async (req: AuthRequest, res: Response) => {
  try {
    const { petani_id, nama_kebun, kecamatan, varietas_nanas, jenis_bibit, jenis_pupuk, tanggal_tanam, latitude, longitude, luas_lahan_hektar } = req.body;
    
    const kebun = await prisma.kebun.create({
      data: {
        petani_id,
        nama_kebun,
        kecamatan,
        varietas_nanas,
        jenis_bibit,
        jenis_pupuk,
        tanggal_tanam: tanggal_tanam ? new Date(tanggal_tanam) : null,
        latitude,
        longitude,
        luas_lahan_hektar,
      },
    });
    res.status(201).json(kebun);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const listKebun = async (req: AuthRequest, res: Response) => {
  try {
    const kebuns = await prisma.kebun.findMany({
      where: { is_active: true },
      orderBy: { created_at: "desc" },
    });
    res.json(kebuns);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getKebun = async (req: AuthRequest, res: Response) => {
  try {
    const kebun = await prisma.kebun.findUnique({ where: { id: Number(req.params.id) } });
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });
    res.json(kebun);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const updateKebun = async (req: AuthRequest, res: Response) => {
  try {
    const kebun = await prisma.kebun.findUnique({ where: { id: Number(req.params.id) } });
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    const updateData = { ...req.body };
    if (updateData.tanggal_tanam) updateData.tanggal_tanam = new Date(updateData.tanggal_tanam);

    const updated = await prisma.kebun.update({
      where: { id: kebun.id },
      data: updateData,
    });
    res.json(updated);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const deactivateKebun = async (req: AuthRequest, res: Response) => {
  try {
    const kebun = await prisma.kebun.findUnique({ where: { id: Number(req.params.id) } });
    if (!kebun) return res.status(404).json({ detail: "Kebun tidak ditemukan" });

    await prisma.kebun.update({
      where: { id: kebun.id },
      data: { is_active: false },
    });
    res.status(204).send();
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
