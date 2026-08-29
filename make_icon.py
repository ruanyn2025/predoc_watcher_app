# -*- coding: utf-8 -*-
"""生成应用图标。

设计是像素画，所以直接在 16×16 网格上作画，再用 NEAREST 整数倍放大 ——
每个尺寸都绝对锐利，不存在缩放糊化。托盘图标实际显示就是 16~24px，
这个尺寸下 6 个字母横排放不下，所以拆成 "pre" / "doc" 两行。

改了这个文件后重新跑一次：python make_icon.py
"""

from pathlib import Path

from PIL import Image

BASE_DIR = Path(__file__).resolve().parent

# 3×5 像素字模。3px 宽是还能认出字形的下限，故用大写形态
# —— 小写的 e / o / c 在 3px 下会糊成一个点。
GLYPH = {
    "p": ["##.", "#.#", "##.", "#..", "#.."],
    "r": ["##.", "#.#", "##.", "#.#", "#.#"],
    "e": ["###", "#..", "##.", "#..", "###"],
    "d": ["##.", "#.#", "#.#", "#.#", "##."],
    "o": ["###", "#.#", "#.#", "#.#", "###"],
    "c": ["###", "#..", "#..", "#..", "###"],
}

BLACK = (24, 26, 30, 255)
WHITE = (255, 255, 255, 255)
ORANGE = (232, 108, 62, 255)
CLEAR = (0, 0, 0, 0)

# 像素风圆角：直接抠掉四角的这几个点
CORNERS = [(0, 0), (1, 0), (0, 1), (15, 0), (14, 0), (15, 1),
           (0, 15), (1, 15), (0, 14), (15, 15), (14, 15), (15, 14)]

ICO_SIZES = [16, 24, 32, 48, 64, 128, 256]


def render_16():
    im = Image.new("RGBA", (16, 16), CLEAR)
    px = im.load()
    for y in range(16):
        for x in range(16):
            px[x, y] = BLACK
    for x, y in CORNERS:
        px[x, y] = CLEAR
    for row, (word, color) in enumerate((("pre", WHITE), ("doc", ORANGE))):
        oy = 3 + row * 6                      # 5px 字高 + 1px 行距
        for i, ch in enumerate(word):
            ox = 3 + i * 4                    # 3px 字宽 + 1px 字距
            for dy, line in enumerate(GLYPH[ch]):
                for dx, on in enumerate(line):
                    if on == "#":
                        px[ox + dx, oy + dy] = color
    return im


def main():
    base = render_16()
    static = BASE_DIR / "static"
    static.mkdir(exist_ok=True)

    # 多尺寸 ICO：托盘、窗口、任务栏各取所需
    ico = BASE_DIR / "app.ico"
    base.resize((256, 256), Image.NEAREST).save(
        ico, format="ICO", sizes=[(s, s) for s in ICO_SIZES])

    base.resize((256, 256), Image.NEAREST).save(static / "icon.png")
    base.resize((32, 32), Image.NEAREST).save(static / "favicon.png")
    print("已生成：")
    print("  %s（含 %s）" % (ico, "/".join(str(s) for s in ICO_SIZES)))
    print("  %s" % (static / "icon.png"))
    print("  %s" % (static / "favicon.png"))


if __name__ == "__main__":
    main()
