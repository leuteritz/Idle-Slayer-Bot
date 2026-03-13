from PIL import Image

Image.open("assets/icon.png").save(
    "assets/icon.ico", format="ICO",
    sizes=[(16, 16), (32, 32), (48, 48), (256, 256)]
)
print("assets/icon.ico erstellt.")
