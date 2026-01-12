import json
import pdal
import subprocess
from pathlib import Path

# ---------------------------
# Yapılandırma
# ---------------------------
INPUT = Path("data/processed_data/RS000016_unity_meters.laz")
OUTPUT = Path("data/processed_data/RS000016_unity_scaled.laz")

# Unity için ölçek (offset zorunlu, scale opsiyonel)
SCALE = 1.0  # 1.0 sadece offset yapar

def main():
    if not INPUT.exists():
        raise FileNotFoundError(f"Girdi dosyası yok: {INPUT}")

    # ---------------------------
    # 1) PDAL info --stats ile bbox bilgisi al
    # ---------------------------
    meta_raw = subprocess.check_output(
        ["pdal", "info", "--stats", str(INPUT)],
        text=True
    )
    meta = json.loads(meta_raw)

    if "stats" not in meta:
        print("meta dict keys:", meta.keys())
        raise KeyError("meta['stats'] bulunamadı")

    bbox = meta["stats"]["bbox"]["native"]["bbox"]

    minx, maxx = bbox["minx"], bbox["maxx"]
    miny, maxy = bbox["miny"], bbox["maxy"]
    minz, maxz = bbox["minz"], bbox["maxz"]

    # ---------------------------
    # 2) Global origin = bbox merkezi
    # ---------------------------
    origin_x = (minx + maxx) / 2.0
    origin_y = (miny + maxy) / 2.0
    origin_z = (minz + maxz) / 2.0

    print("\nGLOBAL ORIGIN (merkez değerleri):")
    print("origin_x =", origin_x)
    print("origin_y =", origin_y)
    print("origin_z =", origin_z)
    print("Scale factor =", SCALE)

    # ---------------------------
    # 3) Offset + scale matrisi
    # ---------------------------
    ox = -origin_x * SCALE
    oy = -origin_y * SCALE
    oz = -origin_z * SCALE

    matrix = (
        f"{SCALE} 0 0 {ox}, "
        f"0 {SCALE} 0 {oy}, "
        f"0 0 {SCALE} {oz}, "
        "0 0 0 1"
    )

    print("\nKULLANILAN 4x4 MATRIX:")
    print(matrix)

    # ---------------------------
    # 4) PDAL Pipeline
    # ---------------------------
    pipeline_json = {
        "pipeline": [
            str(INPUT),
            {
                "type": "filters.transformation",
                "matrix": "1.0 0 0 -1835920.03  0 1.0 0 -613050.27  0 0 1.0 -83.71  0 0 0 1.0"

            },
            {
                "type": "writers.las",
                "filename": str(OUTPUT),
                "minor_version": 4,
                "dataformat_id": 6
            }
        ]
    }

    pipeline = pdal.Pipeline(json.dumps(pipeline_json))
    count = pipeline.execute()

    print("\nİşlenen nokta sayısı:", count)
    print("Yeni ölçeklendirilmiş LAZ dosyası kaydedildi:")
    print(OUTPUT)


if __name__ == "__main__":
    main()

