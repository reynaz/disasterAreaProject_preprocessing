import open3d as o3d
import numpy as np
import plotly.graph_objects as go
from matplotlib.colors import hsv_to_rgb

TILES_DIR = "data/processed/tiles"

def load_points(pattern):
    import glob, os
    all_points = []
    for f in glob.glob(pattern):
        pcd = o3d.io.read_point_cloud(f)
        if not pcd.is_empty():
            all_points.append(np.asarray(pcd.points))
    if not all_points:
        return np.empty((0,3))
    return np.vstack(all_points)

# Ground ve non-ground birleştir
g = load_points(f"{TILES_DIR}/*/ground.pcd")
ng = load_points(f"{TILES_DIR}/*/non_ground.pcd")

print(f"Ground: {len(g)} | Non-ground: {len(ng)}")

# HSV renk hesaplama (yüksekliğe göre)
if len(ng) > 0:
    z = ng[:,2]
    z_norm = (z - z.min()) / (z.max() - z.min() + 1e-8)
    hsv_colors = np.zeros((len(z_norm), 3))
    hsv_colors[:,0] = z_norm           # hue (0–1)
    hsv_colors[:,1] = 1.0              # saturation sabit
    hsv_colors[:,2] = 1.0              # value sabit
    rgb_colors = hsv_to_rgb(hsv_colors)
else:
    rgb_colors = np.empty((0,3))

# Plotly sahnesi
fig = go.Figure()

# Ground (yeşil)
fig.add_trace(go.Scatter3d(
    x=g[:,0], y=g[:,1], z=g[:,2],
    mode='markers',
    marker=dict(size=2, color='green', opacity=0.4),
    name='Ground'
))

# Non-ground (HSV renkli)
fig.add_trace(go.Scatter3d(
    x=ng[:,0], y=ng[:,1], z=ng[:,2],
    mode='markers',
    marker=dict(
        size=2,
        color=[f"rgb({int(r*255)},{int(g*255)},{int(b*255)})" for r,g,b in rgb_colors],
        opacity=0.9
    ),
    name='Non-ground (HSV)'
))

fig.update_layout(
    title="HSV tabanlı derinlik renklendirmesi",
    scene=dict(
        xaxis=dict(showbackground=False),
        yaxis=dict(showbackground=False),
        zaxis=dict(showbackground=False),
        aspectmode='data'
    ),
    margin=dict(l=0, r=0, b=0, t=40)
)
fig.show()

