import os
import glob
import numpy as np
import open3d as o3d
from tqdm import tqdm
import json

def convert_mesh_to_unity_coords(obj_path):
    """
    Bir .obj dosyasını okur, Z-Up sisteminden Y-Up sistemine çevirir.
    İşlem: (x, y, z) -> (x, z, y)
    """
    try:
        # 1. Mesh'i Oku
        mesh = o3d.io.read_triangle_mesh(obj_path)
        
        if not mesh.has_vertices():
            return False, "Mesh boş."

        # 2. Vertexleri (Noktaları) Al
        vertices = np.asarray(mesh.vertices)
        
        # 3. Eksen Değişimi (Swapping)
        # NumPy ile sütunların yerini değiştiriyoruz.
        # Eski: [X, Y, Z] -> Yeni: [X, Z, Y]
        # vertices[:, [0, 2, 1]] ifadesi 0. sütunu korur, 1. ve 2. sütunu yer değiştirir.
        vertices_unity = vertices[:, [0, 2, 1]]
        
        # Değişikliği uygula
        mesh.vertices = o3d.utility.Vector3dVector(vertices_unity)
        
        # 4. Normalleri de Çevir (Işıklandırma için şart)
        if mesh.has_vertex_normals():
            normals = np.asarray(mesh.vertex_normals)
            normals_unity = normals[:, [0, 2, 1]]
            mesh.vertex_normals = o3d.utility.Vector3dVector(normals_unity)
        else:
            mesh.compute_vertex_normals()

        # 5. Dosyayı Üzerine Yaz (veya yeni bir isimle kaydet)
        # Unity direkt bu klasörden okuyacaksa üzerine yazmak en temizidir.
        o3d.io.write_triangle_mesh(obj_path, mesh)
        
        # 6. Metadata Güncelleme (Opsiyonel ama iyi pratik)
        # Tile klasörünü bul (obj path: data/processed/meshes/tile_x_y.obj)
        # Metadata path: data/processed/tiles/tile_x_y/metadata.json
        tile_name = os.path.splitext(os.path.basename(obj_path))[0]
        tile_dir = os.path.join("data", "processed", "tiles", tile_name)
        metadata_path = os.path.join(tile_dir, "metadata.json")
        
        if os.path.exists(metadata_path):
            with open(metadata_path, 'r+') as f:
                metadata = json.load(f)
                metadata['coordinate_system']['axis'] = 'y_up (unity_ready)'
                f.seek(0)
                json.dump(metadata, f, indent=4)
                f.truncate()

        return True, "Dönüştürüldü"

    except Exception as e:
        return False, str(e)

if __name__ == '__main__':
    meshes_dir = os.path.join("data", "processed", "meshes")
    
    # Tüm .obj dosyalarını bul
    mesh_files = glob.glob(os.path.join(meshes_dir, "*.obj"))
    
    if not mesh_files:
        print("Hata: Dönüştürülecek .obj dosyası bulunamadı.")
    else:
        print(f"Toplam {len(mesh_files)} mesh Unity koordinat sistemine (Y-Up) çevriliyor...")
        
        with tqdm(total=len(mesh_files), desc="Eksen Değişimi") as pbar:
            for mesh_path in mesh_files:
                success, msg = convert_mesh_to_unity_coords(mesh_path)
                if not success:
                    print(f"Hata ({os.path.basename(mesh_path)}): {msg}")
                pbar.update(1)
                
        print("\nİşlem tamamlandı. Dosyalar Unity için hazır.")
