"""
DSS Engine — Decision Support System untuk penentuan grade dan rekomendasi pasar.

Logika penentuan grade berdasarkan parameter dari proposal:
- Grade A (Ekspor)       : Ukuran 1.4-1.6 kg, mahkota sempurna, warna kuning-oranye,
                           kematangan 75-80%, brix ≥14, tanpa defect
- Grade B (Premium Lokal): Kualitas baik tapi tidak memenuhi semua syarat ekspor
- Grade C (Standar)      : Kualitas standar untuk pasar tradisional dan industri
- Reject                 : Tidak layak jual
"""

from dataclasses import dataclass
from typing import Optional


@dataclass
class DSSInput:
    """Semua parameter input untuk DSS."""
    # Dari YOLO
    deteksi_ukuran:         Optional[str]   # "Kecil" | "Sedang" | "Besar"
    deteksi_warna_kulit:    Optional[str]   # "Hijau" | "Kuning_Kehijauan" | "Kuning" | "Oranye"
    deteksi_kematangan_pct: Optional[int]   # 0-100
    kondisi_mahkota:        Optional[str]   # "Sempurna" | "Cacat_Rusak"
    kondisi_defect:         Optional[str]   # deskripsi defect

    # Dari input manual (opsional)
    input_brix_manual:      Optional[float] = None
    input_berat_manual_kg:  Optional[float] = None


@dataclass
class DSSOutput:
    """Hasil keputusan DSS."""
    grade_mutu:         str     # "Grade A" | "Grade B" | "Grade C" | "Reject"
    rekomendasi_pasar:  str
    estimasi_harga_min: int     # Rp per kg
    estimasi_harga_max: int     # Rp per kg
    alasan:             str     # Penjelasan singkat untuk logging/debug


# Tabel harga estimasi per grade (Rp/kg) — sesuaikan dengan harga pasar terkini
HARGA_GRADE = {
    "Grade A": (8_000, 12_000),
    "Grade B": (5_000, 7_500),
    "Grade C": (2_500, 4_500),
    "Reject":  (0,     500),
}

REKOMENDASI_PASAR = {
    "Grade A": "Ekspor - Pasar Timur Tengah / Internasional",
    "Grade B": "Supermarket / Retail Premium Lokal",
    "Grade C": "Pasar Tradisional / Industri Pengolahan (IKON)",
    "Reject":  "Tidak Layak Jual - Alternatif: Pakan Ternak / Kompos",
}


def determine_grade(data: DSSInput) -> DSSOutput:
    """
    Algoritma penentuan grade multi-tier nanas.
    
    Urutan pengecekan: Reject → Grade A → Grade B → Grade C (default)
    """

    # ---- REJECT: ada cacat parah ----
    defect_str = (data.kondisi_defect or "").lower()
    has_severe_defect = any(
        keyword in defect_str
        for keyword in ["busuk", "jamur", "rusak_parah", "pecah"]
    )
    if has_severe_defect:
        return _build_output("Reject", "Kondisi defect parah: " + data.kondisi_defect)

    # Kematangan terlalu rendah (masih sangat mentah) atau busuk (terlalu matang)
    kematangan = data.deteksi_kematangan_pct
    if kematangan is not None:
        if kematangan < 40:
            return _build_output("Reject", f"Kematangan terlalu rendah: {kematangan}%")
        if kematangan > 95:
            return _build_output("Reject", f"Kematangan terlalu tinggi/busuk: {kematangan}%")

    # ---- GRADE A: Memenuhi SEMUA kriteria ekspor ----
    is_grade_a = _check_grade_a(data)
    if is_grade_a["eligible"]:
        return _build_output("Grade A", is_grade_a["reason"])

    # ---- GRADE B: Kualitas baik, tidak semua syarat A terpenuhi ----
    is_grade_b = _check_grade_b(data)
    if is_grade_b["eligible"]:
        return _build_output("Grade B", is_grade_b["reason"])

    # ---- GRADE C: Default ----
    return _build_output("Grade C", "Memenuhi standar minimum pasar tradisional/industri")


def _check_grade_a(data: DSSInput) -> dict:
    """
    Kriteria Grade A (Ekspor):
    - Mahkota sempurna
    - Warna kuning atau oranye (kematangan optimal)
    - Kematangan 75-80%
    - Brix ≥ 14 (jika data tersedia)
    - Berat 1.4-1.6 kg (jika data tersedia)
    - Tidak ada defect
    """
    reasons = []

    if data.kondisi_mahkota != "Sempurna":
        return {"eligible": False, "reason": "Mahkota tidak sempurna — gagal Grade A"}

    if data.deteksi_warna_kulit not in ("Kuning", "Oranye"):
        return {"eligible": False, "reason": f"Warna kulit {data.deteksi_warna_kulit} tidak memenuhi syarat ekspor"}

    if data.deteksi_kematangan_pct is not None:
        if not (75 <= data.deteksi_kematangan_pct <= 80):
            return {
                "eligible": False,
                "reason": f"Kematangan {data.deteksi_kematangan_pct}% di luar rentang ekspor (75-80%)"
            }

    defect_str = (data.kondisi_defect or "").lower()
    if defect_str and defect_str != "tidak ada cacat":
        return {"eligible": False, "reason": f"Ada defect: {data.kondisi_defect}"}

    # Cek brix jika data manual tersedia
    if data.input_brix_manual is not None and data.input_brix_manual < 14.0:
        return {"eligible": False, "reason": f"Brix {data.input_brix_manual} di bawah minimum ekspor (14)"}

    # Cek berat jika data manual tersedia
    if data.input_berat_manual_kg is not None:
        if not (1.4 <= data.input_berat_manual_kg <= 1.6):
            return {
                "eligible": False,
                "reason": f"Berat {data.input_berat_manual_kg}kg di luar rentang ekspor (1.4-1.6kg)"
            }

    return {"eligible": True, "reason": "Memenuhi semua kriteria mutu ekspor"}


def _check_grade_b(data: DSSInput) -> dict:
    """
    Kriteria Grade B (Premium Lokal):
    - Warna kuning_kehijauan, kuning, atau oranye
    - Kematangan 60-94%
    - Defect ringan masih diterima
    """
    if data.deteksi_warna_kulit in ("Hijau",):
        return {"eligible": False, "reason": "Warna masih hijau, tidak memenuhi Grade B"}

    if data.deteksi_kematangan_pct is not None:
        if data.deteksi_kematangan_pct < 60:
            return {"eligible": False, "reason": f"Kematangan {data.deteksi_kematangan_pct}% terlalu rendah untuk Grade B"}

    return {"eligible": True, "reason": "Memenuhi standar premium lokal"}


def _build_output(grade: str, alasan: str) -> DSSOutput:
    harga_min, harga_max = HARGA_GRADE[grade]
    return DSSOutput(
        grade_mutu=grade,
        rekomendasi_pasar=REKOMENDASI_PASAR[grade],
        estimasi_harga_min=harga_min,
        estimasi_harga_max=harga_max,
        alasan=alasan,
    )
