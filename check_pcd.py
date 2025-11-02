# scirpts/check_pcd.py
# Kullanım: python3 scirpts/check_pcd.py [dosya_yolu]
# Örnek:
# python3 scirpts/check_pcd.py data/processed/tile_0000_0002/ground.pcd
# python3 scirpts/check_pcd.py data/processed/tile_0000_0002/raw.pcd

import open3d as o3d
import numpy as np
import sys

if len(sys.argv) < 2:
    print("HATA: Görselleştirilecek .pcd dosyasının yolunu belirtmelisiniz.")
    print("Örnek: python3 scirpts/check_pcd.py data/processed/tile_0000_0002/ground.pcd")
    sys.exit()

pcd_path = sys.argv[1]

try:
    pcd = o3d.io.read_point_cloud(pcd_path)
    if not pcd.has_points():
        print(f"HATA: {pcd_path} dosyası boş veya okunamadı.")
    else:
        point_count = len(pcd.points)
        print(f"'{pcd_path}' başarıyla yüklendi.")
        print(f"Toplam {point_count} nokta bulundu.")
        
        if point_count < 1000:
            print("UYARI: Nokta sayısı çok düşük. Bu, seyrek haritanın nedenini açıklayabilir.")
            
        print("\nGörselleştirme penceresi açılıyor...")
        print("Kapatmak için pencereye odaklanıp 'q' tuşuna basın.")
        o3d.visualization.draw_geometries([pcd])
        
except Exception as e:
    print(f"Bir hata oluştu: {e}")
