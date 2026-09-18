"""Fresh visual palette generated whenever a Streamlit page reruns."""
import colorsys
import random


_rng = random.SystemRandom()


def _color(saturation=0.68, lightness=0.48):
    hue = _rng.random()
    red, green, blue = colorsys.hls_to_rgb(hue, lightness, saturation)
    return "#{:02X}{:02X}{:02X}".format(
        round(red * 255), round(green * 255), round(blue * 255)
    )


def _tint(color, amount=0.88):
    red = int(color[1:3], 16)
    green = int(color[3:5], 16)
    blue = int(color[5:7], 16)
    return "#{:02X}{:02X}{:02X}".format(
        round(red + (255 - red) * amount),
        round(green + (255 - green) * amount),
        round(blue + (255 - blue) * amount),
    )


PRIMARY = _color(saturation=0.72, lightness=0.28)
ACCENT = _color(saturation=0.72, lightness=0.52)
RISK = _color(saturation=0.78, lightness=0.45)
SAFE = _color(saturation=0.65, lightness=0.40)
NEUTRAL = _color(saturation=0.18, lightness=0.42)
AT_RISK = _color(saturation=0.72, lightness=0.52)
BG_PAGE = _tint(_color(saturation=0.12, lightness=0.52), 0.96)
BG_CARD = _tint(ACCENT, 0.91)
SIDEBAR_TEXT = _tint(_color(saturation=0.10, lightness=0.55), 0.84)
BORDER = _tint(NEUTRAL, 0.72)
PALE_RISK = _tint(RISK, 0.83)
PALE_ACCENT = _tint(ACCENT, 0.82)
PALE_NEUTRAL = _tint(NEUTRAL, 0.83)
PALE_SAFE = _tint(SAFE, 0.83)
