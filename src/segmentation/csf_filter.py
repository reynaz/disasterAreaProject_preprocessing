# src/segmentation/csf_filter.py

import os
import glob
import pdal
import json
import laspy
from tqdm import tqdm

# --- AYARLAR ---
# Afet alanı için optimize edilmiş değerler
CSF_RESOLUTION = 0.5  # Kumaşın ilmek boyutu (Metre). 0.5m idealdir.
CSF_THRESHOLD = 0.5   # Zemin toleransı. 1.0m çok fazlaydı, 0.5m'ye çektik.
CSF_SMOOTH = False    # True yaparsan zemin çok düzleşir, detay kaybolabilir.

def apply_csf_with_pdal(tile_directory):
    """
    raw.las dosyasını okur, PDAL CSF uygular, 
    ground.las (Zemin) ve non_ground.las (Engel) olarak kaydeder.
    """
    # Girdi ve Çıktı yolları (LAS kullanıyoruz)
    input_las_path = os.path.join(tile_directory, "raw.las")
    ground_output_path = os.path.join(tile_directory, "ground.las")
    non_ground_output_path = os.path.join(tile_directory, "non_ground.las")

    if not os.path.exists(input_las_path):
        # Eğer las yoksa pcd deneyelim (ne olur ne olmaz)
        if os.path.exists(os.path.join(tile_directory, "raw.pcd")):
             print(f"Uyarı: {tile_directory} içinde LAS yok, PCD kullanılacak (Tavsiye edilmez).")
             input_las_path = os.path.join(tile_directory, "raw.pcd")
        else:
            return

    try:
        # 1. Pipeline Tanımı
        pipeline_json = {
            "pipeline": [
                {
                    "type": "readers.las",
                    "filename": input_las_path
                },
                {
                    "type": "filters.csf",
                    "resolution": CSF_RESOLUTION,
                    "threshold": CSF_THRESHOLD,
                    "smooth": CSF_SMOOTH,
                    "returns": "last, first, intermediate, only" 
                },
                # Zemin Noktalarını Ayır ve Yaz (Sınıf 2)
                {
                    "type": "writers.las",
                    "filename": ground_output_path,
                    "where": "Classification == 2",
                    "compression": "lazperf"
                },
                # Zemin OLMAYANLARI Ayır ve Yaz (Sınıf != 2)
                {
                    "type": "writers.las",
                    "filename": non_ground_output_path,
                    "where": "Classification != 2",
                    "compression": "lazperf"
                }
            ]
        }

        # 2. Pipeline Çalıştır
        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        pipeline.execute()

        # 3. Nokta Sayılarını Güncelle (Metadata İçin)
        # laspy ile başlık (header) okumak çok hızlıdır, tüm dosyayı taramaz.
        raw_count = 0
        ground_count = 0
        
        with laspy.open(input_las_path) as f:
            raw_count = f.header.point_count
            
        if os.path.exists(ground_output_path):
            with laspy.open(ground_output_path) as f:
                ground_count = f.header.point_count

        # 4. Metadata Güncelleme
        metadata_path = os.path.join(tile_directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r+') as f:
                metadata = json.load(f)
                
                # İşlem durumu ve istatistikler
                metadata['processing_status'] = 'segmented'
                metadata['segmentation_params'] = {
                    "resolution": CSF_RESOLUTION,
                    "threshold": CSF_THRESHOLD
                }
                metadata['point_counts'] = {
                    "raw": raw_count,
                    "ground": ground_count,
                    "non_ground": raw_count - ground_count
                }
                
                # Dosya referansları
                metadata['files']['ground_data'] = 'ground.las'
                metadata['files']['non_ground_data'] = 'non_ground.las'
                
                f.seek(0)
                json.dump(metadata, f, indent=4)
                f.truncate()

    except Exception as e:
        print(f"Hata: '{tile_directory}' işlenirken CSF hatası: {e}")

if __name__ == '__main__':
    processed_tiles_dir = os.path.join("data", "processed", "tiles")
    
    # Sadece klasörleri al
    tile_folders = [f.path for f in os.scandir(processed_tiles_dir) if f.is_dir()]

    if not tile_folders:
        print(f"Hata: '{processed_tiles_dir}' içinde işlenecek karo klasörü bulunamadı.")
    else:
        print(f"Toplam {len(tile_folders)} adet karo üzerinde PDAL CSF (Threshold: {CSF_THRESHOLD}m) çalıştırılacak.")

        for tile_path in tqdm(tile_folders, desc="Zemin tespiti (CSF)"):
            apply_csf_with_pdal(tile_path)

        print("\nTüm karolar için zemin ayıklama tamamlandı.")
