from pathlib import Path

from pptx import Presentation
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from pptx.enum.text import MSO_ANCHOR, PP_ALIGN
from pptx.util import Inches, Pt

ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = ROOT / "deliverables"
OUTPUT_PPTX = OUTPUT_DIR / "G-RAFT_Math_Tutor_Poster.pptx"

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
    shape = slide.shapes.add_shape(shape_type, Inches(x), Inches(y), Inches(w), Inches(h))
    shape.fill.solid()
    shape.fill.fore_color.rgb = rgb(fill)
    shape.line.color.rgb = rgb(line or fill)
    shape.line.width = Pt(0.7)
    return shape


def add_text(slide, text, x, y, w, h, size=8, color=TEXT, bold=False, align=PP_ALIGN.LEFT, valign=MSO_ANCHOR.TOP, font="Arial", margin=0.02, italic=False):
    box = slide.shapes.add_textbox(Inches(x), Inches(y), Inches(w), Inches(h))
    frame = box.text_frame
    frame.clear()
    frame.word_wrap = True
    frame.margin_left = Inches(margin)
    frame.margin_right = Inches(margin)
    frame.margin_top = Inches(margin)
    frame.margin_bottom = Inches(margin)
    frame.vertical_anchor = valign
    frame.paragraphs[0].text = text
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


def add_section_header(slide, title, x, y, w, color):
    add_rect(slide, x, y, w, 0.31, color)
    add_text(slide, title, x + 0.12, y + 0.02, w - 0.24, 0.23, size=8.2, color=WHITE, bold=True, valign=MSO_ANCHOR.MIDDLE)


def add_issue_card(slide, title, body, x, y, w, fill, accent):
    add_rect(slide, x, y, w, 0.34, fill, line=fill)
    add_rect(slide, x, y, 0.07, 0.34, accent)
    add_text(slide, title, x + 0.12, y + 0.04, w - 0.18, 0.13, 7.5, accent, True)
    add_text(slide, body, x + 0.12, y + 0.18, w - 0.18, 0.12, 6.8, MUTED)


def add_objective(slide, number, text_line, x, y, w):
    add_rect(slide, x, y, 0.29, 0.29, BLUE, radius=True)
    add_text(slide, str(number), x, y, 0.29, 0.29, 7.8, WHITE, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)
    add_text(slide, text_line, x + 0.38, y - 0.005, w - 0.38, 0.32, 7.25, TEXT)


def add_step(slide, number, title, body, x, y, w, color, planned=False):
    add_rect(slide, x, y, w, 0.98, PALE_BLUE, line=MID_GREY)
    add_rect(slide, x, y, 0.43, 0.98, color)
    add_text(slide, str(number), x, y, 0.43, 0.98, 16, WHITE, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)
    add_text(slide, title, x + 0.52, y + 0.10, w - 0.68, 0.20, 8.1, color, True)
    add_text(slide, body, x + 0.52, y + 0.35, w - 0.66, 0.50, 7.15, TEXT)
    if planned:
        add_rect(slide, x + w - 0.80, y + 0.08, 0.68, 0.18, GOLD, radius=True)
        add_text(slide, 'NEXT PHASE', x + w - 0.80, y + 0.08, 0.68, 0.18, 5.8, NAVY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)


def add_metric(slide, value, label, x, y, w):
    add_rect(slide, x, y, w, 0.95, NAVY, line=WHITE)
    add_text(slide, value, x, y + 0.10, w, 0.32, 12.8, GOLD, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)
    add_text(slide, label, x + 0.03, y + 0.52, w - 0.06, 0.28, 6.3, 'C7D3DF', False, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)


def build_poster():
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    deck = Presentation()
    deck.slide_width = Inches(13.333)
    deck.slide_height = Inches(7.5)
    slide = deck.slides.add_slide(deck.slide_layouts[6])
    background = slide.background.fill
    background.solid()
    background.fore_color.rgb = rgb(LIGHT_BG)

    add_rect(slide, 0, 0, 5.68, 1.37, WHITE)
    add_rect(slide, 5.68, 0, 13.333 - 5.68, 1.37, NAVY)
    add_text(slide, 'G-RAFT: MATH TUTOR', 5.87, 0.18, 7.20, 0.38, 20.2, WHITE, True, valign=MSO_ANCHOR.MIDDLE)
    add_text(slide, 'Curriculum-aware AI tutor for primary mathematics', 5.88, 0.62, 7.10, 0.28, 12.2, 'C9D6E2')
    add_text(slide, 'NEO4J  •  QDRANT  •  OLLAMA  •  FASTAPI', 5.88, 0.96, 6.90, 0.24, 10.5, WHITE)

    body_y = 1.50
    body_h = 5.65
    gap = 0.14
    margin = 0.12
    col_w = (13.333 - 2 * margin - 2 * gap) / 3
    x1 = margin
    x2 = x1 + col_w + gap
    x3 = x2 + col_w + gap
    for x in (x1, x2, x3):
        add_rect(slide, x, body_y, col_w, body_h, WHITE, line='D5E0E8')

    add_section_header(slide, 'BACKGROUND, RESEARCH GAP & OBJECTIVES', x1, body_y, col_w, NAVY)
    ix = x1 + 0.15
    iw = col_w - 0.30
    add_text(slide, 'The challenge in AI tutoring', ix, 1.86, iw, 0.18, 8.0, BLUE, True)
    add_text(slide, 'Primary mathematics learning requires correct step-by-step reasoning, safe guidance and strong curriculum alignment. One-shot generative answers can sound convincing while still being wrong.', ix, 2.09, iw, 0.39, 7.3, TEXT)
    add_issue_card(slide, 'Hallucinated answers', 'The model may produce confident but mathematically wrong responses.', ix, 2.50, iw, PALE_RED, 'C32721')
    add_issue_card(slide, 'Weak curriculum grounding', 'Generic answers may skip prerequisite order or grade-level expectations.', ix, 2.90, iw, PALE_ORANGE, 'C96916')
    add_issue_card(slide, 'No verification loop', 'Errors are rarely checked, corrected and fed back into better tutoring.', ix, 3.30, iw, PALE_GOLD, BROWN)
    add_text(slide, 'Research aim', ix, 4.78, iw, 0.17, 7.8, BLUE, True)
    add_text(slide, 'Build a graph-grounded tutor that combines retrieval, verification and learner feedback to improve correctness and trust.', ix, 5.00, iw, 0.35, 7.15, TEXT)
    add_text(slide, 'Objectives', ix, 5.39, iw, 0.17, 7.8, BLUE, True)
    add_objective(slide, 1, 'Represent curriculum concepts, grades and prerequisites in Neo4j.', ix, 5.62, iw)
    add_objective(slide, 2, 'Retrieve grade-aware evidence with Qdrant semantic search.', ix, 5.98, iw)
    add_objective(slide, 3, 'Verify arithmetic and generate grounded mathematical explanations.', ix, 6.34, iw)
    add_objective(slide, 4, 'Support teacher/learner workflows and iterative improvement.', ix, 6.70, iw)

    add_section_header(slide, 'METHODOLOGY: CLOSED LOOP', x2, body_y, col_w, BLUE)
    mx = x2 + 0.15
    mw = col_w - 0.30
    add_text(slide, 'The system combines structured curriculum knowledge, retrieval, generation and deterministic verification in one adaptive loop.', mx, 1.88, mw, 0.39, 7.1, TEXT)
    add_step(slide, 1, 'GRAPH — Curriculum Knowledge', 'Neo4j stores concepts, examples, grades and prerequisite paths for the mathematics curriculum.', mx, 2.26, mw, BLUE)
    add_step(slide, 2, 'RETRIEVE — Learning Evidence', 'Qdrant finds relevant materials using semantic similarity and grade-aware constraints.', mx, 3.34, mw, TEAL)
    add_step(slide, 3, 'GENERATE + VERIFY', 'The model explains the material and arithmetic checks validate the final answer before it is shown.', mx, 4.42, mw, BROWN)
    add_step(slide, 4, 'REFINE — Learning Loop', 'Weak cases are reviewed, corrected and reused to improve future retrieval and generation quality.', mx, 5.50, mw, PURPLE, planned=True)
    add_rect(slide, mx, 6.61, mw, 0.38, PALE_GOLD, line=GOLD, radius=True)
    add_text(slide, 'ASK → GROUND → RETRIEVE → GENERATE → VERIFY → LEARN', mx + 0.07, 6.64, mw - 0.14, 0.29, 6.8, NAVY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)

    add_section_header(slide, 'SYSTEM STACK & EVALUATION', x3, body_y, col_w, GREEN)
    rx = x3 + 0.15
    rw = col_w - 0.30
    add_text(slide, 'Core technologies', rx, 1.86, rw, 0.18, 8.0, BLUE, True)
    for i, line in enumerate([
        'Python and FastAPI backend',
        'Neo4j knowledge graph for curriculum structure',
        'Qdrant vector database for material retrieval',
        'Ollama local LLM for natural explanations',
        'Streamlit and React learner interfaces',
        'Docker-based deployment and local orchestration',
    ]):
        add_text(slide, '• ' + line, rx, 2.10 + i * 0.22, rw, 0.14, 6.7, TEXT)

    add_text(slide, 'Evaluation focus', rx, 4.85, rw, 0.18, 8.0, BLUE, True)
    metric_gap = 0.02
    metric_w = (rw - 3 * metric_gap) / 4
    add_metric(slide, '37', 'Curriculum\nnodes', rx, 5.08, metric_w)
    add_metric(slide, '39', 'Relations', rx + metric_w + metric_gap, 5.08, metric_w)
    add_metric(slide, '10', 'Starter\nmaterials', rx + 2 * (metric_w + metric_gap), 5.08, metric_w)
    add_metric(slide, '22', 'Automated\ntests', rx + 3 * (metric_w + metric_gap), 5.08, metric_w)

    add_rect(slide, rx, 6.10, rw, 0.63, PALE_GREEN, line='A8CDA8')
    add_text(slide, 'Correctness  •  grounding fidelity  •  hallucination control  •  retrieval relevance\nResponse latency  •  learner usability  •  iterative improvement', rx + 0.10, 6.17, rw - 0.20, 0.41, 6.7, GREEN, False, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)
    add_rect(slide, rx, 6.80, rw, 0.22, PALE_GOLD, line=GOLD, radius=True)
    add_text(slide, 'STATUS: Working tutor prototype with graph-grounded reasoning and verification pipeline.', rx + 0.05, 6.80, rw - 0.10, 0.22, 5.9, NAVY, True, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)

    add_rect(slide, 0, 7.23, 13.333, 0.27, NAVY)
    footer = 'G-RAFT Math Tutor  •  Department of Computing & Technology  •  AI for adaptive mathematics learning  •  Built from project root sources'
    add_text(slide, footer, 0.20, 7.26, 13.333 - 0.40, 0.16, 5.3, 'C8D5E0', False, PP_ALIGN.CENTER, MSO_ANCHOR.MIDDLE, margin=0)

    deck.save(OUTPUT_PPTX)
    print(f'Poster created: {OUTPUT_PPTX}')


if __name__ == '__main__':
    build_poster()
