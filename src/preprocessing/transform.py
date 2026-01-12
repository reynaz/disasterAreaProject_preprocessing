import os
import json
import pdal
from pathlib import Path

# ----------------------------------------------------------------------
# Ayarlar
# ----------------------------------------------------------------------
INPUT_PATH = Path("data/raw_data/RS000016.laz")
OUTPUT_DIR = Path("data/processed_data")
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_PATH = OUTPUT_DIR / "RS000016_unity_meters.laz"

# US survey foot -> metre çarpanı
FTUS_TO_M = 0.3048006096012192

# ----------------------------------------------------------------------
# Açıklama:
#
# Kaynak koordinatlar (EPSG:2225, ftUS):
#   X_src = Easting (ftUS)
#   Y_src = Northing (ftUS)
#   Z_src = Up (ftUS)                   sadece metre dönüşümü yapılır.
 
# Bu dönüşüm tek bir 4x4 matris ile yapılır:
#
# [ Xu ]   [  s    0    0    0 ] [ X ]
# [ Yu ] = [  0    s    0     0 ] [ Y ]
# [ Zu ]   [  0    0    s    0 ] [ Z ]
# [ 1  ]   [  0    0    0    1 ] [ 1 ]
#
# Burada s = FTUS_TO_M
# ----------------------------------------------------------------------

 
pipeline_json = {
    "pipeline": [
        str(INPUT_PATH),
        {
            "type": "filters.transformation",
            "matrix":"0.3048006096012192 0 0 0 0 0.3048006096012192 0 0 0 0 0.3048006096012192 0 0 0 0 1"

        },
        {
            "type": "writers.las",
            "filename": str(OUTPUT_PATH),
            "minor_version": 4,
            "dataformat_id": 6
        }
    ]
}

def main():
    if not INPUT_PATH.exists():
        raise FileNotFoundError(f"Girdi dosyası bulunamadı: {INPUT_PATH}")

    print("Girdi dosyası :", INPUT_PATH)
    print("Çıktı dosyası :", OUTPUT_PATH)
    print("Kullanılan dönüşüm matrisi:")
  

    pipeline = pdal.Pipeline(json.dumps(pipeline_json))
    count = pipeline.execute()
    print(f"İşlenen nokta sayısı: {count}")

    print("Dönüştürülmüş LAZ dosyası kaydedildi:")
    print(OUTPUT_PATH)

if __name__ == "__main__":
    main()

