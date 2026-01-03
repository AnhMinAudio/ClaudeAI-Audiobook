"""
Create a professional icon for AnhMin Audio
Microphone with sound wave on gradient background
"""

from PIL import Image, ImageDraw

# Create 512x512 image for high quality
size = 512
img = Image.new('RGBA', (size, size), (0, 0, 0, 0))

draw = ImageDraw.Draw(img)

# Draw circular gradient background
center = size // 2
max_radius = size // 2

for radius in range(max_radius, 0, -1):
    # Gradient from purple to blue
    ratio = radius / max_radius
    r = int(139 + (59 - 139) * ratio)  # 139->59
    g = int(92 + (130 - 92) * ratio)   # 92->130
    b = int(246 + (246 - 246) * ratio) # 246->246

    x1 = center - radius
    y1 = center - radius
    x2 = center + radius
    y2 = center + radius
    draw.ellipse([x1, y1, x2, y2], fill=(r, g, b, 255))

# Draw microphone (centered, scaled appropriately)
mic_center_x = center
mic_center_y = center - 20

# Microphone capsule (top oval)
capsule_width = 100
capsule_height = 140
draw.ellipse(
    [mic_center_x - capsule_width//2, mic_center_y - 40,
     mic_center_x + capsule_width//2, mic_center_y + capsule_height - 40],
    fill=(255, 255, 255, 255),
    outline=(200, 200, 200, 255),
    width=6
)

# Inner capsule detail (grille lines)
for i in range(5):
    y = mic_center_y - 20 + i * 25
    draw.line(
        [mic_center_x - 35, y, mic_center_x + 35, y],
        fill=(220, 220, 220, 255),
        width=3
    )

# Microphone stand connector
stand_top = mic_center_y + capsule_height - 40
draw.rectangle(
    [mic_center_x - 15, stand_top, mic_center_x + 15, stand_top + 40],
    fill=(255, 255, 255, 255)
)

# Microphone base arc
arc_y = stand_top + 40
draw.arc(
    [mic_center_x - 60, arc_y - 20, mic_center_x + 60, arc_y + 30],
    start=0, end=180,
    fill=(255, 255, 255, 255),
    width=8
)

# Sound waves (3 curved lines on each side)
wave_colors = [(255, 255, 255, 200), (255, 255, 255, 150), (255, 255, 255, 100)]

for i, color in enumerate(wave_colors):
    offset = 80 + i * 30

    # Left waves
    draw.arc(
        [mic_center_x - offset - 60, mic_center_y - 60,
         mic_center_x - offset + 60, mic_center_y + 60],
        start=-30, end=30,
        fill=color,
        width=5
    )

    # Right waves
    draw.arc(
        [mic_center_x + offset - 60, mic_center_y - 60,
         mic_center_x + offset + 60, mic_center_y + 60],
        start=150, end=210,
        fill=color,
        width=5
    )

# Add subtle shadow for depth
shadow = Image.new('RGBA', (size, size), (0, 0, 0, 0))
shadow_draw = ImageDraw.Draw(shadow)
shadow_draw.ellipse(
    [mic_center_x - capsule_width//2 + 5, mic_center_y - 35,
     mic_center_x + capsule_width//2 + 5, mic_center_y + capsule_height - 35],
    fill=(0, 0, 0, 50)
)
img = Image.alpha_composite(shadow, img)

# Save as ICO with multiple sizes
img.save('app_icon.ico', format='ICO', sizes=[
    (16, 16), (32, 32), (48, 48), (64, 64),
    (128, 128), (256, 256), (512, 512)
])

print("Icon created successfully: app_icon.ico")
print("Sizes: 16x16, 32x32, 48x48, 64x64, 128x128, 256x256, 512x512")
print("Design: White microphone with sound waves on purple-blue gradient")
print("\nYou can replace this with a custom icon anytime.")
