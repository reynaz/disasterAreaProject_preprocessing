import open3d as o3d
import sys

if len(sys.argv) < 2:
    print("Kullanım: python visualize_mesh.py <dosya_yolu.ply>")
else:
    mesh_path = sys.argv[1]
    print(f"{mesh_path} dosyası yükleniyor...")
    
    # Mesh dosyasını oku
    mesh = o3d.io.read_triangle_mesh(mesh_path)
    
    if not mesh.has_vertices():
        print("Hata: Mesh dosyası boş veya okunamadı.")
    else:
        # Mesh'i görselleştir
        print("Görselleştirici açılıyor. Kapatmak için pencereyi kapatın veya 'Q' tuşuna basın.")
        vis = o3d.visualization.Visualizer()
        vis.create_window()
        vis.add_geometry(mesh)
        vis.get_render_option().mesh_show_wireframe = True  # <-- SİHİRLİ SATIR BURASI
        vis.run()
        vis.destroy_window()
