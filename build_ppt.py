#!/usr/bin/env python3
"""
Convert LLMBook PDF slides into a single PPTX presentation.
Extracts text and images as native PPTX elements (no screenshots).
"""

import os
import re
from io import BytesIO
import pymupdf
from PIL import Image
from pptx import Presentation
from pptx.util import Emu, Pt
from pptx.dml.color import RGBColor
from pptx.enum.text import PP_ALIGN
from pptx.enum.shapes import MSO_SHAPE

# ── Paths ──
SLIDES_DIR = "/home/user/llmbook-zh/llmbook-zh.github.io/slides"
OUTPUT_PATH = "/home/user/cc/大语言模型课件.pptx"
ASSET_DIR = "/tmp/claude-0/template_assets"

SLIDE_W = 12192000
SLIDE_H = 6858000
SCALE = 12700  # EMU per PDF point (914400 / 72)

# Template colors
BLUE_ACCENT = RGBColor(0x33, 0x33, 0xFF)
DARK_BLUE = RGBColor(0x01, 0x52, 0x8A)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
GRAY_TEXT = RGBColor(0x99, 0x99, 0x99)

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
        "7.3 思维链提示.pdf",
        "7.4 检索增强生成.pdf",
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

# ── Font mapping: PDF font names -> Office font names ──
FONT_MAP = {
    "SimHei": "黑体",
    "KaiTi": "楷体",
    "FangSong": "仿宋",
    "SimSun": "宋体",
    "NSimSun": "新宋体",
    "MicrosoftYaHei": "微软雅黑",
    "TimesNewRomanPSMT": "Times New Roman",
    "TimesNewRomanPS-BoldMT": "Times New Roman",
    "TimesNewRomanPS-ItalicMT": "Times New Roman",
    "TimesNewRomanPS-BoldItalicMT": "Times New Roman",
    "ArialMT": "Arial",
    "Arial-BoldMT": "Arial",
    "Arial-ItalicMT": "Arial",
    "Arial-BoldItalicMT": "Arial",
    "CambriaMath": "Cambria Math",
    "Wingdings-Regular": "Wingdings",
    "SymbolMT": "Symbol",
}


def map_font(pdf_font):
    if pdf_font in FONT_MAP:
        return FONT_MAP[pdf_font]
    base = re.sub(r"[-,](Bold|Italic|Regular|Medium|Light|Thin|Book).*$", "", pdf_font)
    if base in FONT_MAP:
        return FONT_MAP[base]
    for key, val in FONT_MAP.items():
        if key.lower() in pdf_font.lower():
            return val
    return pdf_font


def is_bold(font_name, flags):
    return bool(flags & 16) or "Bold" in font_name


def is_italic(font_name, flags):
    return bool(flags & 2) or "Italic" in font_name


def color_int_to_rgb(c):
    return RGBColor((c >> 16) & 0xFF, (c >> 8) & 0xFF, c & 0xFF)


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
        rect.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xF7)
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
        rect.fill.fore_color.rgb = BLUE_ACCENT if cur else RGBColor(0xE8, 0xEE, 0xF7)
        rect.line.fill.background()
        if rect.has_text_frame:
            rect.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            r = rect.text_frame.paragraphs[0].add_run()
            r.text = f"{num} {title}"
            r.font.size = Pt(18)
            r.font.bold = True
            r.font.name = "黑体"
            r.font.color.rgb = WHITE if cur else DARK_BLUE


# ── PDF content extraction ──

def extract_pdf_page_to_slide(page, slide, doc):
    """Extract text blocks and images from a PDF page into native PPTX elements."""
    td = page.get_text("dict")

    # Add images first (behind text)
    for block in td["blocks"]:
        if block["type"] == 1:
            _add_image_block_from_page(block, page, doc, slide)

    # Then add text on top
    for block in td["blocks"]:
        if block["type"] == 0:
            _add_text_block(block, slide)


def _add_text_block(block, slide):
    bbox = block["bbox"]
    left = int(bbox[0] * SCALE)
    top = int(bbox[1] * SCALE)
    width = int((bbox[2] - bbox[0]) * SCALE)
    height = int((bbox[3] - bbox[1]) * SCALE)

    if width < 1000 or height < 1000:
        return

    txbox = slide.shapes.add_textbox(Emu(left), Emu(top), Emu(width), Emu(height))
    tf = txbox.text_frame
    tf.word_wrap = False
    tf.margin_left = Emu(0)
    tf.margin_right = Emu(0)
    tf.margin_top = Emu(0)
    tf.margin_bottom = Emu(0)

    for li, line in enumerate(block["lines"]):
        p = tf.paragraphs[0] if li == 0 else tf.add_paragraph()
        p.space_before = Pt(0)
        p.space_after = Pt(0)

        # Compute line height for line spacing
        line_bbox = line["bbox"]
        line_h = line_bbox[3] - line_bbox[1]

        for span in line["spans"]:
            text = span["text"]
            if not text:
                continue

            run = p.add_run()
            run.text = text

            f = run.font
            f.size = Pt(span["size"])
            f.name = map_font(span["font"])
            f.color.rgb = color_int_to_rgb(span["color"])

            flags = span.get("flags", 0)
            font_name = span["font"]
            if is_bold(font_name, flags):
                f.bold = True
            if is_italic(font_name, flags):
                f.italic = True


def _compress_image(img_data, ext):
    """Compress image to JPEG to reduce file size."""
    MAX_W, MAX_H = 1280, 960
    try:
        img = Image.open(BytesIO(img_data))
        # Resize if too large
        if img.width > MAX_W or img.height > MAX_H:
            img.thumbnail((MAX_W, MAX_H), Image.LANCZOS)
        if img.mode in ("RGBA", "LA", "P"):
            bg = Image.new("RGB", img.size, (255, 255, 255))
            if img.mode == "P":
                img = img.convert("RGBA")
            bg.paste(img, mask=img.split()[-1] if img.mode == "RGBA" else None)
            img = bg
        else:
            img = img.convert("RGB")
        buf = BytesIO()
        img.save(buf, format="JPEG", quality=60, optimize=True)
        buf.seek(0)
        return buf
    except Exception:
        return BytesIO(img_data)


def _add_image_block_from_page(block, page, doc, slide):
    """Extract image using its xref from the document and add to slide."""
    bbox = block["bbox"]
    left = int(bbox[0] * SCALE)
    top = int(bbox[1] * SCALE)
    width = int((bbox[2] - bbox[0]) * SCALE)
    height = int((bbox[3] - bbox[1]) * SCALE)

    if width < 2000 or height < 2000:
        return

    # Get image xref from the block
    # In dict mode, image blocks have "image" as base64 but we need bytes
    # Use page.get_images() to find the matching image
    try:
        images = page.get_images(full=True)
        # Match by finding image whose rect overlaps the block bbox
        block_rect = pymupdf.Rect(bbox)

        for img_info in images:
            xref = img_info[0]
            try:
                img_rects = page.get_image_rects(xref)
                for img_rect in img_rects:
                    if img_rect.intersects(block_rect) and abs(img_rect.width - block_rect.width) < 5:
                        extracted = doc.extract_image(xref)
                        if extracted:
                            img_data = extracted["image"]
                            ext = extracted["ext"]
                            if ext in ("png", "jpeg", "jpg", "bmp", "gif", "tiff", "tif"):
                                img_stream = _compress_image(img_data, ext)
                                slide.shapes.add_picture(
                                    img_stream, Emu(left), Emu(top), Emu(width), Emu(height)
                                )
                                return
            except Exception:
                continue
    except Exception as e:
        pass


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
        print(f"\n--- Chapter {chap_idx+1}: {num} {title} ---")

        make_chapter_nav_slide(prs, chap_idx)

        for pdf_file in pdfs:
            pdf_path = os.path.join(SLIDES_DIR, chap_dir, pdf_file)
            print(f"  {pdf_file}...", end="", flush=True)

            doc = pymupdf.open(pdf_path)
            n = len(doc)

            for page_num in range(n):
                page = doc[page_num]
                blank = prs.slide_layouts[6]
                slide = prs.slides.add_slide(blank)
                extract_pdf_page_to_slide(page, slide, doc)
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
