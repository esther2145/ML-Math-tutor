from pathlib import Path

from PIL import Image
from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt


ROOT = Path(__file__).resolve().parent.parent
SOURCE_POSTER = Path(r"C:\Users\kicae\Downloads\G-RAFT_Research_Poster.pptx.png")
OUTPUT_DIR = ROOT / "deliverables"
ASSET_DIR = OUTPUT_DIR / "assets"
OUTPUT_PPTX = OUTPUT_DIR / "G-RAFT_Closed_Loop_Supervisor_Poster.pptx"
LOGO_ASSET = ASSET_DIR / "ucu_wordmark.png"

SLIDE_W = 13.333
SLIDE_H = 7.5

NAVY = "0D2A49"
BLUE = "145B7D"
TEAL = "0F7658"
BROWN = "825014"
PURPLE = "70206F"
GREEN = "2D643F"
GOLD = "D99B00"
PALE_GOLD = "FFF6D8"
PALE_BLUE = "F1F6FA"
PALE_GREEN = "EEF7ED"
PALE_RED = "FBE9E9"
PALE_ORANGE = "FFF1E5"
LIGHT_BG = "EDF2F6"
MID_GREY = "B9C8D4"
TEXT = "17324D"
WHITE = "FFFFFF"
MUTED = "5D7185"


def rgb(hex_color: str) -> RGBColor:
    return RGBColor.from_string(hex_color)


def add_rect(slide, x, y, w, h, fill, line=None, radius=False):
    shape_type = MSO_SHAPE.ROUNDED_RECTANGLE if radius else MSO_SHAPE.RECTANGLE
    shape = slide.shapes.add_shape(
        shape_type,
        Inches(x),
        Inches(y),
        Inches(w),
        Inches(h),
    )
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(line or fill)
    shape.line.width = Pt(0.7)
    return shape


def add_text(
    slide,
    text,
    x,
    y,
    w,
    h,
    size=8,
    color=TEXT,
    bold=False,
    align=PP_ALIGN.LEFT,
    valign=MSO_ANCHOR.TOP,
    font="Arial",
    margin=0.02,
    italic=False,
):
    box = slide.shapes.add_textbox(
        Inches(x), Inches(y), Inches(w), Inches(h)
    )
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    frame.paragraphs[0].text = text
    # Newlines become separate PowerPoint paragraphs. Apply formatting to every
    # paragraph/run so Office does not fall back to its large default font.
    for paragraph in frame.paragraphs:
        paragraph.alignment = align
        paragraph.space_after = Pt(0)
        paragraph.space_before = Pt(0)
        paragraph.line_spacing = 1.0
        for run in paragraph.runs:
            run.font.name = font
            run.font.size = Pt(size)
            run.font.bold = bold
            run.font.italic = italic
            run.font.color.rgb = rgb(color)
    return box


def add_rule(slide, x, y, w, color=GOLD, height=0.045):
    return add_rect(slide, x, y, w, height, color)


def add_section_header(slide, title, x, y, w, color):
    add_rect(slide, x, y, w, 0.31, color)
    add_text(
        slide,
        title,
        x + 0.12,
        y + 0.02,
        w - 0.24,
        0.23,
        size=8.2,
        color=WHITE,
        bold=True,
        valign=MSO_ANCHOR.MIDDLE,
    )


def add_issue_card(slide, title, body, x, y, w, fill, accent):
    add_rect(slide, x, y, w, 0.34, fill, line=fill)
    add_rect(slide, x, y, 0.07, 0.34, accent)
    add_text(slide, title, x + 0.12, y + 0.04, w - 0.18, 0.13, 7.5, accent, True)
    add_text(slide, body, x + 0.12, y + 0.18, w - 0.18, 0.12, 6.8, MUTED)


def add_objective(slide, number, text, x, y, w):
    add_rect(slide, x, y, 0.29, 0.29, BLUE, radius=True)
    add_text(
        slide,
        str(number),
        x,
        y,
        0.29,
        0.29,
        7.8,
        WHITE,
        True,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )
    add_text(slide, text, x + 0.38, y - 0.005, w - 0.38, 0.32, 7.25, TEXT)


def add_step(slide, number, title, body, x, y, w, color, planned=False):
    add_rect(slide, x, y, w, 0.98, PALE_BLUE, line=MID_GREY)
    add_rect(slide, x, y, 0.43, 0.98, color)
    add_text(
        slide,
        str(number),
        x,
        y,
        0.43,
        0.98,
        16,
        WHITE,
        True,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )
    add_text(slide, title, x + 0.52, y + 0.10, w - 0.68, 0.20, 8.1, color, True)
    add_text(slide, body, x + 0.52, y + 0.35, w - 0.66, 0.50, 7.15, TEXT)
    if planned:
        add_rect(slide, x + w - 0.80, y + 0.08, 0.68, 0.18, GOLD, radius=True)
        add_text(
            slide,
            "NEXT PHASE",
            x + w - 0.80,
            y + 0.08,
            0.68,
            0.18,
            5.8,
            NAVY,
            True,
            PP_ALIGN.CENTER,
            MSO_ANCHOR.MIDDLE,
            margin=0,
        )


def add_literature_card(slide, citation, description, x, y, w):
    add_rect(slide, x, y, w, 0.51, PALE_BLUE, line=MID_GREY)
    add_rect(slide, x, y, 0.07, 0.51, GOLD)
    add_text(slide, citation, x + 0.14, y + 0.06, w - 0.20, 0.15, 7.1, BLUE, True)
    add_text(slide, description, x + 0.14, y + 0.23, w - 0.20, 0.22, 6.6, TEXT)


def add_metric(slide, value, label, x, y, w):
    add_rect(slide, x, y, w, 0.95, NAVY, line=WHITE)
    add_text(
        slide,
        value,
        x,
        y + 0.10,
        w,
        0.32,
        12.8,
        GOLD,
        True,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )
    add_text(
        slide,
        label,
        x + 0.03,
        y + 0.52,
        w - 0.06,
        0.28,
        6.3,
        "C7D3DF",
        False,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )


def make_wordmark_crop():
    ASSET_DIR.mkdir(parents=True, exist_ok=True)
    source = Image.open(SOURCE_POSTER).convert("RGB")
    crop = source.crop((0, 0, 545, 133))
    crop.save(LOGO_ASSET, quality=95)


def build_poster():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    make_wordmark_crop()

    deck = Presentation()
    deck.slide_width = Inches(SLIDE_W)
    deck.slide_height = Inches(SLIDE_H)
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = rgb(LIGHT_BG)

    # Header
    add_rect(slide, 0, 0, 5.68, 1.37, WHITE)
    slide.shapes.add_picture(
        str(LOGO_ASSET), Inches(0.02), Inches(0.02), width=Inches(5.62), height=Inches(1.34)
    )
    add_rect(slide, 5.68, 0, SLIDE_W - 5.68, 1.37, NAVY)
    add_text(
        slide,
        "G-RAFT: A CLOSED-LOOP GRAPH–RETRIEVAL TUTOR",
        5.87,
        0.16,
        7.20,
        0.38,
        20.2,
        WHITE,
        True,
        valign=MSO_ANCHOR.MIDDLE,
    )
    add_text(
        slide,
        "Grounded, verifiable and adaptive primary mathematics support",
        5.88,
        0.60,
        7.10,
        0.28,
        12.2,
        "C9D6E2",
    )
    add_text(
        slide,
        "ESTHER KICA  |  M24B38/010",
        5.88,
        0.96,
        6.90,
        0.24,
        10.5,
        WHITE,
    )
    add_rule(slide, 0, 1.37, SLIDE_W, GOLD, 0.06)

    # Body panels
    body_y = 1.50
    body_h = 5.65
    gap = 0.14
    margin = 0.12
    col_w = (SLIDE_W - 2 * margin - 2 * gap) / 3
    x1 = margin
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap
    for x in (x1, x2, x3):
        add_rect(slide, x, body_y, col_w, body_h, WHITE, line="D5E0E8")

    # Left column
    add_section_header(slide, "BACKGROUND, RESEARCH GAP & OBJECTIVES", x1, body_y, col_w, NAVY)
    ix = x1 + 0.15
    iw = col_w - 0.30
    add_text(slide, "The challenge in AI-supported mathematics", ix, 1.86, iw, 0.18, 8.0, BLUE, True)
    add_text(
        slide,
        "Primary mathematics requires correct steps, curriculum alignment and timely feedback. One-shot LLM answers can sound convincing while hiding reasoning or factual errors.",
        ix,
        2.09,
        iw,
        0.39,
        7.3,
        TEXT,
    )
    add_issue_card(slide, "Hallucinated answers", "Confident output may still be mathematically wrong.", ix, 2.50, iw, PALE_RED, "C32721")
    add_issue_card(slide, "Weak curriculum grounding", "Generic responses may ignore grade and prerequisite order.", ix, 2.90, iw, PALE_ORANGE, "C96916")
    add_issue_card(slide, "No performance feedback loop", "Errors are rarely verified, corrected and reused for improvement.", ix, 3.30, iw, PALE_GOLD, BROWN)
    add_rule(slide, ix, 3.75, iw)
    add_text(slide, "Why this matters in Uganda", ix, 3.89, iw, 0.17, 7.8, BLUE, True)
    add_text(
        slide,
        "Large classes and limited access to individual tutoring create demand for scalable support. The system aligns with SDG 4, Uganda Vision 2040 and national STEM priorities.",
        ix,
        4.14,
        iw,
        0.40,
        7.15,
        TEXT,
    )
    add_rule(slide, ix, 4.64, iw)
    add_text(slide, "Research aim", ix, 4.78, iw, 0.17, 7.8, BLUE, True)
    add_text(
        slide,
        "Design and evaluate a closed-loop, graph-grounded mathematics tutor that improves answer reliability and adapts from verified feedback.",
        ix,
        5.00,
        iw,
        0.35,
        7.15,
        TEXT,
    )
    add_text(slide, "Objectives", ix, 5.39, iw, 0.17, 7.8, BLUE, True)
    add_objective(slide, 1, "Represent curriculum concepts and prerequisites in Neo4j.", ix, 5.62, iw)
    add_objective(slide, 2, "Retrieve grade-aware evidence from Qdrant.", ix, 5.98, iw)
    add_objective(slide, 3, "Verify arithmetic and refine weak answers in a loop.", ix, 6.34, iw)
    add_objective(slide, 4, "Evaluate accuracy, grounding, latency and usability.", ix, 6.70, iw)

    # Middle column
    add_section_header(slide, "METHODOLOGY: G-RAFT CLOSED LOOP", x2, body_y, col_w, BLUE)
    mx = x2 + 0.15
    mw = col_w - 0.30
    add_text(
        slide,
        "The prototype combines structured curriculum knowledge, semantic retrieval, local generation and deterministic verification. The next phase closes the loop using evaluator and learner feedback.",
        mx,
        1.88,
        mw,
        0.39,
        7.1,
        TEXT,
    )
    add_step(
        slide,
        1,
        "GROUND — Curriculum Knowledge Graph",
        "Neo4j stores 37 nodes and 39 relationships: grades, topics, concepts, examples and prerequisite paths.",
        mx,
        2.26,
        mw,
        BLUE,
    )
    add_step(
        slide,
        2,
        "RETRIEVE — Grade-Aware Evidence",
        "Qdrant retrieves relevant learning materials using semantic similarity, grade filters and a confidence threshold.",
        mx,
        3.34,
        mw,
        TEAL,
    )
    add_step(
        slide,
        3,
        "GENERATE + VERIFY — Hybrid Tutor",
        "Llama 3.2:3B explains grounded context; a restricted arithmetic engine bypasses the LLM for explicit calculations.",
        mx,
        4.42,
        mw,
        BROWN,
    )
    add_step(
        slide,
        4,
        "FEEDBACK + REFINE — Loop Engineering",
        "Check correctness, grounding and learner response. Retry with targeted feedback; log weak cases to improve prompts, retrieval and content.",
        mx,
        5.50,
        mw,
        PURPLE,
        planned=True,
    )
    add_rect(slide, mx, 6.61, mw, 0.38, PALE_GOLD, line=GOLD, radius=True)
    add_text(
        slide,
        "↻  ASK → GROUND → RETRIEVE → GENERATE → VERIFY → REFINE → LEARN",
        mx + 0.07,
        6.64,
        mw - 0.14,
        0.29,
        6.8,
        NAVY,
        True,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )

    # Right column
    add_section_header(slide, "LITERATURE, PROTOTYPE STATUS & EVALUATION", x3, body_y, col_w, GREEN)
    rx = x3 + 0.15
    rw = col_w - 0.30
    add_text(slide, "Key related work", rx, 1.86, rw, 0.18, 8.0, BLUE, True)
    add_literature_card(slide, "Lewis et al. (2020) — RAG", "Combines parametric generation with retrieved external evidence.", rx, 2.08, rw)
    add_literature_card(slide, "Zhang et al. (2024) — RAFT", "Trains models to use relevant evidence and ignore distractor documents.", rx, 2.65, rw)
    add_literature_card(slide, "Edge et al. (2024) — GraphRAG", "Uses graph structure to support broader, connected retrieval and synthesis.", rx, 3.22, rw)
    add_literature_card(slide, "Madaan et al. (2023) — Self-Refine", "Iterative feedback and refinement can improve first-pass LLM outputs.", rx, 3.79, rw)
    add_rule(slide, rx, 4.39, rw)
    add_text(slide, "Working prototype — August 2026", rx, 4.52, rw, 0.18, 8.0, BLUE, True)
    metric_gap = 0.02
    metric_w = (rw - 3 * metric_gap) / 4
    add_metric(slide, "37", "Graph\nnodes", rx, 4.78, metric_w)
    add_metric(slide, "39", "Graph\nrelations", rx + metric_w + metric_gap, 4.78, metric_w)
    add_metric(slide, "10", "Learning\nmaterials", rx + 2 * (metric_w + metric_gap), 4.78, metric_w)
    add_metric(slide, "22", "Automated\ntests", rx + 3 * (metric_w + metric_gap), 4.78, metric_w)
    add_text(slide, "Evaluation plan", rx, 5.86, rw, 0.18, 8.0, BLUE, True)
    add_rect(slide, rx, 6.10, rw, 0.63, PALE_GREEN, line="A8CDA8")
    add_text(
        slide,
        "Correctness  •  grounding fidelity  •  hallucination rate  •  retrieval relevance\nresponse latency  •  teacher/learner usability  •  loop improvement per retry",
        rx + 0.10,
        6.17,
        rw - 0.20,
        0.41,
        6.7,
        GREEN,
        False,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )
    add_rect(slide, rx, 6.80, rw, 0.22, PALE_GOLD, line=GOLD, radius=True)
    add_text(
        slide,
        "STATUS: Working grounded tutor; closed-loop refinement is the proposed contribution.",
        rx + 0.05,
        6.80,
        rw - 0.10,
        0.22,
        5.9,
        NAVY,
        True,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )

    # Footer
    add_rect(slide, 0, 7.23, SLIDE_W, 0.27, NAVY)
    add_rule(slide, 0, 7.20, SLIDE_W, GOLD, 0.035)
    footer = (
        "Esther Kica  •  Uganda Christian University  •  Department of Computing & Technology  •  "
        "BSc Computer/Data Science  |  References: Lewis 2020; Cobbe 2021; Madaan 2023; Zhang 2024; Edge 2024"
    )
    add_text(
        slide,
        footer,
        0.20,
        7.26,
        SLIDE_W - 0.40,
        0.16,
        5.3,
        "C8D5E0",
        False,
        PP_ALIGN.CENTER,
        MSO_ANCHOR.MIDDLE,
        margin=0,
    )

    deck.save(OUTPUT_PPTX)
    print(OUTPUT_PPTX)


if __name__ == "__main__":
    build_poster()
