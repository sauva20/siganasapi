import { Response } from "express";
import { pool } from "../db/mysql";
import { AuthRequest } from "../middleware/auth";

export const getSummary = async (req: AuthRequest, res: Response) => {
  try {
    const [countRows]: any = await pool.query("SELECT COUNT(*) as total FROM batch_panen");
    const totalBatches = countRows[0].total;
    
    const [gradings]: any = await pool.query(`
      SELECT grade_mutu, COUNT(*) as count 
      FROM grading_nanas 
      GROUP BY grade_mutu
    `);

    const breakdown = {
      grade_a: 0,
      grade_b: 0,
      grade_c: 0,
      reject: 0,
    };

    gradings.forEach((g: any) => {
      if (g.grade_mutu === "grade_a") breakdown.grade_a = g.count;
      if (g.grade_mutu === "grade_b") breakdown.grade_b = g.count;
      if (g.grade_mutu === "grade_c") breakdown.grade_c = g.count;
      if (g.grade_mutu === "reject") breakdown.reject = g.count;
    });

    res.json({
      total_batches: totalBatches,
      grading_breakdown: breakdown,
    });
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getPerLokasi = async (req: AuthRequest, res: Response) => {
  try {
    const [batches]: any = await pool.query(`
      SELECT b.*, k.kecamatan
      FROM batch_panen b
      LEFT JOIN kebun k ON b.kebun_id = k.id
    `);

    const locationData: Record<string, any> = {};

    batches.forEach((b: any) => {
      const loc = b.kecamatan || "Tidak Diketahui";
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
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};

export const getPerPetani = async (req: AuthRequest, res: Response) => {
  try {
    const [batches]: any = await pool.query(`
      SELECT b.*, u.nama_lengkap as petani_nama
      FROM batch_panen b
      LEFT JOIN kebun k ON b.kebun_id = k.id
      LEFT JOIN users u ON k.petani_id = u.id
    `);

    const petaniData: Record<string, any> = {};

    batches.forEach((b: any) => {
      const p = b.petani_nama || "Tidak Diketahui";
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
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
