"""
YOLO Engine — Inferensi gambar menggunakan YOLOv11.

Menggunakan library Ultralytics. Model dimuat sekali saat startup
menggunakan pola Singleton agar tidak reload setiap request.
"""

import logging
from pathlib import Path
from typing import Optional

from app.core.config import settings
from app.services.dss_engine import DSSInput, DSSOutput, determine_grade

logger = logging.getLogger(__name__)

# Singleton: model YOLO dimuat satu kali
_model = None


def load_model():
    """
    Load model YOLOv11 dari file weights.
    Dipanggil satu kali saat aplikasi startup.
    """
    global _model

    weights_path = Path(settings.YOLO_WEIGHTS_PATH)
    if not weights_path.exists():
        logger.warning(
            f"File weights tidak ditemukan: {weights_path}. "
            "YOLO engine berjalan dalam mode DUMMY (untuk development)."
        )
        return

    try:
        from ultralytics import YOLO
        _model = YOLO(str(weights_path))
        logger.info(f"Model YOLO berhasil dimuat dari: {weights_path}")
    except Exception as e:
        logger.error(f"Gagal memuat model YOLO: {e}")


def _dummy_prediction(image_path: str) -> dict:
    """
    Dummy prediction untuk development/testing sebelum model tersedia.
    Mengembalikan data simulasi yang realistis.
    """
    import random
    logger.debug(f"[DUMMY MODE] Simulasi inferensi untuk: {image_path}")

    return {
        "confidence_score":         round(random.uniform(0.82, 0.97), 4),
        "deteksi_ukuran":           random.choice(["Kecil", "Sedang", "Besar"]),
        "deteksi_warna_kulit":      random.choice(["Kuning_Kehijauan", "Kuning", "Oranye"]),
        "deteksi_kematangan_pct":   random.randint(65, 85),
        "kondisi_mahkota":          random.choice(["Sempurna", "Sempurna", "Cacat_Rusak"]),
        "kondisi_defect":           "Tidak Ada Cacat",
        "raw_output":               {"mode": "dummy", "note": "Ganti dengan model .pt asli"},
    }


def _parse_yolo_output(results) -> dict:
    """
    Parse output raw dari Ultralytics YOLO ke format internal.
    
    TODO: Sesuaikan mapping ini dengan label yang digunakan saat training.
    Label yang diharapkan dari model:
    - ukuran: ['kecil', 'sedang', 'besar']
    - warna: ['hijau', 'kuning_kehijauan', 'kuning', 'oranye']
    - kematangan: direpresentasikan sebagai class atau confidence
    - mahkota: ['sempurna', 'cacat_rusak']
    - defect: berbagai class defect
    """
    # Ambil hasil prediksi terbaik (confidence tertinggi)
    if not results or len(results) == 0:
        return _dummy_prediction("fallback")

    result = results[0]
    boxes = result.boxes

    if boxes is None or len(boxes) == 0:
        return _dummy_prediction("no_detection")

    # Ambil box dengan confidence tertinggi
    best_idx = boxes.conf.argmax().item()
    confidence = float(boxes.conf[best_idx].item())
    class_id = int(boxes.cls[best_idx].item())
    class_name = result.names.get(class_id, "unknown")

    # Raw output untuk audit
    raw_output = {
        "detected_class": class_name,
        "class_id": class_id,
        "confidence": confidence,
        "total_detections": len(boxes),
    }

    # TODO: Map class_name ke atribut sesuai label training
    # Contoh mapping sementara — sesuaikan setelah training selesai:
    return {
        "confidence_score":         round(confidence, 4),
        "deteksi_ukuran":           "Sedang",      # TODO: parse dari class_name
        "deteksi_warna_kulit":      "Kuning",       # TODO: parse dari class_name
        "deteksi_kematangan_pct":   75,             # TODO: parse dari class_name
        "kondisi_mahkota":          "Sempurna",     # TODO: parse dari class_name
        "kondisi_defect":           "Tidak Ada Cacat",
        "raw_output":               raw_output,
    }


def run_inference(
    image_path: str,
    input_brix_manual: Optional[float] = None,
    input_berat_manual_kg: Optional[float] = None,
) -> tuple[dict, DSSOutput]:
    """
    Jalankan inferensi YOLO + DSS untuk satu gambar nanas.
    
    Args:
        image_path: Path lengkap ke file gambar yang sudah disimpan.
        input_brix_manual: Data brix dari refraktometer (opsional).
        input_berat_manual_kg: Data berat dari timbangan (opsional).
    
    Returns:
        Tuple: (yolo_result_dict, dss_output)
    """
    # --- Step 1: Inferensi YOLO ---
    if _model is None:
        yolo_result = _dummy_prediction(image_path)
    else:
        try:
            results = _model.predict(
                source=image_path,
                conf=settings.YOLO_CONFIDENCE_THRESHOLD,
                device=settings.YOLO_DEVICE,
                verbose=False,
            )
            yolo_result = _parse_yolo_output(results)
        except Exception as e:
            logger.error(f"Error saat inferensi YOLO: {e}")
            yolo_result = _dummy_prediction(image_path)

    # --- Step 2: DSS untuk menentukan grade dan rekomendasi pasar ---
    dss_input = DSSInput(
        deteksi_ukuran=yolo_result.get("deteksi_ukuran"),
        deteksi_warna_kulit=yolo_result.get("deteksi_warna_kulit"),
        deteksi_kematangan_pct=yolo_result.get("deteksi_kematangan_pct"),
        kondisi_mahkota=yolo_result.get("kondisi_mahkota"),
        kondisi_defect=yolo_result.get("kondisi_defect"),
        input_brix_manual=input_brix_manual,
        input_berat_manual_kg=input_berat_manual_kg,
    )
    dss_output = determine_grade(dss_input)

    logger.info(
        f"Inferensi selesai | Grade: {dss_output.grade_mutu} | "
        f"Confidence: {yolo_result.get('confidence_score')} | "
        f"Alasan: {dss_output.alasan}"
    )

    return yolo_result, dss_output
