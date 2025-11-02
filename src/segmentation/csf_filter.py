# src/segmentation/csf_filter.py

import os
import glob
import pdal
import json
from tqdm import tqdm
import open3d as o3d # Nokta sayılarını okumak için

def apply_csf_with_pdal(tile_directory):
    """
    raw.pcd'yi okur, PDAL CSF uygular, sonuçları kaydeder ve
    hem raw hem de ground nokta sayılarını metadata'ya yazar.
    """
    input_pcd_path = os.path.join(tile_directory, "raw.pcd")
    ground_output_path = os.path.join(tile_directory, "ground.pcd")
    non_ground_output_path = os.path.join(tile_directory, "non_ground.pcd")

    if not os.path.exists(input_pcd_path):
        return

    raw_point_count = 0
    ground_point_count = 0

    try:
        # --- YENİ ADIM: Önce Raw Nokta Sayısını Oku ---
        try:
            raw_pcd_data = o3d.io.read_point_cloud(input_pcd_path)
            if raw_pcd_data.has_points():
                raw_point_count = len(raw_pcd_data.points)
            else:
                print(f"Uyarı: '{input_pcd_path}' boş.")
                # Boş dosyayı işlemeye gerek yok
                return
        except Exception as read_error:
            print(f"Hata: '{input_pcd_path}' okunurken hata: {read_error}")
            return # Raw dosya okunamıyorsa devam etme
        # --- Bitiş ---

        # PDAL Pipeline'ını JSON formatında tanımla
        pipeline_json = {
            "pipeline": [
                { "type": "readers.pcd", "filename": input_pcd_path },
                {
                    "type": "filters.csf",
                    "smooth": False, 
                    "threshold": 1.0,
                    "resolution": 0.3, 
                    "rigidness": 1
                },
                { "type": "writers.pcd", "filename": ground_output_path, "where": "Classification == 2" },
                { "type": "writers.pcd", "filename": non_ground_output_path, "where": "Classification != 2" }
            ]
        }

        # PDAL pipeline'ını oluştur ve çalıştır
        pipeline = pdal.Pipeline(json.dumps(pipeline_json))
        pipeline.execute()

        # Ground Nokta Sayısını Hesaplama
        if os.path.exists(ground_output_path):
            try:
                ground_pcd_data = o3d.io.read_point_cloud(ground_output_path)
                if ground_pcd_data.has_points():
                    ground_point_count = len(ground_pcd_data.points)
            except Exception as read_error:
                print(f"Uyarı: '{ground_output_path}' okunurken hata: {read_error}")

        # Metadata.json dosyasını güncelle
        metadata_path = os.path.join(tile_directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata['processing_status'] = 'segmented'
                # --- GÜNCELLEME: Her iki sayıyı da ekle ---
                metadata['raw_point_count'] = raw_point_count
                metadata['ground_point_count'] = ground_point_count
                # --- Bitiş ---
                metadata['files']['ground_pcd'] = 'ground.pcd'
                metadata['files']['non_ground_pcd'] = 'non_ground.pcd'
                f.seek(0)
                json.dump(metadata, f, indent=4)
                f.truncate()

    except Exception as e:
        import traceback
        print(f"Hata: '{tile_directory}' işlenirken bir sorun oluştu: {e}")
        traceback.print_exc()

if __name__ == '__main__':
    processed_tiles_dir = os.path.join("data", "processed", "tiles")
    tile_folders = glob.glob(os.path.join(processed_tiles_dir, "*/"))

    if not tile_folders:
        print(f"Hata: '{processed_tiles_dir}' içinde işlenecek karo klasörü bulunamadı.")
    else:
        print(f"Toplam {len(tile_folders)} adet karo üzerinde PDAL ile zemin tespiti yapılacak.")

        for tile_path in tqdm(tile_folders, desc="Zemin tespiti yapılıyor"):
            apply_csf_with_pdal(tile_path)

        print("\nTüm karolar için zemin ayıklama işlemi tamamlandı.")
