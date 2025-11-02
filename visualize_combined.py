import os
# ---- Thread çakışmalarına karşı (segfault azaltır) ----
 
os.environ.setdefault("OMP_NUM_THREADS", "1")
os.environ.setdefault("OPENBLAS_NUM_THREADS", "1")
os.environ.setdefault("MKL_NUM_THREADS", "1")

import open3d as o3d
import numpy as np
import glob
import os
import argparse
from tqdm import tqdm
import matplotlib
import matplotlib.pyplot as plt

# ------------------------------------------------------------
# 1) Tile'ları yükleme ve birleştirme (seninle aynı mantık)
# ------------------------------------------------------------
def load_points_from_tiles(tiles_base_dir, file_to_load, max_points_per_tile=None):
    search_pattern = os.path.join(tiles_base_dir, "*", file_to_load)
    pcd_files = glob.glob(search_pattern)

    if not pcd_files:
        print(f"Uyarı: '{search_pattern}' ile eşleşen dosya bulunamadı.")
        return None

    print(f"Toplam {len(pcd_files)} adet '{file_to_load}' dosyası bulundu.")
    all_points = []
    for pcd_path in tqdm(pcd_files, desc=f"{file_to_load} dosyaları yükleniyor"):
        try:
            pcd = o3d.io.read_point_cloud(pcd_path)
            if pcd.has_points():
                pts = np.asarray(pcd.points)
                if max_points_per_tile is not None and len(pts) > max_points_per_tile:
                    idx = np.random.choice(len(pts), max_points_per_tile, replace=False)
                    pts = pts[idx]
                all_points.append(pts)
        except Exception as e:
            print(f"Uyarı: {pcd_path} okunurken hata oluştu: {e}")

    if not all_points:
        print(f"'{file_to_load}' için birleştirilecek hiç nokta bulunamadı.")
        return None

    combined = np.vstack(all_points)
    print(f"'{file_to_load}' için toplam {len(combined)} nokta birleştirildi.")
    return combined

# ------------------------------------------------------------
# 2) Veri temizliği ve opsiyonel downsample
# ------------------------------------------------------------
def sanitize_points(points, voxel_size=None):
    # NaN / inf temizliği
    mask = np.isfinite(points).all(axis=1)
    clean = points[mask]
    removed = len(points) - len(clean)
    if removed > 0:
        print(f"Temizlendi: {removed} nokta (NaN/inf). Kalan: {len(clean)}")

    if voxel_size is not None and voxel_size > 0:
        p = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(clean))
        p = p.voxel_down_sample(voxel_size=voxel_size)
        clean = np.asarray(p.points)
        print(f"Voxel downsample (voxel={voxel_size}) -> {len(clean)} nokta")
    return clean

# ------------------------------------------------------------
# 3) Yoğunluk + Z tabanlı renkler (Matplotlib uyarısız)
# ------------------------------------------------------------
def compute_density_colors(points, base_colormap='magma', radius=1.0, sample_target=20000):
    z_vals = points[:, 2]
    z_norm = (z_vals - z_vals.min()) / (np.ptp(z_vals) + 1e-9)

    pcd = o3d.geometry.PointCloud(o3d.utility.Vector3dVector(points))
    tree = o3d.geometry.KDTreeFlann(pcd)

    densities = np.zeros(len(points))
    # toplam örneği (maks) sample_target civarı tut
    step = max(1, len(points) // sample_target)
    for i in range(0, len(points), step):
        [_, idx, _] = tree.search_radius_vector_3d(points[i], radius)
        densities[idx] += 1

    if densities.max() > 0:
        densities = densities / densities.max()
    intensity = 0.5 * z_norm + 0.5 * densities

    cmap = matplotlib.colormaps.get_cmap(base_colormap)
    colors = cmap(intensity)[:, :3]
    return colors

# ------------------------------------------------------------
# 4) Normalleri güvenli şekilde hesapla (fallback'li)
# ------------------------------------------------------------
def estimate_normals_safe(pcd: o3d.geometry.PointCloud,
                          approx_spacing=None,
                          prefer_radius_first=True):
    """
    Büyük bulutlarda segfault riskini azaltmak için kademeli strateji:
    - Önce Hybrid(radius, max_nn), başarısızsa
    - KNN(k) deneyelim.
    'orient_normals_consistent_tangent_plane' kullanılmıyor (ağır ve riskli).
    """
    npts = np.asarray(pcd.points).shape[0]
    if npts == 0:
        return False

    # Yaklaşık nokta aralığı tahmini (gerekirse)
    if approx_spacing is None:
        # küçük bir örneklemle kaba tahmin
        sample = min(npts, 50000)
        idx = np.random.choice(npts, sample, replace=False)
        sub = pcd.select_by_index(idx)
        dists = sub.compute_nearest_neighbor_distance()
        if len(dists) > 0:
            approx_spacing = float(np.median(dists))
        else:
            approx_spacing = 0.1
    approx_spacing = max(approx_spacing, 1e-3)

    # Parametreler
    radius = approx_spacing * 12.0
    max_nn = 32
    k_fallback = 24

    # 1) Hybrid (radius, max_nn)
    if prefer_radius_first:
        try:
            print(f"Normals: Hybrid radius={radius:.4f}, max_nn={max_nn} ...")
            pcd.estimate_normals(
                search_param=o3d.geometry.KDTreeSearchParamHybrid(radius=radius, max_nn=max_nn)
            )
            return True
        except Exception as e:
            print(f"Hybrid normal hesaplama hatası: {e}")

    # 2) KNN
    try:
        print(f"Normals: KNN k={k_fallback} ...")
        pcd.estimate_normals(
            search_param=o3d.geometry.KDTreeSearchParamKNN(knn=k_fallback)
        )
        return True
    except Exception as e:
        print(f"KNN normal hesaplama hatası: {e}")
        return False

# ------------------------------------------------------------
# 5) Ana Program (Visualizer eski API ile)
# ------------------------------------------------------------
if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Conda uyumlu: derinlik + yoğunluk renkleri, güvenli normal hesaplama, klasik Visualizer")
    parser.add_argument("--tiles_dir", default=os.path.join("data", "processed", "tiles"))
    parser.add_argument("--max_points", type=int, default=None)
    parser.add_argument("--density_radius", type=float, default=1.0, help="Yoğunluk hesabı yarıçapı")
    parser.add_argument("--voxel", type=float, default=0.0, help="Opsiyonel voxel downsample (0=kapalı)")
    args = parser.parse_args()

    print("Ground noktaları yükleniyor...")
    ground = load_points_from_tiles(args.tiles_dir, "ground.pcd", args.max_points)
    print("\nNon-ground noktaları yükleniyor...")
    non_ground = load_points_from_tiles(args.tiles_dir, "non_ground.pcd", args.max_points)

    if ground is None and non_ground is None:
        print("Görselleştirilecek veri yok.")
        raise SystemExit

    # --- Temizle + (opsiyonel) downsample ---
    if ground is not None:
        ground = sanitize_points(ground, voxel_size=args.voxel if args.voxel > 0 else None)
    if non_ground is not None:
        non_ground = sanitize_points(non_ground, voxel_size=args.voxel if args.voxel > 0 else None)

    # --- Birleştir ---
    all_points, is_ground = [], []
    if ground is not None and len(ground) > 0:
        all_points.append(ground)
        is_ground.append(np.ones(len(ground), dtype=bool))
    if non_ground is not None and len(non_ground) > 0:
        all_points.append(non_ground)
        is_ground.append(np.zeros(len(non_ground), dtype=bool))

    combined = np.vstack(all_points)
    mask_ground = np.concatenate(is_ground)
    print(f"\nToplam {len(combined)} nokta işlenecek (temizlenmiş/downsample'lı).")

    # --- Renkler ---
    colors = np.zeros((len(combined), 3), dtype=np.float64)
    if np.any(mask_ground):
        colors[mask_ground] = [0.0, 0.4, 0.05]  # koyu yeşil

    if np.any(~mask_ground):
        colors[~mask_ground] = compute_density_colors(
            combined[~mask_ground],
            base_colormap='magma',
            radius=args.density_radius,
            sample_target=20000
        )

    # --- PointCloud ---
    pcd = o3d.geometry.PointCloud()
    pcd.points = o3d.utility.Vector3dVector(combined)
    pcd.colors = o3d.utility.Vector3dVector(colors)

    # --- Normaller (güvenli) ---
    print("Normaller hesaplanıyor (güvenli mod)...")
    normals_ok = estimate_normals_safe(pcd)

    if not normals_ok:
        print("Uyarı: Normaller hesaplanamadı. Normalsız görselleştirilecek (renk + yoğunluk ile derinlik).")

    # --- Görselleştir (klasik) ---
    print("\nGörselleştirme başlıyor...")
    vis = o3d.visualization.Visualizer()
    vis.create_window(window_name="Depth Enhanced Point Cloud (Conda Safe)", width=1440, height=900)
    vis.add_geometry(pcd)

    opt = vis.get_render_option()
    opt.background_color = np.asarray([1.0, 1.0, 1.0])
    opt.point_size = 2.5
    opt.light_on = True

    ctr = vis.get_view_control()
    ctr.set_front([0.5, -0.4, -0.8])
    ctr.set_lookat(pcd.get_center())
    ctr.set_up([0, 0, 1])
    ctr.set_zoom(0.65)

    vis.run()
    vis.destroy_window()
   
