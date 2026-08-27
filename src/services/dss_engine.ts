export interface DSSInput {
  deteksi_ukuran?: string;
  deteksi_warna_kulit?: string;
  deteksi_kematangan_pct?: number;
  kondisi_mahkota?: string;
  kondisi_defect?: string;
  input_brix_manual?: number;
  input_berat_manual_kg?: number;
}

export interface DSSOutput {
  grade_mutu: "grade_a" | "grade_b" | "grade_c" | "reject";
  rekomendasi_pasar: string;
  estimasi_harga_min: number;
  estimasi_harga_max: number;
  alasan: string;
}

const HARGA_GRADE = {
  grade_a: { min: 8000, max: 12000 },
  grade_b: { min: 5000, max: 7500 },
  grade_c: { min: 2500, max: 4500 },
  reject: { min: 0, max: 500 },
};

const REKOMENDASI_PASAR = {
  grade_a: "Ekspor - Pasar Timur Tengah / Internasional",
  grade_b: "Supermarket / Retail Premium Lokal",
  grade_c: "Pasar Tradisional / Industri Pengolahan (IKON)",
  reject: "Tidak Layak Jual - Alternatif: Pakan Ternak / Kompos",
};

export const determineGrade = (data: DSSInput): DSSOutput => {
  const defectStr = (data.kondisi_defect || "").toLowerCase();
  const severeDefects = ["busuk", "jamur", "rusak_parah", "pecah"];
  const hasSevereDefect = severeDefects.some(d => defectStr.includes(d));

  if (hasSevereDefect) {
    return buildOutput("reject", "Kondisi defect parah: " + data.kondisi_defect);
  }

  if (data.deteksi_kematangan_pct !== undefined) {
    if (data.deteksi_kematangan_pct < 40) {
      return buildOutput("reject", `Kematangan terlalu rendah: ${data.deteksi_kematangan_pct}%`);
    }
    if (data.deteksi_kematangan_pct > 95) {
      return buildOutput("reject", `Kematangan terlalu tinggi/busuk: ${data.deteksi_kematangan_pct}%`);
    }
  }

  const checkA = checkGradeA(data);
  if (checkA.eligible) return buildOutput("grade_a", checkA.reason);

  const checkB = checkGradeB(data);
  if (checkB.eligible) return buildOutput("grade_b", checkB.reason);

  return buildOutput("grade_c", "Memenuhi standar minimum pasar tradisional/industri");
};

const checkGradeA = (data: DSSInput): { eligible: boolean; reason: string } => {
  if (data.kondisi_mahkota !== "sempurna" && data.kondisi_mahkota !== "Sempurna") {
    return { eligible: false, reason: "Mahkota tidak sempurna — gagal Grade A" };
  }

  const validColors = ["Kuning", "Oranye", "kuning", "oranye"];
  if (data.deteksi_warna_kulit && !validColors.includes(data.deteksi_warna_kulit)) {
    return { eligible: false, reason: `Warna kulit ${data.deteksi_warna_kulit} tidak memenuhi syarat ekspor` };
  }

  if (data.deteksi_kematangan_pct !== undefined) {
    if (data.deteksi_kematangan_pct < 75 || data.deteksi_kematangan_pct > 80) {
      return { eligible: false, reason: `Kematangan ${data.deteksi_kematangan_pct}% di luar rentang ekspor (75-80%)` };
    }
  }

  const defectStr = (data.kondisi_defect || "").toLowerCase();
  if (defectStr && defectStr !== "tidak ada cacat") {
    return { eligible: false, reason: `Ada defect: ${data.kondisi_defect}` };
  }

  if (data.input_brix_manual !== undefined && data.input_brix_manual < 14.0) {
    return { eligible: false, reason: `Brix ${data.input_brix_manual} di bawah minimum ekspor (14)` };
  }

  if (data.input_berat_manual_kg !== undefined) {
    if (data.input_berat_manual_kg < 1.4 || data.input_berat_manual_kg > 1.6) {
      return { eligible: false, reason: `Berat ${data.input_berat_manual_kg}kg di luar rentang ekspor (1.4-1.6kg)` };
    }
  }

  return { eligible: true, reason: "Memenuhi semua kriteria mutu ekspor" };
};

const checkGradeB = (data: DSSInput): { eligible: boolean; reason: string } => {
  if (data.deteksi_warna_kulit === "Hijau" || data.deteksi_warna_kulit === "hijau") {
    return { eligible: false, reason: "Warna masih hijau, tidak memenuhi Grade B" };
  }

  if (data.deteksi_kematangan_pct !== undefined && data.deteksi_kematangan_pct < 60) {
    return { eligible: false, reason: `Kematangan ${data.deteksi_kematangan_pct}% terlalu rendah untuk Grade B` };
  }

  return { eligible: true, reason: "Memenuhi standar premium lokal" };
};

const buildOutput = (grade: "grade_a" | "grade_b" | "grade_c" | "reject", alasan: string): DSSOutput => {
  const harga = HARGA_GRADE[grade];
  return {
    grade_mutu: grade,
    rekomendasi_pasar: REKOMENDASI_PASAR[grade],
    estimasi_harga_min: harga.min,
    estimasi_harga_max: harga.max,
    alasan,
  };
};
