import os
import json
import laspy 
import numpy as np 
import open3d as o3d
from tqdm import tqdm

# --- AYARLAR VE SABİTLER ---
TILE_SIZE = 100.0
OVERLAP = 10.0

# PDAL aşamasında kullandığımız OFFSET değerleri (Bunları çıkarmıştık)
# Bu değerler, Local -> Global dönüşümü için metadata'ya eklenecek.
GLOBAL_OFFSET_X = 1835920.03
GLOBAL_OFFSET_Y = 613050.27
GLOBAL_OFFSET_Z = 83.71

def convert_las_to_pcd(las_path, pcd_path):
    """
    Bir LAS dosyasını okur ve Open3D kullanarak PCD formatına dönüştürür.
    """
    try:
        las = laspy.read(las_path)
        # Noktaların sadece X, Y, Z koordinatlarını bir NumPy dizisine al
        points = np.vstack((las.x, las.y, las.z)).transpose()
        
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        o3d.io.write_point_cloud(pcd_path, pcd, write_ascii=False)
        return True
        
    except Exception as e:
        print(f"Hata: {las_path} dosyası PCD'ye dönüştürülürken hata oluştu: {e}")
        return False
            
def create_files_from_las(input_las_path, output_dir):
    print(f"'{input_las_path}' dosyası işleniyor...")
    
    try: 
        las_file = laspy.read(input_las_path)
        header = las_file.header
    except Exception as e:
        print(f"Hata: {input_las_path} dosyası okunamadı: {e}")
        return
     
    # Veri sınırları (Bunlar artık offsetlenmiş, yerel koordinatlardır)
    x_min, y_min, _ = header.min
    x_max, y_max, _ = header.max
    print(f"Yerel Veri Sınırları (Local): X [{x_min:.2f}, {x_max:.2f}], Y [{y_min:.2f}, {y_max:.2f}]")
    
    # Tile ızgarası oluşturma
    step = TILE_SIZE - OVERLAP
    x_steps = np.arange(x_min, x_max, step)   
    y_steps = np.arange(y_min, y_max, step)

    total_tiles = len(x_steps) * len(y_steps)
    print(f"Toplam {total_tiles} olası karo taranacak.") 
    
    tile_count = 0
    with tqdm(total=total_tiles, desc="Karolar oluşturuluyor") as pbar:
        for i, x in enumerate(x_steps):
            for j, y in enumerate(y_steps):
                pbar.update(1)
                
                # 1. Yerel (Local) Sınırlar (Unity'nin kullanacağı)
                tile_x_min, tile_x_max = x, x + TILE_SIZE
                tile_y_min, tile_y_max = y, y + TILE_SIZE

                # 2. Global (Orijinal) Sınırlar (Metadata için hesaplanır)
                global_bounds = {
                    "x_min": tile_x_min + GLOBAL_OFFSET_X,
                    "x_max": tile_x_max + GLOBAL_OFFSET_X,
                    "y_min": tile_y_min + GLOBAL_OFFSET_Y,
                    "y_max": tile_y_max + GLOBAL_OFFSET_Y
                }

                # 3. Nokta Filtreleme (Yerel koordinatlara göre)
                points_in_tile_mask = (
                    (las_file.x >= tile_x_min) & (las_file.x < tile_x_max) &
                    (las_file.y >= tile_y_min) & (las_file.y < tile_y_max)
                )
                
                points_data = las_file.points[points_in_tile_mask]

                if len(points_data) == 0:
                    continue
                
                tile_count += 1
                # İsimlendirme: Hem index hem de yerel koordinat bilgisini içerse iyi olur
                tile_name = f"tile_{i}_{j}" 
                tile_dir = os.path.join(output_dir, tile_name)
                os.makedirs(tile_dir, exist_ok=True)

                # 4. Dosyaları Kaydetme
                tile_las_path = os.path.join(tile_dir, "raw.las")
                new_las = laspy.LasData(header)
                new_las.points = points_data
                new_las.write(tile_las_path)
                
                tile_pcd_path = os.path.join(tile_dir, "raw.pcd")
                convert_las_to_pcd(tile_las_path, tile_pcd_path)
                
                # 5. Zenginleştirilmiş Metadata (KRİTİK BÖLÜM)
                metadata = {
                    "tile_name": tile_name,
                    "grid_index": {"i": i, "j": j},
                    "source_file": os.path.basename(input_las_path),
                    "point_count": len(points_data),
                    "coordinate_system": {
                        "type": "local_centered",
                        "unit": "meters",
                        "axis": "z_up" # Unity'ye atarken y_up olacak
                    },
                    "offset_values": {
                        "x": GLOBAL_OFFSET_X,
                        "y": GLOBAL_OFFSET_Y,
                        "z": GLOBAL_OFFSET_Z
                    },
                    "bounds": {
                        "local": {
                            "x_min": tile_x_min, "y_min": tile_y_min,
                            "x_max": tile_x_max, "y_max": tile_y_max
                        },
                        "global": global_bounds
                    },
                    "files": {
                        "las": "raw.las",
                        "pcd": "raw.pcd"
                    }
                }
                
                metadata_path = os.path.join(tile_dir, "metadata.json")
                with open(metadata_path, 'w') as f:
                    json.dump(metadata, f, indent=4)

    print(f"\nİşlem tamamlandı. Toplam {tile_count} adet dolu karo oluşturuldu.")

if __name__ == '__main__':
    # Girdi dosyasını önceki adımda oluşturduğumuz centered_zup dosyası olarak güncelledik
    input_file = "RS000016_unity_scaled.laz" 
    
    raw_data_path = os.path.join("data", "processed_data", input_file)
    processed_data_path = os.path.join("data", "processed", "tiles")

    os.makedirs(processed_data_path, exist_ok=True)

    if os.path.exists(raw_data_path):
        create_files_from_las(raw_data_path, processed_data_path)
    else:
        print(f"Hata: Girdi dosyası bulunamadı -> {raw_data_path}")
