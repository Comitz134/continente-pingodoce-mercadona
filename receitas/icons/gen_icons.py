"""Gera icon-192.png e icon-512.png (prato + garfo) usando apenas a stdlib."""
import struct
import zlib
import os

SIZES = (192, 512)
SS = 3  # supersampling por eixo


def clamp01(v):
    return 0.0 if v < 0 else (1.0 if v > 1 else v)


def in_rounded_square(x, y, r=0.22):
    hx = abs(x - 0.5) - (0.5 - r)
    hy = abs(y - 0.5) - (0.5 - r)
    if hx <= 0 or hy <= 0:
        return True
    return (hx * hx + hy * hy) <= r * r


def in_circle(x, y, cx, cy, rad):
    dx, dy = x - cx, y - cy
    return dx * dx + dy * dy <= rad * rad


def in_round_rect(x, y, cx, cy, w, h, rad):
    hx = abs(x - cx) - (w / 2 - rad)
    hy = abs(y - cy) - (h / 2 - rad)
    if hx <= 0 or hy <= 0:
        return True
    return (max(hx, 0) ** 2 + max(hy, 0) ** 2) <= rad * rad


def color_at(x, y):
    """x, y em [0,1]. Devolve (r, g, b, a)."""
    if not in_rounded_square(x, y, 0.22):
        return (0, 0, 0, 0)

    # fundo verde em gradiente vertical
    t = clamp01(y)
    r = int(0x22 + (0x15 - 0x22) * t)
    g = int(0xC5 + (0x80 - 0xC5) * t)
    b = int(0x5E + (0x3D - 0x5E) * t)
    base = (r, g, b, 255)

    # prato
    if in_circle(x, y, 0.5, 0.55, 0.335):
        if in_circle(x, y, 0.5, 0.55, 0.265):
            return (238, 242, 239, 255)  # interior do prato
        return (255, 255, 255, 255)      # borda

    # garfo (verde escuro)
    green = (22, 101, 52, 255)
    # tampa das pontas (3 dentes)
    if (
        in_round_rect(x, y, 0.42, 0.40, 0.045, 0.20, 0.022)
        or in_round_rect(x, y, 0.50, 0.40, 0.045, 0.20, 0.022)
        or in_round_rect(x, y, 0.58, 0.40, 0.045, 0.20, 0.022)
        or in_round_rect(x, y, 0.50, 0.505, 0.22, 0.055, 0.027)   # travessa
        or in_round_rect(x, y, 0.50, 0.66, 0.06, 0.26, 0.03)      # cabo
    ):
        return green

    return base


def render(size):
    px = bytearray()
    for py in range(size):
        row = bytearray()
        row.append(0)  # filtro None
        for pxi in range(size):
            acc = [0, 0, 0, 0]
            for sy in range(SS):
                for sx in range(SS):
                    x = (pxi + (sx + 0.5) / SS) / size
                    y = (py + (sy + 0.5) / SS) / size
                    c = color_at(x, y)
                    acc[0] += c[0]
                    acc[1] += c[1]
                    acc[2] += c[2]
                    acc[3] += c[3]
            n = SS * SS
            row += bytes((acc[0] // n, acc[1] // n, acc[2] // n, acc[3] // n))
        px += row
    return bytes(px)


def write_png(path, size):
    raw = render(size)
    def chunk(tag, data):
        c = struct.pack(">I", len(data)) + tag + data
        c += struct.pack(">I", zlib.crc32(tag + data) & 0xFFFFFFFF)
        return c

    ihdr = struct.pack(">IIBBBBB", size, size, 8, 6, 0, 0, 0)
    png = (
        b"\x89PNG\r\n\x1a\n"
        + chunk(b"IHDR", ihdr)
        + chunk(b"IDAT", zlib.compress(raw, 9))
        + chunk(b"IEND", b"")
    )
    with open(path, "wb") as f:
        f.write(png)
    print("gerado", path, len(png), "bytes")


here = os.path.dirname(os.path.abspath(__file__))
for s in SIZES:
    write_png(os.path.join(here, f"icon-{s}.png"), s)
