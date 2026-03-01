import os
import numpy as np
from flask import Flask, render_template, request
from PIL import Image, ImageEnhance, ImageFilter

app = Flask(__name__)


def generate_braille(image_file, new_width=60, invert=False, brightness=1.1, contrast=1.5, aspect=0.5):
    try:
        img = Image.open(image_file).convert('L')
        img = img.filter(ImageFilter.DETAIL)
        if float(brightness) != 1.0:
            img = ImageEnhance.Brightness(img).enhance(float(brightness))
        if float(contrast) != 1.0:
            img = ImageEnhance.Contrast(img).enhance(float(contrast))

        w_orig, h_orig = img.size
        target_h = int((h_orig / w_orig) * new_width * float(aspect))
        if target_h < 1: target_h = 1

        render_w, render_h = int(new_width * 2), int(target_h * 4)
        img = img.resize((render_w, render_h), Image.Resampling.LANCZOS)
        pixels = np.array(img, dtype=float)

        # Алгоритм Аткинсона (НЕ ТРОГАЕМ)
        for y in range(render_h - 2):
            for x in range(render_w - 2):
                old_px = pixels[y, x]
                new_px = 255 if old_px > 127 else 0
                pixels[y, x] = new_px
                err = (old_px - new_px) / 8
                pixels[y, x + 1] += err
                pixels[y, x + 2] += err
                pixels[y + 1, x - 1] += err
                pixels[y + 1, x] += err
                pixels[y + 1, x + 1] += err
                pixels[y + 2, x] += err

        res = ""
        for y in range(0, render_h - 3, 4):
            for x in range(0, render_w - 1, 2):
                byte = 0

                def get_dot(dx, dy):
                    return pixels[y + dy, x + dx] > 127 if not invert else pixels[y + dy, x + dx] < 127

                if get_dot(0, 0): byte |= 0x1
                if get_dot(0, 1): byte |= 0x2
                if get_dot(0, 2): byte |= 0x4
                if get_dot(1, 0): byte |= 0x8
                if get_dot(1, 1): byte |= 0x10
                if get_dot(1, 2): byte |= 0x20
                if get_dot(0, 3): byte |= 0x40
                if get_dot(1, 3): byte |= 0x80
                res += chr(0x2800 + byte)
            res += "\n"
        return res
    except Exception as e:
        return str(e)


@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        width = int(request.form.get('width', 60))
        bright = float(request.form.get('brightness', 1.1))
        cont = float(request.form.get('contrast', 1.5))
        asp = float(request.form.get('aspect', 0.5))
        inv = 'invert' in request.form
        if 'photo' in request.files:
            f = request.files['photo']
            if f.filename != '':
                return generate_braille(f, width, inv, bright, cont, asp)
    return render_template('index.html')


if __name__ == '__main__':
    app.run(debug=True)