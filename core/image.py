def premoltiplica(im):
    from PIL import Image, ImageChops
    r, g, b, a = im.convert("RGBA").split()
    return Image.merge("RGBA", (
        ImageChops.multiply(r, a),
        ImageChops.multiply(g, a),
        ImageChops.multiply(b, a),
        a,
    ))
