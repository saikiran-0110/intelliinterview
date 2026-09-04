"""Render IntelliInterview ERD as SVG + PNG with large, real system fonts."""

from __future__ import annotations

import math
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

OUT_DIR = Path(__file__).resolve().parent
WIDTH = 2200
HEIGHT = 1560
BOX_W = 400
BOX_H = 108
HEADER_H = 34

# Light fills + dark text so labels stay readable when the image is scaled.
DOMAINS = {
    "identity": ("Identity", "#D9E6F5", "#14325C"),
    "documents": ("Documents", "#D4EFE8", "#0F4C3F"),
    "matching": ("Matching", "#E8DCF6", "#4A2D73"),
    "questions": ("Questions", "#F8E4CC", "#6B3F12"),
    "session": ("Live interview", "#D8EFDA", "#1B4D2B"),
    "outcomes": ("Outcomes", "#F5DCE8", "#6B2448"),
}

TABLES = [
    {
        "id": "otp_challenges",
        "domain": "identity",
        "x": 48,
        "y": 168,
        "lines": ["PK id", "email  purpose  code_hash"],
    },
    {
        "id": "users",
        "domain": "identity",
        "x": 48,
        "y": 312,
        "lines": ["PK id", "email  role  password_hash"],
    },
    {
        "id": "bias_alerts",
        "domain": "identity",
        "x": 48,
        "y": 456,
        "lines": ["PK id", "FK recruiter_id → users"],
    },
    {
        "id": "job_specifications",
        "domain": "documents",
        "x": 48,
        "y": 640,
        "lines": ["PK id", "FK created_by → users"],
    },
    {
        "id": "candidate_cvs",
        "domain": "documents",
        "x": 48,
        "y": 784,
        "lines": ["PK id", "FK uploaded_by → users"],
    },
    {
        "id": "job_applications",
        "domain": "matching",
        "x": 520,
        "y": 168,
        "lines": ["PK id", "FK job_spec_id  candidate_user_id"],
    },
    {
        "id": "gap_analyses",
        "domain": "matching",
        "x": 520,
        "y": 360,
        "lines": ["PK id", "FK cv_id  job_spec_id"],
    },
    {
        "id": "preparation_packs",
        "domain": "matching",
        "x": 520,
        "y": 552,
        "lines": ["PK id", "FK cv_id  job_spec_id  user"],
    },
    {
        "id": "question_plans",
        "domain": "questions",
        "x": 520,
        "y": 760,
        "lines": ["PK id", "FK gap_analysis_id"],
    },
    {
        "id": "interview_questions",
        "domain": "questions",
        "x": 520,
        "y": 920,
        "lines": ["PK id", "FK plan_id → question_plans"],
    },
    {
        "id": "interview_slot_suggestions",
        "domain": "session",
        "x": 992,
        "y": 168,
        "lines": ["PK id", "FK session_id  proposed_by"],
    },
    {
        "id": "interview_sessions",
        "domain": "session",
        "x": 992,
        "y": 360,
        "lines": ["PK id", "FK plan  gap  cv  job  users"],
    },
    {
        "id": "interview_turns",
        "domain": "session",
        "x": 992,
        "y": 552,
        "lines": ["PK id", "FK session_id  plan_question_id"],
    },
    {
        "id": "interview_turn_evaluations",
        "domain": "session",
        "x": 992,
        "y": 744,
        "lines": ["PK id", "UQ FK turn_id  (1:1)"],
    },
    {
        "id": "notifications",
        "domain": "outcomes",
        "x": 1464,
        "y": 168,
        "lines": ["PK id", "FK user_id  related_session_id"],
    },
    {
        "id": "interview_reports",
        "domain": "outcomes",
        "x": 1464,
        "y": 360,
        "lines": ["PK id", "FK session_id  cv_id  job_spec_id"],
    },
    {
        "id": "candidate_feedbacks",
        "domain": "outcomes",
        "x": 1464,
        "y": 552,
        "lines": ["PK id", "FK session_id  report_id"],
    },
]

# parent -> child, optional dashed, one_to_one
EDGES = [
    ("job_specifications", "gap_analyses", False, False),
    ("candidate_cvs", "gap_analyses", False, False),
    ("job_specifications", "job_applications", False, False),
    ("candidate_cvs", "job_applications", True, False),
    ("gap_analyses", "job_applications", True, False),
    ("job_specifications", "preparation_packs", False, False),
    ("candidate_cvs", "preparation_packs", False, False),
    ("gap_analyses", "question_plans", False, False),
    ("question_plans", "interview_questions", False, False),
    ("question_plans", "interview_sessions", False, False),
    ("gap_analyses", "interview_sessions", False, False),
    ("candidate_cvs", "interview_sessions", False, False),
    ("job_specifications", "interview_sessions", False, False),
    ("interview_sessions", "interview_slot_suggestions", False, False),
    ("interview_sessions", "interview_turns", False, False),
    ("interview_questions", "interview_turns", True, False),
    ("interview_turns", "interview_turn_evaluations", False, True),
    ("interview_sessions", "interview_turn_evaluations", False, False),
    ("interview_sessions", "interview_reports", False, False),
    ("job_specifications", "interview_reports", False, False),
    ("candidate_cvs", "interview_reports", False, False),
    ("interview_sessions", "candidate_feedbacks", False, False),
    ("interview_reports", "candidate_feedbacks", True, False),
    ("interview_sessions", "notifications", True, False),
    ("users", "bias_alerts", False, False),
    ("users", "job_specifications", True, False),
    ("users", "candidate_cvs", True, False),
]

BY_ID = {t["id"]: t for t in TABLES}


def font_path(bold: bool) -> str:
    root = Path(r"C:\Windows\Fonts")
    candidates = (
        ["segoeuib.ttf", "arialbd.ttf", "calibrib.ttf"]
        if bold
        else ["segoeui.ttf", "arial.ttf", "calibri.ttf"]
    )
    for name in candidates:
        path = root / name
        if path.exists():
            return str(path)
    raise FileNotFoundError("No TrueType font found in C:\\Windows\\Fonts")


def load_font(size: int, bold: bool = False) -> ImageFont.FreeTypeFont:
    return ImageFont.truetype(font_path(bold), size)


def box_anchor(table: dict, side: str) -> tuple[float, float]:
    x, y = table["x"], table["y"]
    if side == "right":
        return x + BOX_W, y + BOX_H / 2
    if side == "left":
        return x, y + BOX_H / 2
    if side == "bottom":
        return x + BOX_W / 2, y + BOX_H
    return x + BOX_W / 2, y


def choose_sides(parent: dict, child: dict) -> tuple[str, str]:
    if child["x"] >= parent["x"] + BOX_W - 8:
        return "right", "left"
    if parent["x"] >= child["x"] + BOX_W - 8:
        return "left", "right"
    if child["y"] >= parent["y"] + BOX_H:
        return "bottom", "top"
    return "top", "bottom"


def polyline(parent: dict, child: dict) -> list[tuple[float, float]]:
    ps, cs = choose_sides(parent, child)
    x1, y1 = box_anchor(parent, ps)
    x2, y2 = box_anchor(child, cs)
    if ps == "right" and cs == "left":
        mid = (x1 + x2) / 2
        return [(x1, y1), (mid, y1), (mid, y2), (x2, y2)]
    if ps == "left" and cs == "right":
        mid = (x1 + x2) / 2
        return [(x1, y1), (mid, y1), (mid, y2), (x2, y2)]
    if ps == "bottom" and cs == "top":
        mid = (y1 + y2) / 2
        return [(x1, y1), (x1, mid), (x2, mid), (x2, y2)]
    mid = (y1 + y2) / 2
    return [(x1, y1), (x1, mid), (x2, mid), (x2, y2)]


def crow_foot(draw: ImageDraw.ImageDraw, tip: tuple[float, float], toward: tuple[float, float], color: str) -> None:
    tx, ty = tip
    fx, fy = toward
    dx, dy = tx - fx, ty - fy
    length = math.hypot(dx, dy) or 1
    ux, uy = dx / length, dy / length
    px, py = -uy, ux
    base_x = tx - ux * 14
    base_y = ty - uy * 14
    draw.line([(tx, ty), (base_x + px * 8, base_y + py * 8)], fill=color, width=3)
    draw.line([(tx, ty), (base_x - px * 8, base_y - py * 8)], fill=color, width=3)
    draw.line([(tx, ty), (base_x, base_y)], fill=color, width=3)
    bar_x = tx - ux * 20
    bar_y = ty - uy * 20
    draw.line(
        [(bar_x + px * 8, bar_y + py * 8), (bar_x - px * 8, bar_y - py * 8)],
        fill=color,
        width=3,
    )


def render_png() -> Path:
    img = Image.new("RGB", (WIDTH, HEIGHT), "#FFFFFF")
    draw = ImageDraw.Draw(img)
    title_font = load_font(34, bold=True)
    sub_font = load_font(17)
    table_font = load_font(19, bold=True)
    body_font = load_font(15)
    legend_font = load_font(15)
    footer_font = load_font(14)

    draw.rectangle([0, 0, WIDTH, 124], fill="#F3F6FB")
    draw.text((48, 20), "IntelliInterview  —  Entity Relationship Diagram", font=title_font, fill="#12233F")
    draw.text(
        (48, 68),
        "PostgreSQL public schema   |   17 tables   |   Crow’s foot on the many side   |   Dashed line = optional foreign key   |   Green = 1:1",
        font=sub_font,
        fill="#3B4D66",
    )

    # Domain legend
    lx = 48
    for _key, (label, fill, ink) in DOMAINS.items():
        draw.rounded_rectangle([lx, 96, lx + 18, 114], radius=3, fill=fill, outline="#1B3354")
        draw.text((lx + 24, 94), label, font=legend_font, fill=ink)
        lx += 18 + 12 + int(legend_font.getlength(label)) + 22

    line_color = "#234468"
    dash_color = "#5C7594"
    one_color = "#1F6B4A"

    def draw_dashed(pts: list[tuple[float, float]], color: str) -> None:
        for i in range(len(pts) - 1):
            x1, y1 = pts[i]
            x2, y2 = pts[i + 1]
            seg_len = math.hypot(x2 - x1, y2 - y1) or 1
            ux, uy = (x2 - x1) / seg_len, (y2 - y1) / seg_len
            t = 0.0
            on = True
            while t < seg_len:
                nxt = min(t + (9 if on else 7), seg_len)
                if on:
                    draw.line(
                        [(x1 + ux * t, y1 + uy * t), (x1 + ux * nxt, y1 + uy * nxt)],
                        fill=color,
                        width=3,
                    )
                t = nxt
                on = not on

    for parent_id, child_id, optional, one_to_one in EDGES:
        parent, child = BY_ID[parent_id], BY_ID[child_id]
        pts = polyline(parent, child)
        color = one_color if one_to_one else (dash_color if optional else line_color)
        if optional:
            draw_dashed(pts, color)
        else:
            draw.line(pts, fill=color, width=3)
        crow_foot(draw, pts[-1], pts[-2], color)

    for table in TABLES:
        x, y = table["x"], table["y"]
        fill, ink = DOMAINS[table["domain"]][1], DOMAINS[table["domain"]][2]
        draw.rounded_rectangle(
            [x, y, x + BOX_W, y + BOX_H],
            radius=8,
            fill="#FFFFFF",
            outline="#1B3354",
            width=2,
        )
        draw.rectangle([x + 2, y + 2, x + BOX_W - 2, y + HEADER_H], fill=fill)
        draw.line([(x, y + HEADER_H), (x + BOX_W, y + HEADER_H)], fill="#1B3354", width=2)
        draw.text((x + 14, y + 6), table["id"], font=table_font, fill=ink)
        draw.text((x + 14, y + HEADER_H + 10), table["lines"][0], font=body_font, fill="#1A2A40")
        draw.text((x + 14, y + HEADER_H + 36), table["lines"][1], font=body_font, fill="#334155")

    draw.rectangle([0, HEIGHT - 88, WIDTH, HEIGHT], fill="#F3F6FB")
    draw.text(
        (48, HEIGHT - 68),
        "users is also referenced by applications, sessions, reports, feedback, notifications, question_plans and preparation_packs (omitted here so the hiring path stays readable).",
        font=footer_font,
        fill="#3B4D66",
    )
    draw.text(
        (48, HEIGHT - 40),
        "otp_challenges has no foreign keys (email codes can exist before a user row). Three keys commented in the pgAdmin dump are drawn: gap_analyses.cv_id, gap_analyses.job_spec_id, interview_questions.plan_id.",
        font=footer_font,
        fill="#3B4D66",
    )

    out = OUT_DIR / "intelliinterview-erd.png"
    img.save(out, "PNG", dpi=(180, 180))
    return out


def xml_escape(text: str) -> str:
    return (
        text.replace("&", "&amp;")
        .replace("<", "&lt;")
        .replace(">", "&gt;")
        .replace('"', "&quot;")
    )


def render_svg() -> Path:
    parts: list[str] = [
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{WIDTH}" height="{HEIGHT}" viewBox="0 0 {WIDTH} {HEIGHT}">',
        "<rect width='100%' height='100%' fill='#FFFFFF'/>",
        "<rect width='100%' height='124' fill='#F3F6FB'/>",
        "<text x='48' y='48' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='34' font-weight='700' fill='#12233F'>IntelliInterview  —  Entity Relationship Diagram</text>",
        "<text x='48' y='88' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='17' fill='#3B4D66'>PostgreSQL public schema   |   17 tables   |   Crow’s foot on the many side   |   Dashed line = optional foreign key   |   Green = 1:1</text>",
    ]
    lx = 48
    # Approximate legend widths used in PNG; SVG uses similar spacing.
    legend_x = 48
    for _key, (label, fill, ink) in DOMAINS.items():
        parts.append(
            f"<rect x='{legend_x}' y='98' width='16' height='16' rx='3' fill='{fill}' stroke='#1B3354'/>"
        )
        parts.append(
            f"<text x='{legend_x + 22}' y='111' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='15' font-weight='700' fill='{ink}'>{xml_escape(label)}</text>"
        )
        legend_x += 22 + 8 + len(label) * 8 + 18

    def path_from(pts: list[tuple[float, float]]) -> str:
        d = f"M {pts[0][0]:.1f} {pts[0][1]:.1f}"
        for x, y in pts[1:]:
            d += f" L {x:.1f} {y:.1f}"
        return d

    def foot_path(tip: tuple[float, float], toward: tuple[float, float]) -> str:
        tx, ty = tip
        fx, fy = toward
        dx, dy = tx - fx, ty - fy
        length = math.hypot(dx, dy) or 1
        ux, uy = dx / length, dy / length
        px, py = -uy, ux
        base_x = tx - ux * 14
        base_y = ty - uy * 14
        bar_x = tx - ux * 20
        bar_y = ty - uy * 20
        return (
            f"M {tx:.1f} {ty:.1f} L {base_x + px * 8:.1f} {base_y + py * 8:.1f} "
            f"M {tx:.1f} {ty:.1f} L {base_x - px * 8:.1f} {base_y - py * 8:.1f} "
            f"M {tx:.1f} {ty:.1f} L {base_x:.1f} {base_y:.1f} "
            f"M {bar_x + px * 8:.1f} {bar_y + py * 8:.1f} L {bar_x - px * 8:.1f} {bar_y - py * 8:.1f}"
        )

    for parent_id, child_id, optional, one_to_one in EDGES:
        parent, child = BY_ID[parent_id], BY_ID[child_id]
        pts = polyline(parent, child)
        color = "#1F6B4A" if one_to_one else ("#5C7594" if optional else "#234468")
        dash = " stroke-dasharray='9 7'" if optional else ""
        parts.append(
            f"<path d='{path_from(pts)}' fill='none' stroke='{color}' stroke-width='3' stroke-linejoin='round'{dash}/>"
        )
        parts.append(
            f"<path d='{foot_path(pts[-1], pts[-2])}' fill='none' stroke='{color}' stroke-width='3' stroke-linecap='round'/>"
        )

    for table in TABLES:
        x, y = table["x"], table["y"]
        fill, ink = DOMAINS[table["domain"]][1], DOMAINS[table["domain"]][2]
        parts.append(
            f"<rect x='{x}' y='{y}' width='{BOX_W}' height='{BOX_H}' rx='8' fill='#FFFFFF' stroke='#1B3354' stroke-width='2'/>"
        )
        parts.append(f"<rect x='{x}' y='{y}' width='{BOX_W}' height='{HEADER_H}' fill='{fill}'/>")
        parts.append(
            f"<path d='M {x} {y} h {BOX_W} v {HEADER_H} H {x} z' fill='{fill}'/>"
        )
        parts.append(
            f"<rect x='{x}' y='{y}' width='{BOX_W}' height='{HEADER_H}' rx='8' fill='{fill}'/>"
        )
        parts.append(
            f"<rect x='{x}' y='{y + 10}' width='{BOX_W}' height='{HEADER_H - 10}' fill='{fill}'/>"
        )
        parts.append(
            f"<line x1='{x}' y1='{y + HEADER_H}' x2='{x + BOX_W}' y2='{y + HEADER_H}' stroke='#1B3354' stroke-width='2'/>"
        )
        parts.append(
            f"<text x='{x + 14}' y='{y + 24}' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='19' font-weight='700' fill='{ink}'>{xml_escape(table['id'])}</text>"
        )
        parts.append(
            f"<text x='{x + 14}' y='{y + HEADER_H + 24}' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='15' fill='#1A2A40'>{xml_escape(table['lines'][0])}</text>"
        )
        parts.append(
            f"<text x='{x + 14}' y='{y + HEADER_H + 48}' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='15' fill='#334155'>{xml_escape(table['lines'][1])}</text>"
        )

    parts.append(f"<rect x='0' y='{HEIGHT - 88}' width='{WIDTH}' height='88' fill='#F3F6FB'/>")
    parts.append(
        f"<text x='48' y='{HEIGHT - 48}' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='14' fill='#3B4D66'>users is also referenced by applications, sessions, reports, feedback, notifications, question_plans and preparation_packs (omitted here so the hiring path stays readable).</text>"
    )
    parts.append(
        f"<text x='48' y='{HEIGHT - 24}' font-family='Segoe UI, Arial, Helvetica, sans-serif' font-size='14' fill='#3B4D66'>otp_challenges has no foreign keys. Three keys commented in the pgAdmin dump are drawn: gap_analyses.cv_id, gap_analyses.job_spec_id, interview_questions.plan_id.</text>"
    )
    parts.append("</svg>")
    out = OUT_DIR / "intelliinterview-erd.svg"
    out.write_text("\n".join(parts), encoding="utf-8")
    return out


def main() -> None:
    png = render_png()
    svg = render_svg()
    print(png)
    print(svg)


if __name__ == "__main__":
    main()
