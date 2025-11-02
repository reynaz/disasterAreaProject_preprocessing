# src/meshing/delaunay.py

import os
import glob
import open3d as o3d
import numpy as np
from scipy.spatial import Delaunay
from tqdm import tqdm
import json

def create_mesh_from_pcd(tile_directory, meshes_output_dir):
    """
    Belirtilen karo klasöründeki ground.pcd dosyasını okur, 
    Delaunay üçgenlemesi uygular ve sonucu DÜNYA KOORDİNATLARINDA .obj olarak kaydeder.
    """
    input_pcd_path = os.path.join(tile_directory, "ground.pcd")
    
    tile_name = os.path.basename(os.path.normpath(tile_directory))
    output_obj_path = os.path.join(meshes_output_dir, f"{tile_name}.obj")
    
    if not os.path.exists(input_pcd_path):
        return

    try:
        pcd = o3d.io.read_point_cloud(input_pcd_path)
        if not pcd.has_points():
            return

        # Orijinal dünya koordinatlarındaki noktaları al
        points = np.asarray(pcd.points)

        # --- MERKEZİLEŞTİRME KODU KALDIRILDI ---
        # center = pcd.get_center()
        # points_centered = points - center
        # --- MERKEZİLEŞTİRME KODU KALDIRILDI ---

        # Orijinal 'points' dizisinin X ve Y'sini kullan
        xy_points = points[:, :2]
        
        tri = Delaunay(xy_points)
        
        mesh = o3d.geometry.TriangleMesh()
        
        # Mesh'i merkezileştirilmiş noktalar yerine Orijinal 'points' ile oluştur
        mesh.vertices = o3d.utility.Vector3dVector(points)
        mesh.triangles = o3d.utility.Vector3iVector(tri.simplices)
        
        # (Opsiyonel) Mesh'i temizle ve normalleri hesapla (Unity için faydalı olabilir)
        mesh.remove_degenerate_triangles()
        mesh.remove_duplicated_vertices()
        mesh.compute_vertex_normals()
        
        o3d.io.write_triangle_mesh(output_obj_path, mesh)
        
        metadata_path = os.path.join(tile_directory, "metadata.json")
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata['processing_status'] = 'meshed'
                metadata['files']['ground_mesh_obj'] = output_obj_path
                
                # --- MERKEZİLEŞTİRME KODU KALDIRILDI ---
                # 'world_center' anahtarını (varsa) kaldırabilir veya dokunmayabilirsiniz
                if 'world_center' in metadata:
                    del metadata['world_center']
                # --- MERKEZİLEŞTİRME KODU KALDIRILDI ---
                
                f.seek(0)
                json.dump(metadata, f, indent=4)
                f.truncate()

    except Exception as e:
        print(f"Hata: '{tile_directory}' işlenirken bir sorun oluştu: {e}")


if __name__ == '__main__':
    processed_tiles_dir = os.path.join("data", "processed", "tiles")
    meshes_output_dir = os.path.join("data", "processed", "meshes")
    os.makedirs(meshes_output_dir, exist_ok=True)
    
    tile_folders = glob.glob(os.path.join(processed_tiles_dir, "*/"))
    
    if not tile_folders:
        print(f"Hata: '{processed_tiles_dir}' içinde işlenecek karo klasörü bulunamadı.")
    else:
        print(f"Toplam {len(tile_folders)} adet zemin nokta bulutu üzerinde dünya koordinatlı .obj ağı oluşturulacak.")
        
        desc = "Dünya Koordinatlı üçgen ağlar (.obj) oluşturuluyor"
        for tile_path in tqdm(tile_folders, desc=desc):
            create_mesh_from_pcd(tile_path, meshes_output_dir)
            
        print(f"\nTüm karolar için üçgen ağ oluşturma işlemi tamamlandı. Çıktılar '{meshes_output_dir}' klasörüne kaydedildi.")
