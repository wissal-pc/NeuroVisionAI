import numpy as np
from skimage import measure
import cv2

def calculate_volume(mask, voxel_volume=1.0):
    """
    Calcule le volume total de la tumeur dans un masque 3D binaire.
    mask : np.array 3D binaire (0/1)
    voxel_volume : volume d'un voxel en mm3 ou unité réelle
    """
    return np.sum(mask) * voxel_volume

def get_tumor_coordinates(mask):
    """
    Retourne le centre de gravité (centroid) de la tumeur dans un masque 2D ou 3D.
    mask : np.array binaire (2D ou 3D)
    """
    labeled = measure.label(mask)
    props = measure.regionprops(labeled)
    if not props:
        return None
    centroid = props[0].centroid
    return tuple(int(c) for c in centroid)
def get_centroid_3d_mm(mask, spacing):
    """
    Calcule le centroïde 3D de la tumeur et le convertit en mm.
    """
    labeled = measure.label(mask)
    props = measure.regionprops(labeled)
    if not props:
        return None
    centroid_voxel = props[0].centroid
    centroid_mm = tuple(round(c * s, 2) for c, s in zip(centroid_voxel, spacing))
    return centroid_mm
def dice_coefficient(pred_mask, true_mask):
    intersection = np.sum(pred_mask * true_mask)
    denominator = np.sum(pred_mask) + np.sum(true_mask)
    if denominator == 0:
        return 1.0  # les deux masques sont vides
    return 2. * intersection / denominator
def overlay_mask(image_slice, mask_slice, alpha=0.4):
    color_mask = np.zeros((*mask_slice.shape, 3), dtype=np.uint8)
    color_mask[mask_slice == 1] = [255, 0, 0]  # masque en rouge
    image_rgb = cv2.cvtColor(image_slice, cv2.COLOR_GRAY2BGR)
    overlay = cv2.addWeighted(image_rgb, 1 - alpha, color_mask, alpha, 0)
    return overlay
def preprocess_slice(slice_2d):
    # Sauvegarder la taille originale
    original_shape = slice_2d.shape
    # Prétraitement avec resize
    img = cv2.resize(slice_2d, (128, 128))
    img = img.astype(np.float32) / np.max(img) if np.max(img) != 0 else img
    return np.expand_dims(img, axis=(0, -1)), original_shape
#Calculer l'age 
from datetime import datetime
def calculer_age(date_str):
    try:
        # naissance = datetime.strptime(date_str.strip(), '%d/%m/%Y')
        naissance = datetime.strptime(date_str.strip(), '%Y-%m-%d')
        aujourdhui = datetime.now()
        if naissance > aujourdhui:
            return None  # Date future
        return aujourdhui.year - naissance.year - ((aujourdhui.month, aujourdhui.day) < (naissance.month, naissance.day))
    except ValueError:
        return None

