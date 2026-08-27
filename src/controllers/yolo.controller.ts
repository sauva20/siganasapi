import { Response } from "express";
import { prisma } from "../db/prisma";
import { AuthRequest } from "../middleware/auth";
import { determineGrade, DSSInput } from "../services/dss_engine";
import { syncBlock } from "../services/traceability_service";
import { exec } from "child_process";
import path from "path";

export const scanPineapple = async (req: AuthRequest, res: Response) => {
  try {
    const { batch_id, input_brix_manual, input_berat_manual_kg } = req.body;
    
    if (!req.file) {
      return res.status(400).json({ detail: "Gambar wajib diunggah" });
    }
    const imagePath = req.file.path;
    const batchIdNum = Number(batch_id);

    const batch = await prisma.batchPanen.findUnique({ where: { id: batchIdNum } });
    if (!batch) return res.status(404).json({ detail: "Batch tidak ditemukan" });

    // Call Python script for YOLO inference
    // Usage: python yolo_inference.py <image_path>
    const yoloScript = process.env.YOLO_SCRIPT_PATH || "yolo_inference.py";
    const command = `python ${yoloScript} "${imagePath}"`;

    exec(command, async (error, stdout, stderr) => {
      let yoloResult;
      try {
        if (error) throw new Error(stderr || error.message);
        yoloResult = JSON.parse(stdout);
      } catch (err) {
        console.error("YOLO Error:", err);
        // Fallback or handle error
        return res.status(500).json({ detail: "Gagal melakukan inferensi YOLO" });
      }

      const dssInput: DSSInput = {
        deteksi_ukuran: yoloResult.deteksi_ukuran,
        deteksi_warna_kulit: yoloResult.deteksi_warna_kulit,
        deteksi_kematangan_pct: yoloResult.deteksi_kematangan_pct,
        kondisi_mahkota: yoloResult.kondisi_mahkota,
        kondisi_defect: yoloResult.kondisi_defect,
        input_brix_manual: input_brix_manual ? parseFloat(input_brix_manual) : undefined,
        input_berat_manual_kg: input_berat_manual_kg ? parseFloat(input_berat_manual_kg) : undefined,
      };

      const dssOutput = determineGrade(dssInput);

      const grading = await prisma.gradingNanas.create({
        data: {
          batch_id: batchIdNum,
          foto_url: `/static/uploads/${req.file!.filename}`,
          input_brix_manual: dssInput.input_brix_manual,
          input_berat_manual_kg: dssInput.input_berat_manual_kg,
          confidence_score: yoloResult.confidence_score,
          yolo_raw_output: JSON.stringify(yoloResult.raw_output),
          deteksi_ukuran: dssInput.deteksi_ukuran as any,
          deteksi_warna_kulit: dssInput.deteksi_warna_kulit as any,
          deteksi_kematangan_pct: dssInput.deteksi_kematangan_pct,
          kondisi_mahkota: dssInput.kondisi_mahkota as any,
          kondisi_defect: dssInput.kondisi_defect,
          grade_mutu: dssOutput.grade_mutu,
          rekomendasi_pasar: dssOutput.rekomendasi_pasar,
          estimasi_harga_min: dssOutput.estimasi_harga_min,
          estimasi_harga_max: dssOutput.estimasi_harga_max,
        },
      });

      // Update Batch Recap
      const incA = dssOutput.grade_mutu === "grade_a" ? 1 : 0;
      const incB = dssOutput.grade_mutu === "grade_b" ? 1 : 0;
      const incC = dssOutput.grade_mutu === "grade_c" ? 1 : 0;
      const incR = dssOutput.grade_mutu === "reject" ? 1 : 0;
      const addedBerat = dssInput.input_berat_manual_kg || 0;

      const updatedBatch = await prisma.batchPanen.update({
        where: { id: batchIdNum },
        data: {
          total_buah: { increment: 1 },
          total_berat_kg: { increment: addedBerat },
          jumlah_grade_a: { increment: incA },
          jumlah_grade_b: { increment: incB },
          jumlah_grade_c: { increment: incC },
          jumlah_reject: { increment: incR },
        },
      });

      await syncBlock(updatedBatch);

      res.status(201).json({ grading, dss_output: dssOutput, yolo_result: yoloResult });
    });
  } catch (error) {
    res.status(500).json({ detail: "Internal server error" });
  }
};
