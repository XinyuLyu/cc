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
    """Add a colored title bar below the header."""
    # Title background bar
    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(0), Emu(836295), Emu(SLIDE_W), Emu(560000),
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = LIGHT_BLUE_BG
    rect.line.fill.background()

    # Title text
    txbox = slide.shapes.add_textbox(
        Emu(200000), Emu(856295), Emu(SLIDE_W - 400000), Emu(520000),
    )
    tf = txbox.text_frame
    tf.word_wrap = True
    tf.margin_left = Emu(100000)
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

# Bullet markers to strip
BULLET_RE = re.compile(r"^[➢▶●○■□◆◇•▪▸▹►▻→←↑↓⇒⇐⇑⇓✓✗✘✔✕☐☑☒★☆♦♠♣♥]\s*")

# X-position thresholds for indent level detection (in PDF points)
INDENT_THRESHOLDS = [70, 110, 140, 170, 200]


def detect_indent_level(x0, font_size):
    """Determine indent level from x-position."""
    for i, thresh in enumerate(INDENT_THRESHOLDS):
        if x0 < thresh:
            return i
    return len(INDENT_THRESHOLDS)


def is_footer(text, y0, page_h):
    """Detect footer/reference text to skip."""
    if "教材课件" in text:
        return True
    if y0 > page_h - 30 and len(text) < 40:
        return True
    return False


def is_url_ref(text):
    """Detect URL reference lines."""
    return text.strip().startswith("http://") or text.strip().startswith("https://")


def parse_pdf_page(page):
    """Parse a PDF page into structured content: title, body lines, images."""
    td = page.get_text("dict")
    page_h = page.rect.height

    title_text = ""
    body_lines = []    # list of (indent_level, spans_data)
    image_blocks = []  # list of (bbox, xref_match_info)

    all_blocks = sorted(td["blocks"], key=lambda b: (b["bbox"][1], b["bbox"][0]))

    for block in all_blocks:
        if block["type"] == 1:
            bbox = block["bbox"]
            w = bbox[2] - bbox[0]
            h = bbox[3] - bbox[1]
            if w > 60 and h > 40:
                image_blocks.append(bbox)
            continue

        if block["type"] != 0:
            continue

        for line in block["lines"]:
            if not line["spans"]:
                continue

            # Build full line text from all spans
            full_text = "".join(s["text"] for s in line["spans"]).strip()
            if not full_text:
                continue

            first_span = line["spans"][0]
            max_size = max(s["size"] for s in line["spans"])
            x0 = line["bbox"][0]
            y0 = line["bbox"][1]

            # Skip footer/references
            if is_footer(full_text, y0, page_h):
                continue

            # Detect title (large font at top of page)
            if max_size >= 30 and y0 < 80 and not title_text:
                title_text = full_text
                continue

            # Skip URL references at bottom
            if is_url_ref(full_text) and y0 > page_h - 50:
                continue

            # Body content - determine indent and collect span data
            indent = detect_indent_level(x0, max_size)

            # Collect rich span data for this line
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


def build_content_slide(prs, page, doc, chapter_label, section_name):
    """Build a formatted slide from a PDF page."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])

    title_text, body_lines, image_bboxes = parse_pdf_page(page)

    # Add template header
    add_header_bar(slide, chapter_label)

    # Add title bar
    if title_text:
        # Check if title differs from section name (indicating a sub-topic)
        if title_text != section_name:
            add_title_bar(slide, title_text)
        else:
            add_title_bar(slide, section_name)
    else:
        add_title_bar(slide, section_name)

    # Content area starts below title bar
    content_top = 1430000
    content_left = 200000
    content_w = SLIDE_W - 400000

    # Determine layout based on images
    has_large_right_image = False
    large_image_bbox = None

    # Check for large images and their position
    for bbox in image_bboxes:
        img_w = bbox[2] - bbox[0]
        img_h = bbox[3] - bbox[1]
        if img_w > 200 and img_h > 100:
            # If image is on the right side and takes significant space
            if bbox[0] > 400 and img_w > 300:
                has_large_right_image = True
                large_image_bbox = bbox
            elif img_w > 500:
                # Full-width image
                large_image_bbox = bbox

    # Text content width - narrower if there's a right-side image
    text_w = content_w
    if has_large_right_image and large_image_bbox:
        text_w = int(large_image_bbox[0] * SCALE) - content_left - 100000
        if text_w < 4000000:
            text_w = content_w
            has_large_right_image = False

    # Add body text
    if body_lines:
        # Calculate text box height
        text_h = SLIDE_H - content_top - 200000

        txbox = slide.shapes.add_textbox(
            Emu(content_left), Emu(content_top),
            Emu(text_w), Emu(text_h),
        )
        tf = txbox.text_frame
        tf.word_wrap = True
        tf.margin_left = Emu(50000)
        tf.margin_right = Emu(50000)
        tf.margin_top = Emu(50000)
        tf.margin_bottom = Emu(50000)

        INDENT_EMU = 380000  # per level

        for li, (indent, spans_data, y0) in enumerate(body_lines):
            p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
            p.space_before = Pt(3)
            p.space_after = Pt(1)

            # Set indentation
            pPr = p._p.get_or_add_pPr()
            pPr.set("marL", str(indent * INDENT_EMU))

            # Determine if first span starts with bullet marker
            first_text = spans_data[0]["text"]
            bullet_match = BULLET_RE.match(first_text)

            for si, sd in enumerate(spans_data):
                text = sd["text"]

                # Strip bullet marker from first span and we'll set bullet formatting
                if si == 0 and bullet_match:
                    # Keep the bullet character, it's part of the design
                    pass

                run = p.add_run()
                run.text = text

                f = run.font
                f.name = map_font(sd["font"])
                # Scale font sizes slightly for the content area
                orig_size = sd["size"]
                if orig_size >= 28:
                    f.size = Pt(22)
                elif orig_size >= 24:
                    f.size = Pt(18)
                elif orig_size >= 20:
                    f.size = Pt(16)
                elif orig_size >= 16:
                    f.size = Pt(14)
                else:
                    f.size = Pt(12)

                f.color.rgb = color_int_to_rgb(sd["color"])

                flags = sd["flags"]
                font_name = sd["font"]
                if flags & 16 or "Bold" in font_name:
                    f.bold = True
                if flags & 2 or "Italic" in font_name:
                    f.italic = True

    # Add images
    for bbox in image_bboxes:
        img_w_pdf = bbox[2] - bbox[0]
        img_h_pdf = bbox[3] - bbox[1]

        if img_w_pdf < 60 or img_h_pdf < 40:
            continue

        # Map image position to PPTX coordinates
        # Y: map from PDF page to content area below title bar
        pdf_content_start = 80.0
        pdf_content_end = page.rect.height - 20.0
        pdf_range = pdf_content_end - pdf_content_start

        pptx_content_start = content_top
        pptx_content_end = SLIDE_H - 100000
        pptx_range = pptx_content_end - pptx_content_start

        # Map y position
        rel_y = (bbox[1] - pdf_content_start) / pdf_range
        img_top = int(pptx_content_start + rel_y * pptx_range)
        img_top = max(content_top, min(img_top, SLIDE_H - 500000))

        # Map x position
        img_left = int(bbox[0] * SCALE)

        # Scale image size to fit slide
        max_img_w = SLIDE_W - img_left - 100000
        max_img_h = SLIDE_H - img_top - 100000

        img_w = int(img_w_pdf * SCALE)
        img_h = int(img_h_pdf * SCALE)

        # Scale down if needed
        if img_w > max_img_w:
            ratio = max_img_w / img_w
            img_w = max_img_w
            img_h = int(img_h * ratio)
        if img_h > max_img_h:
            ratio = max_img_h / img_h
            img_h = max_img_h
            img_w = int(img_w * ratio)

        # Find and extract actual image data
        _try_add_image(page, doc, slide, bbox, img_left, img_top, img_w, img_h)


def _try_add_image(page, doc, slide, target_bbox, left, top, width, height):
    """Try to find and add the matching image from the PDF."""
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
                            extracted = doc.extract_image(xref)
                            if extracted and extracted["ext"] in ("png", "jpeg", "jpg", "bmp", "gif", "tiff"):
                                img_stream = compress_image(extracted["image"])
                                slide.shapes.add_picture(
                                    img_stream, Emu(left), Emu(top), Emu(width), Emu(height),
                                )
                                return True
            except Exception:
                continue
    except Exception:
        pass
    return False


# ── Section title page (sub-section intro within a chapter) ──

def make_section_intro_slide(prs, chapter_label, section_name):
    """Create a section title slide for each PDF within a chapter."""
    slide = prs.slides.add_slide(prs.slide_layouts[6])
    add_header_bar(slide, chapter_label)

    # Centered section name
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

    # Decorative line
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

        # Chapter navigation slide
        make_chapter_nav_slide(prs, chap_idx)

        for pdf_file in pdfs:
            pdf_path = os.path.join(SLIDES_DIR, chap_dir, pdf_file)
            section_name = os.path.splitext(pdf_file)[0]
            print(f"  {pdf_file}...", end="", flush=True)

            # Section intro slide
            make_section_intro_slide(prs, chapter_label, section_name)

            doc = pymupdf.open(pdf_path)
            n = len(doc)

            for page_num in range(n):
                page = doc[page_num]
                # Skip the PDF's own title page (page 0 usually)
                # Page 0 is typically a cover with just title + author
                if page_num == 0:
                    # Check if it's a real title page (very few text blocks, large title)
                    td = page.get_text("dict")
                    text_blocks = [b for b in td["blocks"] if b["type"] == 0]
                    total_text = sum(
                        len("".join(s["text"] for s in l["spans"]))
                        for b in text_blocks for l in b["lines"]
                    )
                    # If very little text, skip (it's just a decorative title page)
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
