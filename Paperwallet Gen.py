import qrcode
from PIL import Image
import os
import random

templates = []
for i in os.listdir("templates"):
    print(i)
    templates.append("templates\\" + i)

with open("seeds.txt") as sf:
    count = 0
    for seed in sf:
        seed = seed.rstrip()
        count = count + 1
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_H,
            box_size=4,
            border=1,
        )
        qr.add_data(seed)
        qr.make(fit=True)

        img = qr.make_image()
        img.save("image.png")
        qr = Image.open("image.png", 'r')
        img_w, img_h = img.size

        rand = random.randint(0, len(templates))
        print(rand)
        print(len(templates))
        template = Image.open(templates[rand-1])

        tem_w, tem_h = template.size
        offset = ((tem_w - img_w) // 2, 350)
        template.paste(img, offset)
        template.save("paperwallets/" + str(count) + ".png")


