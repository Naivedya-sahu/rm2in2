from svgpathtools import svg2paths, Line
import math

SVG_FILE = "flat.svg"
OUT_FILE = "pen.txt"

MAX_STEP = 5.0      # max distance between sampled points (px)
GAP_PEN_UP = 8.0    # if jump > this, lift pen; else draw connecting line

def dist(p, q):
    return math.hypot(p[0] - q[0], p[1] - q[1])

paths, attrs = svg2paths(SVG_FILE)

strokes = []  # list of list[(x,y)]

for path in paths:
    pts = []
    for seg in path:
        if isinstance(seg, Line):
            # straight line: only endpoints
            if not pts:
                pts.append((round(seg.start.real), round(seg.start.imag)))
            pts.append((round(seg.end.real), round(seg.end.imag)))
        else:
            # curved segment: sample by arc length
            length = seg.length()
            n = max(1, int(length / MAX_STEP))
            for k in range(n + 1):
                t = k / n
                z = seg.point(t)
                x, y = round(z.real), round(z.imag)
                if not pts or (x, y) != pts[-1]:
                    pts.append((x, y))

    if pts:
        strokes.append(pts)

# Merge strokes with minimal pen lifts:
merged_sequences = []
current = []

for stroke in strokes:
    if not stroke:
        continue
    if not current:
        current = stroke[:]
        continue
    # distance between last of current and first of next
    if dist(current[-1], stroke[0]) <= GAP_PEN_UP:
        # continue same pen stroke
        current.extend(stroke)
    else:
        # finish current and start a new one
        merged_sequences.append(current)
        current = stroke[:]

if current:
    merged_sequences.append(current)

# Emit PEN commands
# Don't merge all strokes into one; each SVG path -> one pen stroke sequence
with open(OUT_FILE, "w") as f:
    for pts in strokes:
        if not pts:
            continue
        x0, y0 = pts[0]
        f.write("PEN_UP\n")
        f.write(f"PEN_MOVE {x0} {y0}\n")
        f.write(f"PEN_DOWN {x0} {y0}\n")
        for x, y in pts[1:]:
            f.write(f"PEN_MOVE {x} {y}\n")
        f.write("PEN_UP\n")
