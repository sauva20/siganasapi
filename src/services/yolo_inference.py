import sys
import json
import logging
from pathlib import Path
import random

# Disable ultralytics logging to prevent messing up stdout
logging.getLogger("ultralytics").setLevel(logging.ERROR)

def dummy_prediction(image_path: str) -> dict:
    return {
        "confidence_score": round(random.uniform(0.82, 0.97), 4),
        "deteksi_ukuran": random.choice(["Kecil", "Sedang", "Besar"]),
        "deteksi_warna_kulit": random.choice(["Kuning_Kehijauan", "Kuning", "Oranye"]),
        "deteksi_kematangan_pct": random.randint(65, 85),
        "kondisi_mahkota": random.choice(["Sempurna", "Sempurna", "Cacat_Rusak"]),
        "kondisi_defect": "Tidak Ada Cacat",
        "raw_output": {"mode": "dummy", "note": "Ganti dengan model .pt asli"}
    }

def main():
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No image path provided"}))
        sys.exit(1)
        
    image_path = sys.argv[1]
    
    # Optional: If you want to use the actual model, uncomment below.
    # try:
    #     from ultralytics import YOLO
    #     model = YOLO("weights/yolov11_nanas.pt")
    #     results = model.predict(source=image_path, conf=0.5, device="cpu", verbose=False)
    #     # parse results...
    # except Exception as e:
    #     result = dummy_prediction(image_path)
    
    # Using dummy prediction for now as fallback
    result = dummy_prediction(image_path)
    
    print(json.dumps(result))

if __name__ == "__main__":
    main()
