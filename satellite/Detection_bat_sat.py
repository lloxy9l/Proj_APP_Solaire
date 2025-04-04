# 📦 Installations préalables 
# pip install rasterio geopandas shapely torch torchvision segmentation-models-pytorch albumentations tqdm requests

import rasterio
import geopandas as gpd
import numpy as np
from rasterio.features import rasterize
from shapely.geometry import box
import matplotlib.pyplot as plt
import torch
import torch.nn as nn
import torchvision.transforms as T
import segmentation_models_pytorch as smp
from torch.utils.data import Dataset, DataLoader
from albumentations import Resize, Normalize, Compose
from albumentations.pytorch import ToTensorV2
import requests
import json
from shapely.geometry import Polygon
from collections import defaultdict
# Etape 1 : Charger une image satellite GeoTIFF
image_path = "geneve.tiff"  

with rasterio.open(image_path) as src:
    img = src.read([1, 2, 3])  # RGB
    img = np.transpose(img, (1, 2, 0))  # HWC
    transform = src.transform
    bounds = src.bounds
    crs = src.crs

# Etape 2 : Récupérer les bâtiments depuis OpenStreetMap (bbox autour de Genève)

bbox_coords = [46.17, 6.10, 46.25, 6.25]  # minlat, minlon, maxlat, maxlon
query = f"""
[out:json];
(
  way["building"]({bbox_coords[0]},{bbox_coords[1]},{bbox_coords[2]},{bbox_coords[3]});
);
out body;
>;
out skel qt;
"""
response = requests.get("https://overpass-api.de/api/interpreter", params={"data": query})
osm_data = response.json()

# Convertir en GeoDataFrame


nodes = {el['id']: (el['lon'], el['lat']) for el in osm_data['elements'] if el['type'] == 'node'}
ways = [el for el in osm_data['elements'] if el['type'] == 'way']
polygons = []
for way in ways:
    try:
        coords = [nodes[node_id] for node_id in way['nodes'] if node_id in nodes]
        if coords[0] != coords[-1]:
            coords.append(coords[0])
        polygons.append(Polygon(coords))
    except:
        continue
buildings = gpd.GeoDataFrame(geometry=polygons, crs="EPSG:4326").to_crs(crs)

# Etape 3 : Rasteriser les polygones pour créer le masque
bbox = box(*bounds)
buildings = buildings[buildings.intersects(bbox)]
building_mask = rasterize(
    [(geom, 1) for geom in buildings.geometry],
    out_shape=(img.shape[0], img.shape[1]),
    transform=transform,
    fill=0,
    dtype=np.uint8
)

# Etape 4 : Dataset PyTorch
class SatelliteDataset(Dataset):
    def __init__(self, image, mask, transform=None):
        self.image = image
        self.mask = mask
        self.transform = transform

    def __len__(self):
        return 1

    def __getitem__(self, idx):
        augmented = self.transform(image=self.image, mask=self.mask)
        return augmented['image'], augmented['mask'].unsqueeze(0).float()


transform = Compose([
    Resize(256, 256),
    Normalize(),
    ToTensorV2()
])

dataset = SatelliteDataset(img, building_mask, transform=transform)
loader = DataLoader(dataset, batch_size=1)

# Etape 5 : Modèle U-Net
model = smp.Unet(encoder_name="resnet18", in_channels=3, classes=1, activation=None)
loss_fn = nn.BCEWithLogitsLoss()
optimizer = torch.optim.Adam(model.parameters(), lr=1e-3)

num_epochs = 1000 
# Boucle d'entraînement sur plusieurs époques
for epoch in range(num_epochs):
    model.train() 
    epoch_loss = 0  
    for image, mask in loader:
        optimizer.zero_grad() 
        output = model(image)  
        loss = loss_fn(output, mask)  
        loss.backward()  
        optimizer.step()  
        
        epoch_loss += loss.item()  

    avg_epoch_loss = epoch_loss / len(loader)  
    print(f"Époque {epoch+1}/{num_epochs}, Perte moyenne : {avg_epoch_loss:.4f}")



torch.save(model.state_dict(), "model.pth")
