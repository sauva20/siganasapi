import { Response } from "express";
import { prisma } from "../db/prisma";
import { AuthRequest } from "../middleware/auth";

export const getSummary = async (req: AuthRequest, res: Response) => {
  try {
    const totalBatches = await prisma.batchPanen.count();
    
    const gradings = await prisma.gradingNanas.groupBy({
      by: ["grade_mutu"],
      _count: { grade_mutu: true },
    });

    const breakdown = {
      grade_a: 0,
      grade_b: 0,
      grade_c: 0,
      reject: 0,
    };

    gradings.forEach((g: any) => {
      if (g.grade_mutu === "grade_a") breakdown.grade_a = g._count.grade_mutu;
      if (g.grade_mutu === "grade_b") breakdown.grade_b = g._count.grade_mutu;
      if (g.grade_mutu === "grade_c") breakdown.grade_c = g._count.grade_mutu;
      if (g.grade_mutu === "reject") breakdown.reject = g._count.grade_mutu;
    });

    res.json({
      total_batches: totalBatches,
      grading_breakdown: breakdown,
    });
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getPerLokasi = async (req: AuthRequest, res: Response) => {
  try {
    const batches = await prisma.batchPanen.findMany({
      include: {
        kebun: true,
      },
    });

    const locationData: Record<string, any> = {};

    batches.forEach((b: any) => {
      const loc = b.kebun.kecamatan || "Tidak Diketahui";
      if (!locationData[loc]) {
        locationData[loc] = {
          total_batch: 0,
          total_buah: 0,
          grade_a: 0,
          grade_b: 0,
          grade_c: 0,
          reject: 0,
        };
      }
      locationData[loc].total_batch += 1;
      locationData[loc].total_buah += b.total_buah;
      locationData[loc].grade_a += b.jumlah_grade_a;
      locationData[loc].grade_b += b.jumlah_grade_b;
      locationData[loc].grade_c += b.jumlah_grade_c;
      locationData[loc].reject += b.jumlah_reject;
    });

    const result = Object.keys(locationData).map(k => ({
      lokasi: k,
      ...locationData[k]
    }));

    res.json(result);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getPerPetani = async (req: AuthRequest, res: Response) => {
  try {
    const batches = await prisma.batchPanen.findMany({
      include: {
        kebun: { include: { petani: true } },
      },
    });

    const petaniData: Record<string, any> = {};

    batches.forEach((b: any) => {
      const p = b.kebun.petani.nama_lengkap || "Tidak Diketahui";
      if (!petaniData[p]) {
        petaniData[p] = {
          total_batch: 0,
          total_buah: 0,
          grade_a: 0,
          grade_b: 0,
          grade_c: 0,
          reject: 0,
        };
      }
      petaniData[p].total_batch += 1;
      petaniData[p].total_buah += b.total_buah;
      petaniData[p].grade_a += b.jumlah_grade_a;
      petaniData[p].grade_b += b.jumlah_grade_b;
      petaniData[p].grade_c += b.jumlah_grade_c;
      petaniData[p].reject += b.jumlah_reject;
    });

    const result = Object.keys(petaniData).map(k => ({
      petani: k,
      ...petaniData[k]
    }));

    res.json(result);
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
