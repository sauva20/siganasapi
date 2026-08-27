import { Response } from "express";
import { pool } from "../db/mysql";
import { AuthRequest } from "../middleware/auth";
import { determineGrade, DSSInput } from "../services/dss_engine";
import { syncBlock } from "../services/traceability_service";
import { exec } from "child_process";

export const scanPineapple = async (req: AuthRequest, res: Response) => {
  try {
    const { batch_id, input_brix_manual, input_berat_manual_kg } = req.body;
    
    if (!req.file) {
      return res.status(400).json({ detail: "Gambar wajib diunggah" });
    }
    const imagePath = req.file.path;
    const batchIdNum = Number(batch_id);

    const [batchRows]: any = await pool.query("SELECT * FROM batch_panen WHERE id = ?", [batchIdNum]);
    const batch = batchRows[0];
    if (!batch) return res.status(404).json({ detail: "Batch tidak ditemukan" });

    // Call Python script for YOLO inference
    const yoloScript = process.env.YOLO_SCRIPT_PATH || "yolo_inference.py";
    const command = `python ${yoloScript} "${imagePath}"`;

    exec(command, async (error, stdout, stderr) => {
      let yoloResult;
      try {
        if (error) throw new Error(stderr || error.message);
        yoloResult = JSON.parse(stdout);
      } catch (err) {
        console.error("YOLO Error:", err);
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

      const [insertResult]: any = await pool.query(
        `INSERT INTO grading_nanas (
          batch_id, foto_url, input_brix_manual, input_berat_manual_kg, confidence_score,
          yolo_raw_output, deteksi_ukuran, deteksi_warna_kulit, deteksi_kematangan_pct,
          kondisi_mahkota, kondisi_defect, grade_mutu, rekomendasi_pasar, estimasi_harga_min, estimasi_harga_max, created_at, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, NOW(), NOW())`,
        [
          batchIdNum,
          `/static/uploads/${req.file!.filename}`,
          dssInput.input_brix_manual || null,
          dssInput.input_berat_manual_kg || null,
          yoloResult.confidence_score,
          JSON.stringify(yoloResult.raw_output),
          dssInput.deteksi_ukuran,
          dssInput.deteksi_warna_kulit,
          dssInput.deteksi_kematangan_pct,
          dssInput.kondisi_mahkota,
          dssInput.kondisi_defect,
          dssOutput.grade_mutu,
          dssOutput.rekomendasi_pasar,
          dssOutput.estimasi_harga_min,
          dssOutput.estimasi_harga_max
        ]
      );

      const [gradingRows]: any = await pool.query("SELECT * FROM grading_nanas WHERE id = ?", [insertResult.insertId]);
      const grading = gradingRows[0];

      // Update Batch Recap
      const incA = dssOutput.grade_mutu === "grade_a" ? 1 : 0;
      const incB = dssOutput.grade_mutu === "grade_b" ? 1 : 0;
      const incC = dssOutput.grade_mutu === "grade_c" ? 1 : 0;
      const incR = dssOutput.grade_mutu === "reject" ? 1 : 0;
      const addedBerat = dssInput.input_berat_manual_kg || 0;

      await pool.query(
        `UPDATE batch_panen SET 
          total_buah = total_buah + 1,
          total_berat_kg = total_berat_kg + ?,
          jumlah_grade_a = jumlah_grade_a + ?,
          jumlah_grade_b = jumlah_grade_b + ?,
          jumlah_grade_c = jumlah_grade_c + ?,
          jumlah_reject = jumlah_reject + ?,
          updated_at = NOW()
        WHERE id = ?`,
        [addedBerat, incA, incB, incC, incR, batchIdNum]
      );

      const [updatedBatchRows]: any = await pool.query("SELECT * FROM batch_panen WHERE id = ?", [batchIdNum]);
      const updatedBatch = updatedBatchRows[0];

      await syncBlock(updatedBatch);

      res.status(201).json({ grading, dss_output: dssOutput, yolo_result: yoloResult });
    });
  } catch (error: any) {
    console.error(error.message || error);
    res.status(500).json({ detail: "Internal server error" });
  }
};
