import rasterio
import numpy as np
import torch
import matplotlib.pyplot as plt
import segmentation_models_pytorch as smp
from albumentations import Compose, Normalize, Resize
from albumentations.pytorch import ToTensorV2
import cv2  # Pour le redimensionnement de la prédiction

# Charger le modèle sauvegardé
model = smp.Unet(encoder_name="resnet18", in_channels=3, classes=1, activation=None)
model.load_state_dict(torch.load("model.pth"))
model.eval()  # Ne pas oublier de passer en mode évaluation

image_path = "geneve.tiff"  

with rasterio.open(image_path) as src:
    img = src.read([1, 2, 3])  # RGB
    img = np.transpose(img, (1, 2, 0))  # HWC
    transform = src.transform
    bounds = src.bounds
    crs = src.crs

# Prétraiter l'image avant de la passer au modèle
transform = Compose([
    Resize(256, 256),  # Redimensionner l'image pour correspondre à la taille d'entrée du modèle
    Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225], max_pixel_value=255.0, p=1),  # Normaliser les pixels
    ToTensorV2(p=1)  
])

# Appliquer la transformation sur l'image
image_transformed = transform(image=img)["image"]
image_transformed = image_transformed.unsqueeze(0)  # Ajouter une dimension de lot

# Affichage des résultats
with torch.no_grad():
    pred = model(image_transformed).squeeze().sigmoid().numpy()

# Redimensionner la prédiction pour qu'elle corresponde à la taille de l'image originale
pred_resized = cv2.resize(pred, (img.shape[1], img.shape[0]))  # Redimensionnement à la taille de l'image satellite

# Superposer la prédiction sur l'image satellite
plt.figure(figsize=(12, 6))


plt.subplot(1, 2, 1)
plt.imshow(img)  
plt.title("Image Satellite")


plt.subplot(1, 2, 2)
plt.imshow(img)  
plt.imshow(pred_resized > 0.1, cmap='Reds', alpha=0.2)  
plt.title("Prédiction des Bâtiments")

plt.tight_layout()
plt.show()
