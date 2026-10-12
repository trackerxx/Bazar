"""Bazar Hisab: app icon + splash screen apply script.
GitHub Actions e `npx cap add android` er por eta run hoy.
"""
import os, shutil
from PIL import Image, ImageDraw

RES = "android/app/src/main/res"
SRC = "resources" if os.path.isdir("resources") else "."  # folder na thakle repo root theke nibe

fg     = Image.open(f"{SRC}/icon-foreground.png").convert("RGBA")
legacy = Image.open(f"{SRC}/icon-legacy.png").convert("RGBA")
# ---------- Icon ke ektu choto kora (edge e jeno kata na pore) ----------
ICON_SCALE = 0.72

def shrink_fg(img, k):
    W, H = img.size
    w, h = int(W * k), int(H * k)
    out = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    out.paste(img.resize((w, h), Image.LANCZOS), ((W - w) // 2, (H - h) // 2))
    return out

def shrink_legacy(img, k):
    W, H = img.size
    w, h = int(W * k), int(H * k)
    base = Image.new("RGBA", (W, H), (0, 0, 0, 255))
    inner = img.resize((w, h), Image.LANCZOS)
    base.alpha_composite(inner, ((W - w) // 2, (H - h) // 2))
    base.putalpha(img.getchannel("A"))  # ager rounded corner thik rakho
    return base

fg = shrink_fg(fg, ICON_SCALE)
legacy = shrink_legacy(legacy, ICON_SCALE)

splash = Image.open(f"{SRC}/splash-icon.png").convert("RGBA")
text   = Image.open(f"{SRC}/splash-text.png").convert("RGBA")

def save(img, path):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    img.save(path)

# ---------- App icon ----------
legacy_px = {"mdpi": 48, "hdpi": 72, "xhdpi": 96, "xxhdpi": 144, "xxxhdpi": 192}
fg_px     = {"mdpi": 108, "hdpi": 162, "xhdpi": 216, "xxhdpi": 324, "xxxhdpi": 432}

for d, px in legacy_px.items():
    sq = legacy.resize((px, px), Image.LANCZOS)
    save(sq, f"{RES}/mipmap-{d}/ic_launcher.png")
    mask = Image.new("L", (px * 4, px * 4), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, px * 4 - 1, px * 4 - 1), fill=255)
    mask = mask.resize((px, px), Image.LANCZOS)
    rd = Image.new("RGBA", (px, px), (0, 0, 0, 0))
    rd.paste(sq, (0, 0), mask)
    save(rd, f"{RES}/mipmap-{d}/ic_launcher_round.png")
    save(fg.resize((fg_px[d], fg_px[d]), Image.LANCZOS), f"{RES}/mipmap-{d}/ic_launcher_foreground.png")

# template er default vector icon gula muche dao
for p in (f"{RES}/drawable/ic_launcher_background.xml",
          f"{RES}/drawable-v24/ic_launcher_foreground.xml"):
    if os.path.exists(p):
        os.remove(p)

adaptive = """<?xml version="1.0" encoding="utf-8"?>
<adaptive-icon xmlns:android="http://schemas.android.com/apk/res/android">
    <background android:drawable="@color/ic_launcher_background"/>
    <foreground android:drawable="@mipmap/ic_launcher_foreground"/>
</adaptive-icon>
"""
for name in ("ic_launcher.xml", "ic_launcher_round.xml"):
    os.makedirs(f"{RES}/mipmap-anydpi-v26", exist_ok=True)
    open(f"{RES}/mipmap-anydpi-v26/{name}", "w").write(adaptive)

os.makedirs(f"{RES}/values", exist_ok=True)
open(f"{RES}/values/ic_launcher_background.xml", "w").write(
    '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
    '    <color name="ic_launcher_background">#000000</color>\n</resources>\n')

# ---------- Splash screen ----------
def make_splash(w, h):
    # icon thik majhkhane, tar niche tagline text (360dp wide phone e icon ~135dp)
    img = Image.new("RGB", (w, h), (0, 0, 0))
    m = min(w, h)
    s = int(m * 0.27)
    t = splash.resize((s, s), Image.LANCZOS)
    ix, iy = (w - s) // 2, (h - s) // 2
    img.paste(t, (ix, iy), t)
    tw = int(m * 0.42)
    th = int(text.height * tw / text.width)
    tx = text.resize((tw, th), Image.LANCZOS)
    img.paste(tx, ((w - tw) // 2, iy + s + int(m * 0.06)), tx)
    return img

port = {"mdpi": (320, 480), "hdpi": (480, 800), "xhdpi": (720, 1280),
        "xxhdpi": (960, 1600), "xxxhdpi": (1280, 1920)}
for d, (w, h) in port.items():
    save(make_splash(w, h), f"{RES}/drawable-port-{d}/splash.png")
    save(make_splash(h, w), f"{RES}/drawable-land-{d}/splash.png")
save(make_splash(480, 800), f"{RES}/drawable/splash.png")

# Android 12+ system splash (icon + black bg)
sq = Image.new("RGBA", (960, 960), (0, 0, 0, 0))
t = splash.resize((320, 320), Image.LANCZOS)
sq.alpha_composite(t, (320, 320))
save(sq, f"{RES}/drawable-nodpi/splash_icon.png")

# splash theme: Capacitor er generate kora styles.xml e black bg + icon boshao
import re
sp = f"{RES}/values/styles.xml"
st = open(sp, encoding="utf-8").read()
m = re.search(r'<style name="AppTheme\.NoActionBarLaunch"([^>]*)>(.*?)</style>', st, re.S)
assert m, "AppTheme.NoActionBarLaunch not found"
inner = m.group(2)
for key in ("windowSplashScreenBackground", "windowSplashScreenAnimatedIcon", "android:windowSplashScreenBackground", "android:windowSplashScreenAnimatedIcon"):
    inner = re.sub(r'\s*<item name="%s">.*?</item>' % re.escape(key), "", inner)
if "SplashScreen" in m.group(1):
    # androidx core-splashscreen theme (Capacitor 5/6)
    items = ('\n        <item name="windowSplashScreenBackground">#000000</item>'
             '\n        <item name="windowSplashScreenAnimatedIcon">@drawable/splash_icon</item>\n    ')
    new_style = '<style name="AppTheme.NoActionBarLaunch"' + m.group(1) + '>' + inner.rstrip() + items + '</style>'
    st = st[:m.start()] + new_style + st[m.end():]
    open(sp, "w", encoding="utf-8").write(st)
    print("splash theme: androidx")
else:
    # normal theme: Android 12+ er jonno values-v31 e alada
    os.makedirs(f"{RES}/values-v31", exist_ok=True)
    open(f"{RES}/values-v31/styles.xml", "w", encoding="utf-8").write(
        '<?xml version="1.0" encoding="utf-8"?>\n<resources>\n'
        '    <style name="AppTheme.NoActionBarLaunch"' + m.group(1) + '>' + inner.rstrip() + '\n'
        '        <item name="android:windowSplashScreenBackground">#000000</item>\n'
        '        <item name="android:windowSplashScreenAnimatedIcon">@drawable/splash_icon</item>\n'
        '    </style>\n</resources>\n')
    print("splash theme: v31")
print("Icon + splash applied")
