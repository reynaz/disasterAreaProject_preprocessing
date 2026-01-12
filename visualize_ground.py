# visualize_ground_only.py

import open3d as o3d
import numpy as np
import glob
import os
import argparse
from tqdm import tqdm
# import matplotlib.pyplot as plt # Artık matplotlib'e gerek yok

def visualize_combined_ground_pcd(tiles_base_dir, max_points_per_tile=None):
    """
    Belirtilen klasördeki tüm tile'lardan ground.pcd dosyasını okur,
    birleştirir ve tek renk (yeşil) olarak görselleştirir.

    Args:
        tiles_base_dir (str): Tüm tile klasörlerini içeren ana dizin.
        max_points_per_tile (int, optional): Her tile'dan yüklenecek maksimum nokta sayısı.
    """
    file_to_load = "ground.pcd"
    search_pattern = os.path.join(tiles_base_dir, "", file_to_load)
    pcd_files = glob.glob(search_pattern)

    if not pcd_files:
        print(f"Hata: '{search_pattern}' ile eşleşen dosya bulunamadı.")
        return

    print(f"Toplam {len(pcd_files)} adet '{file_to_load}' dosyası bulundu.")
    print("Zemin nokta bulutları birleştiriliyor...")

    combined_pcd = o3d.geometry.PointCloud()
    all_points = []

    for pcd_path in tqdm(pcd_files, desc=f"{file_to_load} dosyaları yükleniyor"):
        try:
            pcd = o3d.io.read_point_cloud(pcd_path)
            if pcd.has_points():
                points = np.asarray(pcd.points)
                if max_points_per_tile is not None and len(points) > max_points_per_tile:
                    indices = np.random.choice(len(points), max_points_per_tile, replace=False)
                    points = points[indices]
                all_points.append(points)
        except Exception as e:
            print(f"Uyarı: {pcd_path} okunurken hata oluştu: {e}")

    if not all_points:
        print("Birleştirilecek hiç zemin noktası bulunamadı.")
        return

    combined_points = np.vstack(all_points)
    print(f"Toplam {len(combined_points)} zemin noktası birleştirildi.")

    combined_pcd.points = o3d.utility.Vector3dVector(combined_points)

    # --- Görselleştirme (Tek Renk: Yeşil) ---
    print("Görselleştirici açılıyor...")
    # Tüm noktalara sabit yeşil renk ata (RGB: 0, 1, 0)
    combined_pcd.paint_uniform_color([0, 1, 0]) # Yeşil
    # --- Bitiş ---

    o3d.visualization.draw_geometries([combined_pcd], window_name="Birleştirilmiş - Sadece Zemin (Yeşil)")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tile'lardaki ground.pcd dosyalarını birleştirip yeşil renkte görselleştirir.")
    parser.add_argument("--tiles_dir", default=os.path.join("data", "processed", "tiles"),
                        help="Tile klasörlerinin bulunduğu ana dizin.")
    parser.add_argument("--max_points", type=int, default=None,
                        help="Performans için her tile'dan yüklenecek maksimum nokta sayısı (opsiyonel).")

    args = parser.parse_args()

    visualize_combined_ground_pcd(args.tiles_dir, args.max_points)
