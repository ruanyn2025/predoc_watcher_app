# -*- coding: utf-8 -*-
"""生成应用图标。

⚠ 关键：每个尺寸都**直接按整数像素块绘制**，全程不做任何缩放。

    早先的版本是画一张 256px 再交给 PIL 的 ICO 写入器去生成各档尺寸，
    但 PIL 内部用的是平滑重采样 —— 结果 3 色的像素画在 16px 帧里变成了
    150 多种颜色，任务栏上看就是一团糊。像素画一旦被非整数倍插值就完了。

托盘/任务栏实际只有 16~24px。这个尺寸下 6 个字母横排放不下（每个字母只剩 2px），
所以拆成 "pre" / "doc" 两行，用 3×5 的字模。
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

GW, GH = 3, 5           # 单字宽高（格）
GAP = 1                 # 字距 / 行距（格）
COLS = GW * 3 + GAP * 2         # 一行三个字 = 11 格
ROWS = GH * 2 + GAP             # 两行 = 11 格

BLACK = (24, 26, 30, 255)
WHITE = (255, 255, 255, 255)
ORANGE = (234, 122, 16, 255)
CLEAR = (0, 0, 0, 0)

# 字块占画布的比例。0.76 让字尽量撑满，四周只留一点点边 —— 小尺寸下更好认。
FILL = 0.76

# 往右的视觉补正（单位：格）。几何居中时看着偏左，因为左右两边的墨量差很多：
# 最左列是 p/d 的满高竖干（10 格墨），最右列只有 e/c 的上下两横（4 格墨）。
# 实测墨迹重心落在第 4.83 列而不是 5.00 列，偏左 0.17 格，这里正好抵消掉。
NUDGE_X = 0.2

ICO_SIZES = [16, 20, 24, 32, 40, 48, 64, 96, 128, 256]


def render(size):
    """在 size×size 上直接作画，每个"像素格"都是整数个真实像素。"""
    unit = max(1, round(size * FILL / COLS))
    while COLS * unit > size - 2 and unit > 1:      # 至少留 1px 边
        unit -= 1

    im = Image.new("RGBA", (size, size), CLEAR)
    px = im.load()

    # 底板铺满，再抠出像素风的圆角（阶梯状，跟着尺寸放大）
    for y in range(size):
        for x in range(size):
            px[x, y] = BLACK
    c = max(1, round(size / 16))
    for x in range(2 * c):
        for y in range(2 * c):
            if (x < c and y < 2 * c) or (x < 2 * c and y < c):
                px[x, y] = CLEAR
                px[size - 1 - x, y] = CLEAR
                px[x, size - 1 - y] = CLEAR
                px[size - 1 - x, size - 1 - y] = CLEAR

    ox0 = round((size - COLS * unit) / 2 + NUDGE_X * unit)
    oy0 = (size - ROWS * unit) // 2
    for row, (word, color) in enumerate((("pre", WHITE), ("doc", ORANGE))):
        for i, ch in enumerate(word):
            for gy, line in enumerate(GLYPH[ch]):
                for gx, on in enumerate(line):
                    if on != "#":
                        continue
                    x0 = ox0 + (i * (GW + GAP) + gx) * unit
                    y0 = oy0 + (row * (GH + GAP) + gy) * unit
                    for dy in range(unit):           # 整数块填充，不做缩放
                        for dx in range(unit):
                            x, y = x0 + dx, y0 + dy
                            if 0 <= x < size and 0 <= y < size:
                                px[x, y] = color
    return im


def main():
    frames = [render(s) for s in ICO_SIZES]
    static = BASE_DIR / "static"
    static.mkdir(exist_ok=True)

    # append_images 让 PIL 存下我画好的每一帧，而不是自己去重采样
    ico = BASE_DIR / "app.ico"
    frames[-1].save(ico, format="ICO",
                    sizes=[(s, s) for s in ICO_SIZES],
                    append_images=frames[:-1])

    render(256).save(static / "icon.png")
    render(32).save(static / "favicon.png")
    print("已生成 %s（%s）" % (ico, "/".join(str(s) for s in ICO_SIZES)))
    print("已生成 %s、%s" % (static / "icon.png", static / "favicon.png"))


if __name__ == "__main__":
    main()
