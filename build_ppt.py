#!/usr/bin/env python3
"""
Convert LLMBook PDF slides into a properly formatted PPTX presentation.
Parses content structure (titles, bullet hierarchies, images) and rebuilds
slides with native text and template styling.
"""

import os
import re
from io import BytesIO
import pymupdf
from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN, MSO_ANCHOR
from pptx.enum.shapes import MSO_SHAPE

# ── Paths ──
SLIDES_DIR = "/home/user/llmbook-zh/llmbook-zh.github.io/slides"
OUTPUT_PATH = "/home/user/cc/大语言模型课件.pptx"
ASSET_DIR = "/tmp/claude-0/template_assets"

SLIDE_W = 12192000
SLIDE_H = 6858000
SCALE = 12700  # EMU per PDF point

# Template colors
BLUE_ACCENT = RGBColor(0x33, 0x33, 0xFF)
DARK_BLUE = RGBColor(0x01, 0x52, 0x8A)
LIGHT_BLUE_BG = RGBColor(0xE8, 0xEE, 0xF7)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY_TEXT = RGBColor(0x99, 0x99, 0x99)
RED_TITLE = RGBColor(0xA1, 0x00, 0x32)
BLACK = RGBColor(0x33, 0x33, 0x33)

CHAPTERS = [
    ("第一课", "初识大模型", [
        "1.1 语言模型发展历程.pdf",
        "1.2 大模型技术基础.pdf",
        "1.3 GPT+DeepSeek模型介绍.pdf",
    ]),
    ("第二课", "模型架构", [
        "2.1 Transformer模型.pdf",
        "2.2 模型详细配置.pdf",
        "2.3 长上下文模型和新型架构.pdf",
    ]),
    ("第三课", "预训练", [
        "3.1 预训练之数据工程.pdf",
        "3.2预训练之具体流程.pdf",
        "3.3预训练之训练优化与效率.pdf",
    ]),
    ("第四课", "指令微调", [
        "4.1 指令微调与常见策略.pdf",
        "4.2 轻量化微调.pdf",
    ]),
    ("第五课", "人类对齐", [
        "5.1 人类对齐之基础.pdf",
        "5.2 人类对齐之进阶.pdf",
    ]),
    ("第六课", "解码与部署", [
        "6.1 大模型解码.pdf",
        "6.2 解码效率分析与加速算法.pdf",
        "6.3 模型压缩.pdf",
    ]),
    ("第七课", "提示学习", [
        "7.1 提示工程.pdf",
        "7.2 上下文学习.pdf",
        "7.4 检索增强生成.pdf",
        "7.3 思维链提示.pdf",
    ]),
    ("第八课", "复杂推理", [
        "8.1 规划与智能体.pdf",
        "8.2 复杂推理与慢思考.pdf",
    ]),
    ("附录", "评测与资源", [
        "大模型评测.pdf",
        "大模型资源.pdf",
    ]),
]

BOOK_TITLE = "大语言模型"
BOOK_SUBTITLE = "从理论到实践"

# ── Font mapping ──
FONT_MAP = {
    "SimHei": "黑体", "KaiTi": "楷体", "FangSong": "仿宋",
    "SimSun": "宋体", "MicrosoftYaHei": "微软雅黑",
    "TimesNewRomanPSMT": "Times New Roman",
    "TimesNewRomanPS-BoldMT": "Times New Roman",
    "TimesNewRomanPS-ItalicMT": "Times New Roman",
    "TimesNewRomanPS-BoldItalicMT": "Times New Roman",
    "ArialMT": "Arial", "Arial-BoldMT": "Arial",
    "CambriaMath": "Cambria Math",
    "Wingdings-Regular": "Wingdings", "SymbolMT": "Symbol",
}


def map_font(pdf_font):
    if pdf_font in FONT_MAP:
        return FONT_MAP[pdf_font]
    for key, val in FONT_MAP.items():
        if key.lower() in pdf_font.lower():
            return val
    return pdf_font


def color_int_to_rgb(c):
    if c == 0:
        return BLACK
    return RGBColor((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)


def compress_image(img_data, max_w=1280, max_h=960, quality=60):
    try:
        img = Image.open(BytesIO(img_data))
        if img.width > max_w or img.height > max_h:
            img.thumbnail((max_w, max_h), Image.LANCZOS)
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        else:
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=quality, optimize=True)
        buf.seek(0)
        return buf
    except Exception:
        return BytesIO(img_data)


# ── Template slide builders ──

def add_header_bar(slide, chapter_label=""):
    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(3530600), Emu(6985), Emu(8661400), Emu(836295),
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = DARK_BLUE
    rect.line.fill.background()

    logo_path = os.path.join(ASSET_DIR, "图片 1.png")
    if os.path.exists(logo_path):
        slide.shapes.add_picture(logo_path, Emu(0), Emu(0), Emu(6342380), Emu(836295))

    if chapter_label:
        txbox = slide.shapes.add_textbox(Emu(0), Emu(0), Emu(SLIDE_W), Emu(770890))
        tf = txbox.text_frame
        tf.word_wrap = True
        run = tf.paragraphs[0].add_run()
        run.text = f"       {chapter_label}"
        run.font.size = Pt(40)
        run.font.bold = True
        run.font.name = "楷体"
        run.font.color.rgb = WHITE


def add_title_bar(slide, title_text, subtitle_text=""):
    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(0), Emu(836295), Emu(SLIDE_W), Emu(620000),
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = LIGHT_BLUE_BG
    rect.line.fill.background()

    # Blue left accent bar
    accent = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(0), Emu(836295), Emu(80000), Emu(620000),
    )
    accent.fill.solid()
    accent.fill.fore_color.rgb = BLUE_ACCENT
    accent.line.fill.background()

    txbox = slide.shapes.add_textbox(
        Emu(250000), Emu(860000), Emu(SLIDE_W - 400000), Emu(580000),
    )
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.LEFT
    run = p.add_run()
    run.text = title_text
    run.font.size = Pt(28)
    run.font.bold = True
    run.font.name = "黑体"
    run.font.color.rgb = DARK_BLUE

    if subtitle_text:
        run2 = p.add_run()
        run2.text = f"  {subtitle_text}"
        run2.font.size = Pt(22)
        run2.font.bold = True
        run2.font.name = "黑体"
        run2.font.color.rgb = BLUE_ACCENT


def add_bottom_decoration(slide):
    path = os.path.join(ASSET_DIR, "图片 5.png")
    if os.path.exists(path):
        slide.shapes.add_picture(path, Emu(0), Emu(5167054), Emu(SLIDE_W), Emu(1703387))


def make_cover_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header_bar(slide, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")
    add_bottom_decoration(slide)

    txbox = slide.shapes.add_textbox(Emu(376238), Emu(1500000), Emu(11541125), Emu(3500000))
    tf = txbox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = BOOK_TITLE
    run.font.size = Pt(54)
    run.font.bold = True
    run.font.name = "微软雅黑"
    run.font.color.rgb = DARK_BLUE

    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(8)
    run2 = p2.add_run()
    run2.text = BOOK_SUBTITLE
    run2.font.size = Pt(36)
    run2.font.name = "微软雅黑"
    run2.font.color.rgb = BLUE_ACCENT

    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(30)
    run3 = p3.add_run()
    run3.text = "基于《大语言模型：从理论到实践》课件整理"
    run3.font.size = Pt(20)
    run3.font.name = "黑体"
    run3.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    p4 = tf.add_paragraph()
    p4.alignment = PP_ALIGN.CENTER
    p4.space_before = Pt(8)
    run4 = p4.add_run()
    run4.text = "LLMBook-zh.github.io"
    run4.font.size = Pt(18)
    run4.font.name = "Times New Roman"
    run4.font.color.rgb = BLUE_ACCENT


def make_toc_slide(prs):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header_bar(slide, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")

    txbox = slide.shapes.add_textbox(Emu(500000), Emu(950000), Emu(3000000), Emu(600000))
    run = txbox.text_frame.paragraphs[0].add_run()
    run.text = "目  录"
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.name = "黑体"
    run.font.color.rgb = DARK_BLUE

    start_y = 1700000
    col1_x, col2_x = 800000, 6400000
    item_h, gap = 520000, 80000

    for idx, (num, title, _) in enumerate(CHAPTERS):
        x = col1_x if idx < 5 else col2_x
        y = start_y + (idx if idx < 5 else idx - 5) * (item_h + gap)

        diamond = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Emu(x), Emu(y), Emu(500000), Emu(440000))
        diamond.fill.solid()
        diamond.fill.fore_color.rgb = BLUE_ACCENT
        diamond.line.fill.background()
        if diamond.has_text_frame:
            diamond.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            r = diamond.text_frame.paragraphs[0].add_run()
            r.text = f"{idx+1:02d}" if idx < 8 else "A"
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.name = "Times New Roman"
            r.font.color.rgb = WHITE

        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Emu(x + 580000), Emu(y + 20000), Emu(4600000), Emu(400000),
        )
        rect.fill.solid()
        rect.fill.fore_color.rgb = LIGHT_BLUE_BG
        rect.line.fill.background()
        if rect.has_text_frame:
            rect.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            r = rect.text_frame.paragraphs[0].add_run()
            r.text = f"{num} {title}"
            r.font.size = Pt(18)
            r.font.bold = True
            r.font.name = "黑体"
            r.font.color.rgb = DARK_BLUE


def make_chapter_nav_slide(prs, current_idx):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header_bar(slide, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")

    txbox = slide.shapes.add_textbox(Emu(500000), Emu(950000), Emu(11000000), Emu(600000))
    r = txbox.text_frame.paragraphs[0].add_run()
    r.text = "当前章节"
    r.font.size = Pt(20)
    r.font.name = "黑体"
    r.font.color.rgb = GRAY_TEXT

    start_y = 1700000
    col1_x, col2_x = 800000, 6400000
    item_h, gap = 520000, 80000

    for idx, (num, title, _) in enumerate(CHAPTERS):
        cur = idx == current_idx
        x = col1_x if idx < 5 else col2_x
        y = start_y + (idx if idx < 5 else idx - 5) * (item_h + gap)

        diamond = slide.shapes.add_shape(MSO_SHAPE.DIAMOND, Emu(x), Emu(y), Emu(500000), Emu(440000))
        diamond.fill.solid()
        diamond.fill.fore_color.rgb = BLUE_ACCENT if cur else RGBColor(0xCC, 0xCC, 0xCC)
        diamond.line.fill.background()
        if diamond.has_text_frame:
            diamond.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            r = diamond.text_frame.paragraphs[0].add_run()
            r.text = f"{idx+1:02d}" if idx < 8 else "A"
            r.font.size = Pt(16)
            r.font.bold = True
            r.font.name = "Times New Roman"
            r.font.color.rgb = WHITE

        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Emu(x + 580000), Emu(y + 20000), Emu(4600000), Emu(400000),
        )
        rect.fill.solid()
        rect.fill.fore_color.rgb = BLUE_ACCENT if cur else LIGHT_BLUE_BG
        rect.line.fill.background()
        if rect.has_text_frame:
            rect.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            r = rect.text_frame.paragraphs[0].add_run()
            r.text = f"{num} {title}"
            r.font.size = Pt(18)
            r.font.bold = True
            r.font.name = "黑体"
            r.font.color.rgb = WHITE if cur else DARK_BLUE


# ── PDF content parsing ──

BULLET_RE = re.compile(r"^[➢▶●○■□◆◇•▪▸▹►▻→←↑↓⇒⇐⇑⇓✓✗✘✔✕☐☑☒★☆♦♠♣♥]\s*")

INDENT_THRESHOLDS = [70, 110, 140, 170, 200]


def detect_indent_level(x0, font_size):
    for i, thresh in enumerate(INDENT_THRESHOLDS):
        if x0 < thresh:
            return i
    return len(INDENT_THRESHOLDS)


def is_footer(text, y0, page_h):
    if "教材课件" in text:
        return True
    if y0 > page_h - 30 and len(text) < 40:
        return True
    return False


def is_url_ref(text):
    return text.strip().startswith("http://") or text.strip().startswith("https://")


def parse_pdf_page(page):
    """Parse a PDF page into structured content: title, body lines, images."""
    td = page.get_text("dict")
    page_h = page.rect.height
    page_w = page.rect.width

    title_text = ""
    body_lines = []
    image_blocks = []

    all_blocks = sorted(td["blocks"], key=lambda b: (b["bbox"][1], b["bbox"][0]))

    for block in all_blocks:
        if block["type"] == 1:
            bbox = block["bbox"]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            # Skip tiny images and the recurring header logo (~144x154 in PDF coords ~11x12pt)
            if w > 60 and h > 40 and not (w < 20 and h < 20):
                image_blocks.append(bbox)
            continue

        if block["type"] != 0:
            continue

        for line in block["lines"]:
            if not line["spans"]:
                continue

            full_text = "".join(s["text"] for s in line["spans"]).strip()
            if not full_text:
                continue

            first_span = line["spans"][0]
            max_size = max(s["size"] for s in line["spans"])
            x0 = line["bbox"][0]
            y0 = line["bbox"][1]

            if is_footer(full_text, y0, page_h):
                continue

            if max_size >= 30 and y0 < 80 and not title_text:
                title_text = full_text
                continue

            if is_url_ref(full_text) and y0 > page_h - 50:
                continue

            indent = detect_indent_level(x0, max_size)

            spans_data = []
            for s in line["spans"]:
                text = s["text"]
                if not text:
                    continue
                spans_data.append({
                    "text": text,
                    "font": s["font"],
                    "size": s["size"],
                    "color": s["color"],
                    "flags": s.get("flags", 0),
                })

            if spans_data:
                body_lines.append((indent, spans_data, y0))

    return title_text, body_lines, image_blocks


def _classify_images(image_bboxes, page_w, page_h):
    """Classify images by position and size for layout decisions."""
    if not image_bboxes:
        return "none", []

    large_images = []
    for bbox in image_bboxes:
        w = bbox[2] - bbox[0]
        h = bbox[3] - bbox[1]
        if w < 60 or h < 40:
            continue
        cx = (bbox[0] + bbox[2]) / 2
        cy = (bbox[1] + bbox[3]) / 2
        area_ratio = (w * h) / (page_w * page_h)
        large_images.append({
            "bbox": bbox,
            "w": w, "h": h,
            "cx": cx, "cy": cy,
            "area": area_ratio,
            "right_side": cx > page_w * 0.55,
            "bottom_half": cy > page_h * 0.5,
        })

    if not large_images:
        return "none", []

    total_area = sum(im["area"] for im in large_images)

    # If images dominate the page (>45% area), render full page as image
    if total_area > 0.45:
        return "image_dominant", large_images

    right_images = [im for im in large_images if im["right_side"]]
    bottom_images = [im for im in large_images if im["bottom_half"] and not im["right_side"]]

    # Any significant image on the right side → right column layout
    if right_images and sum(im["area"] for im in right_images) > 0.04:
        return "right_column", large_images

    if bottom_images and sum(im["area"] for im in bottom_images) > 0.04:
        return "bottom_images", large_images

    # Any remaining images — use right column if any single image is significant
    if large_images and max(im["area"] for im in large_images) > 0.03:
        return "right_column", large_images

    return "scattered", large_images


def _add_text_content(tf, body_lines, font_size_map="normal"):
    """Add body text lines to a text frame with proper formatting."""
    BULLET_CHARS = {0: "●", 1: "▸", 2: "○", 3: "–", 4: "·", 5: "·"}

    # Font size mapping based on layout mode
    if font_size_map == "compact":
        SIZE_MAP = {28: 20, 24: 18, 20: 16, 16: 14, 12: 12}
    else:
        SIZE_MAP = {28: 24, 24: 22, 20: 20, 16: 16, 12: 14}

    INDENT_EMU = 350000

    prev_indent = -1
    for li, (indent, spans_data, y0) in enumerate(body_lines):
        p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()

        # Spacing: more space between top-level items, less for sub-items
        if indent <= 1:
            p.space_before = Pt(8)
        else:
            p.space_before = Pt(3)
        p.space_after = Pt(2)

        # Set indentation
        pPr = p._p.get_or_add_pPr()
        indent_emu = indent * INDENT_EMU
        pPr.set("marL", str(indent_emu))

        # Check for existing bullet in text
        first_text = spans_data[0]["text"]
        has_bullet = bool(BULLET_RE.match(first_text))

        # Determine dominant font size in this line
        max_size = max(sd["size"] for sd in spans_data)

        for si, sd in enumerate(spans_data):
            text = sd["text"]
            run = p.add_run()
            run.text = text

            f = run.font
            f.name = map_font(sd["font"])

            orig_size = sd["size"]
            mapped = SIZE_MAP.get(28, 24)
            for threshold in sorted(SIZE_MAP.keys(), reverse=True):
                if orig_size >= threshold:
                    mapped = SIZE_MAP[threshold]
                    break
            else:
                mapped = SIZE_MAP.get(12, 14)
            f.size = Pt(mapped)

            f.color.rgb = color_int_to_rgb(sd["color"])

            flags = sd["flags"]
            font_name = sd["font"]
            if flags & 16 or "Bold" in font_name:
                f.bold = True
            if flags & 2 or "Italic" in font_name:
                f.italic = True


def build_content_slide(prs, page, doc, chapter_label, section_name):
    """Build a formatted slide from a PDF page with professional layout."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_text, body_lines, image_bboxes = parse_pdf_page(page)
    page_w = page.rect.width
    page_h = page.rect.height

    add_header_bar(slide, chapter_label)

    display_title = title_text if title_text else section_name
    add_title_bar(slide, display_title)

    # Content area boundaries
    CONTENT_TOP = 1500000
    CONTENT_LEFT = 300000
    CONTENT_RIGHT_MARGIN = 300000
    CONTENT_BOTTOM = SLIDE_H - 200000
    FULL_CONTENT_W = SLIDE_W - CONTENT_LEFT - CONTENT_RIGHT_MARGIN

    layout_type, classified_images = _classify_images(image_bboxes, page_w, page_h)

    if layout_type == "image_dominant":
        # Page is mostly images (diagrams, charts) — render as full-page image
        _render_page_as_image(page, slide, CONTENT_TOP, CONTENT_LEFT, FULL_CONTENT_W, CONTENT_BOTTOM)
        return

    if layout_type == "right_column":
        # Text on left, images on right
        img_col_w = int(FULL_CONTENT_W * 0.42)
        text_col_w = FULL_CONTENT_W - img_col_w - 200000  # gap
        img_col_left = CONTENT_LEFT + text_col_w + 200000

        # Add text on left
        if body_lines:
            text_h = CONTENT_BOTTOM - CONTENT_TOP
            txbox = slide.shapes.add_textbox(
                Emu(CONTENT_LEFT), Emu(CONTENT_TOP),
                Emu(text_col_w), Emu(text_h),
            )
            tf = txbox.text_frame
            tf.word_wrap = True
            tf.margin_left = Emu(80000)
            tf.margin_right = Emu(50000)
            tf.margin_top = Emu(30000)
            tf.margin_bottom = Emu(30000)
            _add_text_content(tf, body_lines, "compact")

        # Stack images on right column
        _place_images_in_column(
            page, doc, slide, classified_images,
            img_col_left, CONTENT_TOP, img_col_w, CONTENT_BOTTOM,
        )
        return

    if layout_type == "bottom_images":
        # Text on top, images below
        bottom_imgs = [im for im in classified_images if im["bottom_half"]]
        top_imgs = [im for im in classified_images if not im["bottom_half"]]

        # Calculate split point
        img_zone_h = int((CONTENT_BOTTOM - CONTENT_TOP) * 0.40)
        text_zone_h = CONTENT_BOTTOM - CONTENT_TOP - img_zone_h - 100000
        img_zone_top = CONTENT_TOP + text_zone_h + 100000

        if body_lines:
            txbox = slide.shapes.add_textbox(
                Emu(CONTENT_LEFT), Emu(CONTENT_TOP),
                Emu(FULL_CONTENT_W), Emu(text_zone_h),
            )
            tf = txbox.text_frame
            tf.word_wrap = True
            tf.margin_left = Emu(80000)
            tf.margin_right = Emu(50000)
            tf.margin_top = Emu(30000)
            tf.margin_bottom = Emu(30000)
            _add_text_content(tf, body_lines, "compact")

        # Place images in bottom row
        all_imgs = bottom_imgs if bottom_imgs else classified_images
        _place_images_in_row(
            page, doc, slide, all_imgs,
            CONTENT_LEFT, img_zone_top, FULL_CONTENT_W, CONTENT_BOTTOM,
        )

        # Also place any top images in text zone if they exist
        if top_imgs:
            for im in top_imgs:
                _try_add_image_at(page, doc, slide, im["bbox"],
                                  CONTENT_LEFT + int(FULL_CONTENT_W * 0.55),
                                  CONTENT_TOP,
                                  int(FULL_CONTENT_W * 0.40),
                                  text_zone_h)
        return

    # Default: text-only or scattered images
    if body_lines:
        text_h = CONTENT_BOTTOM - CONTENT_TOP
        txbox = slide.shapes.add_textbox(
            Emu(CONTENT_LEFT), Emu(CONTENT_TOP),
            Emu(FULL_CONTENT_W), Emu(text_h),
        )
        tf = txbox.text_frame
        tf.word_wrap = True
        tf.margin_left = Emu(80000)
        tf.margin_right = Emu(50000)
        tf.margin_top = Emu(30000)
        tf.margin_bottom = Emu(30000)
        _add_text_content(tf, body_lines, "normal")

    # Place scattered images below text or centered
    if classified_images:
        _place_images_scattered(page, doc, slide, classified_images,
                                CONTENT_LEFT, CONTENT_TOP, FULL_CONTENT_W, CONTENT_BOTTOM,
                                page_w, page_h)


def _render_page_as_image(page, slide, top, left, width, bottom):
    """Render the entire PDF page as an image for diagram-heavy pages."""
    available_h = bottom - top
    mat = pymupdf.Matrix(2.0, 2.0)
    pix = page.get_pixmap(matrix=mat, alpha=False)
    img = Image.frombytes("RGB", (pix.width, pix.height), pix.samples)

    # Crop off header area (top ~15%) and footer (~5%)
    crop_top = int(pix.height * 0.13)
    crop_bottom = int(pix.height * 0.95)
    img = img.crop((0, crop_top, pix.width, crop_bottom))

    buf = BytesIO()
    img.save(buf, format="JPEG", quality=70, optimize=True)
    buf.seek(0)

    img_aspect = img.width / img.height
    avail_aspect = width / available_h

    if img_aspect > avail_aspect:
        img_w = width
        img_h = int(width / img_aspect)
    else:
        img_h = available_h
        img_w = int(available_h * img_aspect)

    img_left = left + (width - img_w) // 2
    img_top = top + (available_h - img_h) // 2

    slide.shapes.add_picture(buf, Emu(img_left), Emu(img_top), Emu(img_w), Emu(img_h))


def _place_images_in_column(page, doc, slide, images, col_left, col_top, col_w, col_bottom):
    """Place images stacked vertically in a column."""
    available_h = col_bottom - col_top
    n = len(images)
    if n == 0:
        return

    gap = 100000
    per_img_h = (available_h - gap * (n - 1)) // n
    per_img_h = min(per_img_h, available_h // 2)

    y = col_top
    for im in images:
        if y + 200000 > col_bottom:
            break
        remaining = col_bottom - y
        h = min(per_img_h, remaining)
        _try_add_image_at(page, doc, slide, im["bbox"], col_left, y, col_w, h)
        y += h + gap


def _place_images_in_row(page, doc, slide, images, row_left, row_top, row_w, row_bottom):
    """Place images side by side in a horizontal row."""
    available_h = row_bottom - row_top
    n = len(images)
    if n == 0:
        return

    gap = 150000
    per_img_w = (row_w - gap * (n - 1)) // n

    x = row_left
    for im in images:
        if x + 200000 > row_left + row_w:
            break
        remaining = row_left + row_w - x
        w = min(per_img_w, remaining)
        _try_add_image_at(page, doc, slide, im["bbox"], x, row_top, w, available_h)
        x += w + gap


def _place_images_scattered(page, doc, slide, images, left, top, width, bottom, page_w, page_h):
    """Place scattered images centered below text, never overlapping."""
    n = len(images)
    if n == 0:
        return

    # Place all images in a row at the bottom portion of the content area
    img_zone_top = top + int((bottom - top) * 0.55)
    img_zone_h = bottom - img_zone_top
    gap = 150000
    per_img_w = (width - gap * max(n - 1, 0)) // max(n, 1)
    per_img_w = min(per_img_w, int(width * 0.6))

    total_row_w = per_img_w * n + gap * max(n - 1, 0)
    start_x = left + (width - total_row_w) // 2

    x = start_x
    for im in images:
        if x + 200000 > left + width:
            break
        _try_add_image_at(page, doc, slide, im["bbox"], x, img_zone_top, per_img_w, img_zone_h)
        x += per_img_w + gap


def _extract_and_fix_image(doc, img_info):
    """Extract image from PDF, handling SMask compositing and filtering bad images."""
    xref = img_info[0]
    smask = img_info[1]
    img_w = img_info[2]
    img_h = img_info[3]

    # Skip the recurring header logo (144x154 on every page)
    if img_w <= 200 and img_h <= 200:
        return None

    extracted = doc.extract_image(xref)
    if not extracted or extracted["ext"] not in ("png", "jpeg", "jpg", "bmp", "gif", "tiff"):
        return None

    img = Image.open(BytesIO(extracted["image"]))

    # Handle SMask (soft mask) — composite onto white background
    if smask > 0:
        try:
            mask_data = doc.extract_image(smask)
            if mask_data:
                mask_img = Image.open(BytesIO(mask_data["image"])).convert("L")
                if mask_img.size != img.size:
                    mask_img = mask_img.resize(img.size, Image.LANCZOS)
                # Composite: place image onto white background using mask
                bg = Image.new("RGB", img.size, (255, 255, 255))
                img_rgb = img.convert("RGB")
                bg.paste(img_rgb, mask=mask_img)
                img = bg
        except Exception:
            pass

    # For RGBA images, composite onto white
    if img.mode == "RGBA":
        bg = Image.new("RGB", img.size, (255, 255, 255))
        bg.paste(img, mask=img.split()[3])
        img = bg

    img = img.convert("RGB")

    # Check if image is mostly black (broken extraction)
    sample = img.resize((20, 20), Image.LANCZOS)
    raw = sample.tobytes()
    avg_brightness = sum(raw) / len(raw)
    if avg_brightness < 30:
        return None

    return img


def _try_add_image_at(page, doc, slide, target_bbox, left, top, max_w, max_h):
    """Try to find and add the matching image from the PDF, fitting into the given area."""
    target_rect = pymupdf.Rect(target_bbox)

    try:
        images = page.get_images(full=True)
        for img_info in images:
            xref = img_info[0]
            try:
                img_rects = page.get_image_rects(xref)
                for img_rect in img_rects:
                    if img_rect.intersects(target_rect):
                        overlap = img_rect & target_rect
                        if overlap.width > target_rect.width * 0.5:
                            img = _extract_and_fix_image(doc, img_info)
                            if img is None:
                                continue

                            img_stream = compress_image(_img_to_bytes(img))
                            img_aspect = img.width / img.height

                            avail_aspect = max_w / max_h if max_h > 0 else 1
                            if img_aspect > avail_aspect:
                                w = max_w
                                h = int(max_w / img_aspect)
                            else:
                                h = max_h
                                w = int(max_h * img_aspect)

                            actual_left = left + (max_w - w) // 2
                            actual_top = top + (max_h - h) // 2

                            slide.shapes.add_picture(
                                img_stream,
                                Emu(actual_left), Emu(actual_top),
                                Emu(w), Emu(h),
                            )
                            return True
            except Exception:
                continue
    except Exception:
        pass
    return False


def _img_to_bytes(img):
    """Convert PIL Image to bytes."""
    buf = BytesIO()
    img.save(buf, format="PNG")
    return buf.getvalue()


# ── Section title page ──

def make_section_intro_slide(prs, chapter_label, section_name):
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header_bar(slide, chapter_label)

    txbox = slide.shapes.add_textbox(
        Emu(1000000), Emu(2200000), Emu(SLIDE_W - 2000000), Emu(2000000),
    )
    tf = txbox.text_frame
    tf.word_wrap = True

    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = section_name
    run.font.size = Pt(40)
    run.font.bold = True
    run.font.name = "黑体"
    run.font.color.rgb = DARK_BLUE

    line = slide.shapes.add_connector(
        1, Emu(3000000), Emu(4400000), Emu(SLIDE_W - 3000000), Emu(4400000),
    )
    line.line.color.rgb = BLUE_ACCENT
    line.line.width = Pt(2)


# ── Main ──

def main():
    print("Creating presentation...")
    prs = Presentation()
    prs.slide_width = Emu(SLIDE_W)
    prs.slide_height = Emu(SLIDE_H)

    print("Creating cover slide...")
    make_cover_slide(prs)

    print("Creating TOC slide...")
    make_toc_slide(prs)

    total_pages = 0

    for chap_idx, (num, title, pdfs) in enumerate(CHAPTERS):
        chap_dir = f"{num} {title}" if num != "附录" else "评测与资源"
        chapter_label = f"{num} {title}" if num != "附录" else f"附录：{title}"
        print(f"\n--- {chapter_label} ---")

        make_chapter_nav_slide(prs, chap_idx)

        for pdf_file in pdfs:
            pdf_path = os.path.join(SLIDES_DIR, chap_dir, pdf_file)
            section_name = os.path.splitext(pdf_file)[0]
            print(f"  {pdf_file}...", end="", flush=True)

            make_section_intro_slide(prs, chapter_label, section_name)

            doc = pymupdf.open(pdf_path)
            n = len(doc)

            for page_num in range(n):
                page = doc[page_num]
                if page_num == 0:
                    td = page.get_text("dict")
                    text_blocks = [b for b in td["blocks"] if b["type"] == 0]
                    total_text = sum(
                        len("".join(s["text"] for s in l["spans"]))
                        for b in text_blocks for l in b["lines"]
                    )
                    if total_text < 50:
                        continue

                build_content_slide(prs, page, doc, chapter_label, section_name)
                total_pages += 1

            doc.close()
            print(f" {n} pages")

    print(f"\nTotal content slides: {total_pages}")
    print(f"Total slides: {len(prs.slides)}")
    print(f"Saving to {OUTPUT_PATH}...")
    prs.save(OUTPUT_PATH)
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"Done! File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
