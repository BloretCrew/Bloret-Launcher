from PIL import Image

img = Image.open('Bloret.png')

# 指定多个尺寸（例如：16x16, 32x32, 48x48, 256x256）
sizes = [(16, 16), (32, 32), (48, 48), (256, 256)]

img.save('Bloret.ico', format='ICO', sizes=sizes)