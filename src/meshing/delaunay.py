# src/meshing/delaunay_mesh.py

import os
import glob
import open3d as o3d
import numpy as np
import laspy
from scipy.spatial import Delaunay
from tqdm import tqdm
import json

def create_mesh_from_las(tile_directory, meshes_output_dir):
    """
    Tile klasöründeki ground.las dosyasını okur, Delaunay uygular
    ve sonucu 'data/processed/meshes' altına kaydeder.
    """
    # Girdi: Tile içindeki ground.las
    input_las_path = os.path.join(tile_directory, "ground.las")
    
    # Tile ismini klasör yolundan al (Örn: tile_0_0)
    tile_name = os.path.basename(os.path.normpath(tile_directory))
    
    # Çıktı: Merkezi meshes klasörüne kaydet
    output_obj_filename = f"{tile_name}.obj"
    output_obj_path = os.path.join(meshes_output_dir, output_obj_filename)
    
    if not os.path.exists(input_las_path):
        return False, "ground.las bulunamadı"

    try:
        # 1. LAS Dosyasını Oku
        las = laspy.read(input_las_path)
        
        if len(las.points) < 3:
            return False, "Yetersiz nokta sayısı (<3)"

        # 2. Noktaları Al (Koordinatları DEĞİŞTİRME - Offset zaten yapıldı)
        # points_3d: [x, y, z] (Z-Up sisteminde)
        points_3d = np.vstack((las.x, las.y, las.z)).transpose()
        
        # 3. Delaunay Üçgenlemesi (XY düzleminde - 2.5D)
        points_2d = points_3d[:, :2] 
        tri = Delaunay(points_2d)
        
        # 4. Open3D Mesh Oluşturma
        mesh = o3d.geometry.TriangleMesh()
        mesh.vertices = o3d.utility.Vector3dVector(points_3d)
        mesh.triangles = o3d.utility.Vector3iVector(tri.simplices)
        
        # 5. Mesh Optimizasyonu
        mesh.compute_vertex_normals()
        
        # 6. OBJ Olarak Kaydet
        o3d.io.write_triangle_mesh(output_obj_path, mesh)
        
        # 7. Metadata Güncelleme (Tile klasöründeki json güncellenir)
        metadata_path = os.path.join(tile_directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata['processing_status'] = 'meshed'
                # Mesh dosyasının yolunu relative (göreceli) veya tam yol olarak kaydedebiliriz
                # Burada dosya adını ve bulunduğu klasörü belirtiyoruz
                metadata['files']['mesh_obj'] = {
                    "filename": output_obj_filename,
                    "path": f"../../meshes/{output_obj_filename}" # Tile klasöründen çıkıp meshes'a git
                }
                metadata['mesh_info'] = {
                    "vertex_count": len(mesh.vertices),
                    "triangle_count": len(mesh.triangles)
                }
                f.seek(0)
                json.dump(metadata, f, indent=4)
                f.truncate()
                
        return True, f"Mesh oluşturuldu: {output_obj_filename}"
                
    except Exception as e:
        return False, str(e)


if __name__ == '__main__':
    # Klasör Yolları
    processed_tiles_dir = os.path.join("data", "processed", "tiles")
    meshes_output_dir = os.path.join("data", "processed", "meshes")
    
    # Çıktı klasörünü oluştur
    os.makedirs(meshes_output_dir, exist_ok=True)
    
    # Tile klasörlerini bul
    tile_folders = [f.path for f in os.scandir(processed_tiles_dir) if f.is_dir()]

    if not tile_folders:
        print(f"Hata: '{processed_tiles_dir}' içinde işlenecek karo klasörü bulunamadı.")
    else:
        print(f"Toplam {len(tile_folders)} karo işlenecek. Çıktılar '{meshes_output_dir}' klasörüne kaydedilecek.")
        
        with tqdm(total=len(tile_folders), desc="Mesh Oluşturuluyor") as pbar:
            for tile_path in tile_folders:
                success, msg = create_mesh_from_las(tile_path, meshes_output_dir)
                pbar.update(1)
        
        print(f"\nİşlem tamamlandı. Lütfen '{meshes_output_dir}' klasörünü kontrol edin.")
