import open3d as o3d
import os
import numpy as np
import laspy
import matplotlib.pyplot as plt

def view_colored_point_cloud(file_path):
    # 1. Dosya Kontrolü
    if not os.path.exists(file_path):
        print(f"HATA: Dosya bulunamadı -> {file_path}")
        return

    print(f"Dosya işleniyor: {file_path}")
    
    # 2. LAZ Dosyasını Oku
    try:
        las = laspy.read(file_path)
        points = np.vstack((las.x, las.y, las.z)).transpose()
        
        # Open3D Nesnesi Oluştur
        pcd = o3d.geometry.PointCloud()
        pcd.points = o3d.utility.Vector3dVector(points)

        # --- RENKLENDİRME ALGORİTMASI ---
        print("Yükseklik haritası (Height Map) oluşturuluyor...")
        
        # Z değerlerini al (Yükseklik)
        z_values = points[:, 2]
        
        # Z değerlerini 0 ile 1 arasına sıkıştır (Normalize et)
        # Formül: (Değer - Min) / (Max - Min)
        z_min = np.min(z_values)
        z_max = np.max(z_values)
        z_norm = (z_values - z_min) / (z_max - z_min)
        
        # Matplotlib'in 'jet' (Gökkuşağı) renk haritasını kullan
        # Mavi (Alçak) -> Yeşil -> Sarı -> Kırmızı (Yüksek)
        colormap = plt.get_cmap("jet")
        
        # Normalize edilmiş yükseklik değerlerini renklere çevir
        # colormap() bize (R, G, B, Alpha) döner, biz sadece ilk 3'ünü (RGB) alıyoruz.
        colors = colormap(z_norm)[:, :3]
        
        # Renkleri nokta bulutuna ata
        pcd.colors = o3d.utility.Vector3dVector(colors)
        
        print(f"Min Yükseklik: {z_min:.2f} m (Mavi)")
        print(f"Max Yükseklik: {z_max:.2f} m (Kırmızı)")
        
    except Exception as e:
        print(f"Hata oluştu: {e}")
        return

    # 3. Görselleştirme
    print("\nPencere açılıyor...")
    
    # Koordinat eksenleri (Referans için)
    mesh_frame = o3d.geometry.TriangleMesh.create_coordinate_frame(
        size=10.0, origin=[0, 0, 0])

    o3d.visualization.draw_geometries([pcd, mesh_frame], 
                                      window_name="Height Map Viewer - ProjectWomen",
                                      width=1024,
                                      height=768)

if __name__ == "__main__":
    # Görüntülemek istediğin dosya
   # target_path = os.path.join("data", "processed_data", "RS000016_unity_scaled.laz")
    #target_path = os.path.join("data", "processed_data", "RS000016_unity_scaled.laz")
   # target_path = os.path.join("data", "processed", "tiles","tile_0_0", "raw.las")
    #target_path = os.path.join("data", "processed", "tiles","tile_1_0", "raw.las")
    target_path = os.path.join("data", "processed", "tiles","tile_0_0", "ground.las")
   # target_path = os.path.join("data", "processed", "tiles","tile_1_0", "ground.las")
   
    
    
    
    view_colored_point_cloud(target_path)
