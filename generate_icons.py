"""Generate PWA icons for Daystock using Pillow for high quality."""
import os
import math

try:
    from PIL import Image, ImageDraw, ImageFont
    HAS_PILLOW = True
except ImportError:
    HAS_PILLOW = False
    import struct
    import zlib


def generate_with_pillow(size, path):
    """Generate a high-quality Daystock icon using Pillow."""
    bg = (10, 15, 30)          # #0a0f1e
    accent = (0, 212, 255)     # #00d4ff
    green = (0, 255, 136)      # #00ff88

    img = Image.new('RGBA', (size, size), bg)
    draw = ImageDraw.Draw(img)

    cx, cy = size // 2, size // 2
    margin = int(size * 0.08)

    # Outer rounded rectangle background with subtle gradient feel
    r = int(size * 0.15)
    draw.rounded_rectangle([margin, margin, size - margin, size - margin],
                           radius=r, fill=(15, 22, 41), outline=accent, width=max(2, size // 128))

    # Draw a stylized stock chart line (uptrend)
    chart_margin_x = int(size * 0.2)
    chart_margin_top = int(size * 0.55)
    chart_margin_bot = int(size * 0.78)
    chart_w = size - 2 * chart_margin_x

    # Chart line points (normalized 0-1 for x and y)
    points_norm = [
        (0.0, 0.7), (0.12, 0.5), (0.25, 0.65), (0.38, 0.35),
        (0.5, 0.5), (0.62, 0.2), (0.75, 0.35), (0.88, 0.05), (1.0, 0.15)
    ]

    chart_points = []
    for px, py in points_norm:
        x = chart_margin_x + px * chart_w
        y = chart_margin_top + py * (chart_margin_bot - chart_margin_top)
        chart_points.append((x, y))

    # Draw chart line
    line_width = max(3, size // 100)
    for i in range(len(chart_points) - 1):
        x1, y1 = chart_points[i]
        x2, y2 = chart_points[i + 1]
        # Gradient from accent to green as it goes up
        progress = i / (len(chart_points) - 1)
        cr = int(accent[0] + (green[0] - accent[0]) * progress)
        cg = int(accent[1] + (green[1] - accent[1]) * progress)
        cb = int(accent[2] + (green[2] - accent[2]) * progress)
        draw.line([(x1, y1), (x2, y2)], fill=(cr, cg, cb), width=line_width)

    # Draw small dots at chart points
    dot_r = max(2, size // 120)
    for i, (px, py) in enumerate(chart_points):
        progress = i / (len(chart_points) - 1)
        cr = int(accent[0] + (green[0] - accent[0]) * progress)
        cg = int(accent[1] + (green[1] - accent[1]) * progress)
        cb = int(accent[2] + (green[2] - accent[2]) * progress)
        draw.ellipse([px - dot_r, py - dot_r, px + dot_r, py + dot_r], fill=(cr, cg, cb))

    # Draw "DS" text (Daystock) at top
    text = "DS"
    # Try to use a built-in font at a reasonable size
    font_size = int(size * 0.28)
    try:
        font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", font_size)
    except (IOError, OSError):
        try:
            font = ImageFont.truetype("/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf", font_size)
        except (IOError, OSError):
            font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), text, font=font)
    tw = bbox[2] - bbox[0]
    th = bbox[3] - bbox[1]
    text_x = cx - tw // 2
    text_y = int(size * 0.15)

    # Draw text with accent color
    draw.text((text_x, text_y), text, fill=accent, font=font)

    # Draw upward arrow indicator (▲) near the end of chart
    arrow_size = int(size * 0.06)
    arrow_x = chart_points[-1][0] + int(size * 0.03)
    arrow_y = chart_points[-1][1] - int(size * 0.02)
    arrow_points = [
        (arrow_x, arrow_y - arrow_size),
        (arrow_x - arrow_size * 0.6, arrow_y + arrow_size * 0.3),
        (arrow_x + arrow_size * 0.6, arrow_y + arrow_size * 0.3),
    ]
    draw.polygon(arrow_points, fill=green)

    img.save(path, 'PNG')
    print(f'Generated {path} ({size}x{size})')


def generate_fallback(size, path):
    """Fallback: pure Python PNG without Pillow."""
    import struct
    import zlib

    def chunk(chunk_type, data):
        c = chunk_type + data
        return struct.pack('>I', len(data)) + c + struct.pack('>I', zlib.crc32(c) & 0xffffffff)

    header = b'\x89PNG\r\n\x1a\n'
    ihdr = chunk(b'IHDR', struct.pack('>IIBBBBB', size, size, 8, 2, 0, 0, 0))

    bg = (10, 15, 30)
    accent = (0, 212, 255)

    raw = b''
    cx, cy = size // 2, size // 2
    r = int(size * 0.38)

    for y in range(size):
        raw += b'\x00'
        for x in range(size):
            dx, dy = x - cx, y - cy
            dist = (dx * dx + dy * dy) ** 0.5

            if dist < r:
                # Draw DS letters pattern
                lx = (x - cx + r) / (2 * r) * 10
                ly = (y - cy + r) / (2 * r) * 10
                in_letter = False

                # D shape
                if 1.5 <= lx <= 4.5 and 2 <= ly <= 8:
                    if lx <= 2.3:  # left bar
                        in_letter = True
                    elif 2 <= ly <= 2.8 or 7.2 <= ly <= 8:  # top/bottom
                        in_letter = True
                    elif lx >= 3.8 and 3.5 <= ly <= 6.5:  # right curve
                        in_letter = True

                # S shape
                if 5.5 <= lx <= 8.5 and 2 <= ly <= 8:
                    if 2 <= ly <= 2.8 and 5.5 <= lx <= 8.5:
                        in_letter = True
                    elif 2.8 <= ly <= 4.5 and 5.5 <= lx <= 6.3:
                        in_letter = True
                    elif 4.5 <= ly <= 5.5 and 5.5 <= lx <= 8.5:
                        in_letter = True
                    elif 5.5 <= ly <= 7.2 and 7.7 <= lx <= 8.5:
                        in_letter = True
                    elif 7.2 <= ly <= 8 and 5.5 <= lx <= 8.5:
                        in_letter = True

                raw += bytes(accent if in_letter else bg)
            elif dist < r + max(2, size // 128):
                raw += bytes(accent)
            else:
                raw += bytes(bg)

    idat = chunk(b'IDAT', zlib.compress(raw, 9))
    iend = chunk(b'IEND', b'')

    with open(path, 'wb') as f:
        f.write(header + ihdr + idat + iend)
    print(f'Generated {path} ({size}x{size}) [fallback]')


def main():
    icon_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'icons')
    os.makedirs(icon_dir, exist_ok=True)

    sizes = [192, 512]

    for size in sizes:
        path = os.path.join(icon_dir, f'icon-{size}x{size}.png')
        if os.path.exists(path):
            fsize = os.path.getsize(path)
            if fsize > 100:
                print(f'Exists {path} ({fsize} bytes)')
                continue
        if HAS_PILLOW:
            generate_with_pillow(size, path)
        else:
            generate_fallback(size, path)


if __name__ == '__main__':
    main()
