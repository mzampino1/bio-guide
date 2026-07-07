import os
import requests
import matplotlib.pyplot as plt
from PIL import Image as PILImage, ImageDraw

def generate_visual_assets(monthly_trends, unique_species, hotspots):
    """
    Generates analytics charts, scatter maps, and downloads all unique species photos.
    Saves all output assets to the 'tmp' directory.
    """
    os.makedirs("tmp", exist_ok=True)
    
    # 1. Monthly Trends Chart
    if monthly_trends:
        months = [t['month_name'] for t in monthly_trends]
        sightings = [t['sightings'] for t in monthly_trends]
        
        fig, ax = plt.subplots(figsize=(6, 2.5))
        ax.bar(months, sightings, color='#2E7D32', edgecolor='#1B5E20', alpha=0.85, width=0.5)
        ax.set_title("Monthly Wildlife Activity Trends", fontsize=10, fontweight='bold', color='#1B5E20', pad=8)
        ax.set_ylabel("Sightings", fontsize=8, color='#424242')
        ax.tick_params(axis='both', labelsize=8, colors='#424242')
        ax.spines['top'].set_visible(False)
        ax.spines['right'].set_visible(False)
        ax.grid(axis='y', linestyle='--', alpha=0.3)
        plt.tight_layout()
        plt.savefig("tmp/trend_chart.png", dpi=300)
        plt.close()
    
    # 2. Density Hotspot Map
    if hotspots:
        lats = [h['grid_latitude'] for h in hotspots]
        lngs = [h['grid_longitude'] for h in hotspots]
        sizes = [max(h['sightings'] * 40, 60) for h in hotspots] 
        richness = [h['species_richness'] for h in hotspots]
        
        fig, ax = plt.subplots(figsize=(6, 2.5))
        sc = ax.scatter(lngs, lats, s=sizes, c=richness, cmap='YlOrBr', edgecolor='#5D4037', alpha=0.85, linewidths=0.5)
        ax.set_title("Regional Biodiversity Hotspots", fontsize=10, fontweight='bold', color='#1B5E20', pad=8)
        ax.tick_params(axis='both', labelsize=8)
        ax.grid(True, linestyle=':', alpha=0.5)
        ax.set_facecolor('#FAFAFA')
        
        cbar = plt.colorbar(sc, ax=ax, fraction=0.046, pad=0.04)
        cbar.set_label("Species Richness", fontsize=7, color='#424242')
        cbar.ax.tick_params(labelsize=7)
        
        plt.tight_layout()
        plt.savefig("tmp/location_map.png", dpi=300)
        plt.close()

    # 3. Species Placeholder Creation
    placeholder_path = "tmp/species_placeholder.png"
    if not os.path.exists(placeholder_path):
        img = PILImage.new('RGB', (140, 110), color='#EEEEEE')
        draw = ImageDraw.Draw(img)
        draw.rectangle([(2, 2), (138, 108)], outline='#BDBDBD', width=1)
        draw.text((32, 48), "[ No Photo ]", fill='#9E9E9E')
        img.save(placeholder_path)

    # 4. Process & Download Species Images Safely
    for species in unique_species:
        taxon_id = species.get("taxon_id")
        img_url = species.get("image_url")
        target_path = f"tmp/species_{taxon_id}.png"
        
        if img_url and not os.path.exists(target_path):
            try:
                res = requests.get(img_url, timeout=5)
                if res.status_code == 200:
                    with open(target_path, 'wb') as f:
                        f.write(res.content)
            except Exception:
                pass