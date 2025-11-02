import os
import json
import laspy 
import numpy as np 
import open3d as o3d
from  tqdm import tqdm


TILE_SIZE = 100.0
OVERLAP = 10.0



def convert_las_to_pcd(las_path, pcd_path):
    """
    Bir LAS dosyasını okur ve Open3D kullanarak PCD formatına dönüştürür.
    Bu, PCL uyumluluğu için gereklidir.
    
    YENİ YÖNTEM: Önce laspy ile veriyi oku, sonra NumPy dizisi olarak Open3D'ye ver.
    Bu, Open3D'nin LAS desteği olmasa bile çalışmasını sağlar.

    Args:
        las_path (str): Girdi .las dosyasının yolu.
        pcd_path (str): Çıktı .pcd dosyasının yolu.
    
    Returns:
        bool: Dönüşüm başarılı ise True, değilse False.
    """
    try:
        # 1. LAS dosyasını laspy ile oku
        las = laspy.read(las_path)
        
        # 2. Noktaların sadece X, Y, Z koordinatlarını bir NumPy dizisine al
        points = np.vstack((las.x, las.y, las.z)).transpose()
        
        # 3. NumPy dizisinden bir Open3D PointCloud nesnesi oluştur
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)
        
        # 4. PCD dosyasına yaz
        o3d.io.write_point_cloud(pcd_path, pcd, write_ascii=False)
        return True
        
    except Exception as e:
        print(f"Hata: {las_path} dosyası PCD'ye dönüştürülürken hata oluştu: {e}")
        return False
    
            
def create_files_from_las(input_las_path, output_dir):
    """
    Büyük bir LAS dosyasını, belirlenen boyut ve bindirme payı ile karolara böler.
    Her bir karo için .las, .pcd ve metadata.json dosyaları oluşturur.

    Args:
        input_las_path (str): İşlenecek ham .las dosyasının yolu.
        output_dir (str): İşlenmiş karoların kaydedileceği ana dizin.
    """
    print(f"'{input_las_path}' dosyası işleniyor...")
    
    # step1: open raw las. file and read header info
    try: 
        las_file = laspy.read(input_las_path)
        header = las_file.header
    except Exception as e:
        print(f"Hata: {input_las_path} dosyası okunamadı: {e}")
        return
     
    # step2: calculate bounding box
    x_min, y_min, _ = header.min
    x_max, y_max, _ = header.max
    print(f"Veri sınırları: X [{x_min:.2f}, {x_max:.2f}], Y [{y_min:.2f}, {y_max:.2f}]")
    
    # step3: make tile grids
    step = TILE_SIZE - OVERLAP
    x_steps = np.arange(x_min, x_max, step)   
    y_steps = np.arange(y_min, y_max, step)

    total_tiles = len(x_steps) * len(y_steps)
    print(f"Toplam {total_tiles} olası karo oluşturulacak. Boyut: {TILE_SIZE}m, overlap : {OVERLAP}m") 
    
    tile_count = 0
    with tqdm(total=total_tiles, desc="karolar oluşturuluyor") as pbar:
        for i, x in enumerate(x_steps):
            for j, y in enumerate(y_steps):
                pbar.update(1)
                
                # 4. Her bir karonun sınırlarını belirle
                tile_x_min, tile_x_max = x, x + TILE_SIZE
                tile_y_min, tile_y_max = y, y + TILE_SIZE

                # 5. Sınırlar içindeki noktaları filtrele
                # Belleği verimli kullanmak için NumPy boolean indekleme kullanılır
                points_in_tile_mask = (
                    (las_file.x >= tile_x_min) & (las_file.x < tile_x_max) &
                    (las_file.y >= tile_y_min) & (las_file.y < tile_y_max)
                )
                
                points_data = las_file.points[points_in_tile_mask]

                # Eğer karoda hiç nokta yoksa bu karoyu atla
                if len(points_data) == 0:
                    continue
                
                tile_count += 1
                tile_name = f"tile_{i:04d}_{j:04d}"
                tile_dir = os.path.join(output_dir, tile_name)
                os.makedirs(tile_dir, exist_ok=True)

                # 6. Yeni karo için LAS dosyası oluştur ve kaydet
                tile_las_path = os.path.join(tile_dir, "raw.las")
                new_las = laspy.LasData(header)
                new_las.points = points_data
                new_las.write(tile_las_path)
                
                # 7. Oluşturulan LAS dosyasını PCD formatına dönüştür
                tile_pcd_path = os.path.join(tile_dir, "raw.pcd")
                convert_las_to_pcd(tile_las_path, tile_pcd_path)
                
                # 8. Metadata dosyasını oluştur
                metadata = {
                    "tile_name": tile_name,
                    "source_file": os.path.basename(input_las_path),
                    "bounds": {
                        "x_min": tile_x_min, "y_min": tile_y_min,
                        "x_max": tile_x_max, "y_max": tile_y_max
                    },
                    "point_count": len(points_data),
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
    # --- Bu bölüm script'i doğrudan çalıştırmak içindir ---
    # Proje ana dizininde olduğunuzu varsayarak yolları ayarlayın
    
    # KULLANIM:
    # 1. 'data/raw/' klasörüne işlenecek .las dosyanızı koyun.
    # 2. Aşağıdaki 'input_file' değişkenini dosya adınızla güncelleyin.
    
    input_file = "RS000016.laz"  # Örnek dosya adı
    
    raw_data_path = os.path.join("data", "raw_data", input_file)
    processed_data_path = os.path.join("data", "processed", "tiles")

    # Çıktı dizininin var olduğundan emin ol
    os.makedirs(processed_data_path, exist_ok=True)

    if os.path.exists(raw_data_path):
        create_files_from_las(raw_data_path, processed_data_path)
    else:
        print(f"Hata: Girdi dosyası bulunamadı -> {raw_data_path}")
        print("Lütfen 'data/raw/' klasörüne bir .las dosyası koyduğunuzdan ve 'input_file' değişkenini güncellediğinizden emin olun.")

    
          
