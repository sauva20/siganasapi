import sys
import json
import os
import glob
from ultralytics import YOLO

def get_latest_model():
    # Because this script is run from backend-node, we need to go up one level to find the 'runs' folder
    base_dir = os.path.join("..", "runs", "classify", "siganas_models")
    search_path = os.path.join(base_dir, "*", "weights", "best.pt")
    models = glob.glob(search_path)
    
    if not models:
        # Try finding it in the current directory if 'runs' was created inside backend-node
        base_dir = os.path.join("runs", "classify", "siganas_models")
        search_path = os.path.join(base_dir, "*", "weights", "best.pt")
        models = glob.glob(search_path)
        
    if not models:
        # Fallback to absolute path just in case
        search_path = r"C:\laragon\www\siganasweb\runs\classify\siganas_models\*\weights\best.pt"
        models = glob.glob(search_path)
        
    if not models:
        return None
        
    # Sort by modification time, newest first
    models.sort(key=os.path.getmtime, reverse=True)
    return models[0]

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided"}))
        sys.exit(1)

    image_path = sys.argv[1]
    
    # Matikan output YOLO ultralytics agar tidak mengotori JSON output
    import logging
    logging.getLogger("ultralytics").setLevel(logging.ERROR)
    os.environ['YOLO_VERBOSE'] = 'False'
    
    model_path = get_latest_model()
    if not model_path:
        print(json.dumps({"error": "Model best.pt tidak ditemukan! Pastikan training sudah selesai."}))
        sys.exit(1)

    try:
        model = YOLO(model_path)
        
        # Jalankan inferensi dengan verbose=False
        results = model(image_path, verbose=False)
        
        # Dapatkan prediksi top 1
        top1_index = results[0].probs.top1
        confidence = float(results[0].probs.top1conf.cpu().numpy())
        class_name = results[0].names[top1_index].lower() # e.g. "grade_a", "grade_b"
        
        # Karena model klasifikasi hanya mengeluarkan kelas (Grade A/B/C/Reject),
        # kita buat data 'mock' (tiruan) untuk menyuapi DSS Engine backend kita 
        # agar seolah-olah sensor ukuran dan warna bekerja sesuai grade-nya.
        
        dss_mock = {
            "confidence_score": round(confidence * 100, 2),
            "raw_output": {"predicted_class": class_name, "confidence": confidence},
            "deteksi_ukuran": "Sedang",
            "deteksi_warna_kulit": "Kuning",
            "deteksi_kematangan_pct": 70,
            "kondisi_mahkota": "Normal",
            "kondisi_defect": "tidak ada cacat"
        }
        
        if class_name == "grade_a":
            dss_mock["deteksi_ukuran"] = "Besar"
            dss_mock["deteksi_warna_kulit"] = "Kuning"
            dss_mock["deteksi_kematangan_pct"] = 78
            dss_mock["kondisi_mahkota"] = "Sempurna"
        elif class_name == "grade_b":
            dss_mock["deteksi_ukuran"] = "Sedang"
            dss_mock["deteksi_warna_kulit"] = "Kuning"
            dss_mock["deteksi_kematangan_pct"] = 65
            dss_mock["kondisi_mahkota"] = "Normal"
        elif class_name == "grade_c":
            dss_mock["deteksi_ukuran"] = "Kecil"
            dss_mock["deteksi_warna_kulit"] = "Hijau"
            dss_mock["deteksi_kematangan_pct"] = 55
            dss_mock["kondisi_mahkota"] = "Cacat"
        elif class_name == "reject":
            dss_mock["deteksi_ukuran"] = "Kecil"
            dss_mock["deteksi_warna_kulit"] = "Coklat"
            dss_mock["deteksi_kematangan_pct"] = 30
            dss_mock["kondisi_mahkota"] = "Rusak"
            dss_mock["kondisi_defect"] = "busuk"
            
        print(json.dumps(dss_mock))
    except Exception as e:
        print(json.dumps({"error": str(e)}))
        sys.exit(1)

if __name__ == "__main__":
    main()
