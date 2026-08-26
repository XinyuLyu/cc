#!/usr/bin/env python3
"""
Convert LLMBook PDF slides into a single PPTX presentation
using the provided template style.
"""

import os
import io
import copy
import pymupdf
from pptx import Presentation
from pptx.util import Inches, Pt, Emu
from pptx.enum.text import PP_ALIGN
from pptx.dml.color import RGBColor
from pptx.enum.shapes import MSO_SHAPE
from lxml import etree

# ── Constants ──
TEMPLATE_PATH = "/home/user/cc/模板.pptx"
SLIDES_DIR = "/home/user/llmbook-zh/llmbook-zh.github.io/slides"
OUTPUT_PATH = "/home/user/cc/大语言模型课件.pptx"
IMG_DIR = "/tmp/claude-0/pdf_images"
ASSET_DIR = "/tmp/claude-0/template_assets"

SLIDE_W = 12192000  # EMU
SLIDE_H = 6858000

# Colors from template
BLUE_ACCENT = RGBColor(0x33, 0x33, 0xFF)
DARK_BLUE = RGBColor(0x01, 0x52, 0x8A)
ORANGE = RGBColor(0xEB, 0x64, 0x1B)
WHITE = RGBColor(0xFF, 0xFF, 0xFF)
LIGHT_GRAY = RGBColor(0xF0, 0xF0, 0xF0)
GRAY_TEXT = RGBColor(0x99, 0x99, 0x99)

# Chapter definitions in order
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

os.makedirs(IMG_DIR, exist_ok=True)


def add_header_bar(slide, prs_obj, chapter_label=""):
    """Add the template-style header bar to a slide."""
    # Blue/dark rectangle on the right side of header
    rect = slide.shapes.add_shape(
        MSO_SHAPE.RECTANGLE,
        Emu(3530600), Emu(6985),
        Emu(8661400), Emu(836295)
    )
    rect.fill.solid()
    rect.fill.fore_color.rgb = DARK_BLUE
    rect.line.fill.background()

    # Logo image on the left
    logo_path = os.path.join(ASSET_DIR, "图片 1.png")
    if os.path.exists(logo_path):
        slide.shapes.add_picture(
            logo_path,
            Emu(0), Emu(0),
            Emu(6342380), Emu(836295)
        )

    # Horizontal line under header
    line = slide.shapes.add_connector(
        1,  # straight connector
        Emu(0), Emu(836332),
        Emu(SLIDE_W), Emu(836332)
    )
    line.line.color.rgb = DARK_BLUE
    line.line.width = Pt(1)

    # Chapter label text on header
    if chapter_label:
        txbox = slide.shapes.add_textbox(
            Emu(0), Emu(0),
            Emu(SLIDE_W), Emu(770890)
        )
        tf = txbox.text_frame
        tf.word_wrap = True
        p = tf.paragraphs[0]
        run = p.add_run()
        run.text = f"       {chapter_label}"
        run.font.size = Pt(40)
        run.font.bold = True
        run.font.name = "楷体"
        run.font.color.rgb = WHITE


def add_bottom_decoration(slide):
    """Add the bottom decoration strip from template."""
    bottom_path = os.path.join(ASSET_DIR, "图片 5.png")
    if os.path.exists(bottom_path):
        slide.shapes.add_picture(
            bottom_path,
            Emu(0), Emu(5167054),
            Emu(SLIDE_W), Emu(1703387)
        )


def make_cover_slide(prs_obj):
    """Create the cover/title slide."""
    blank_layout = prs_obj.slide_layouts[6]  # blank layout
    slide = prs_obj.slides.add_slide(blank_layout)

    add_header_bar(slide, prs_obj, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")
    add_bottom_decoration(slide)

    # Main title text box
    txbox = slide.shapes.add_textbox(
        Emu(376238), Emu(1500000),
        Emu(11541125), Emu(3500000)
    )
    tf = txbox.text_frame
    tf.word_wrap = True

    # Title
    p = tf.paragraphs[0]
    p.alignment = PP_ALIGN.CENTER
    run = p.add_run()
    run.text = BOOK_TITLE
    run.font.size = Pt(54)
    run.font.bold = True
    run.font.name = "微软雅黑"
    run.font.color.rgb = DARK_BLUE

    # Subtitle
    p2 = tf.add_paragraph()
    p2.alignment = PP_ALIGN.CENTER
    p2.space_before = Pt(8)
    run2 = p2.add_run()
    run2.text = BOOK_SUBTITLE
    run2.font.size = Pt(36)
    run2.font.bold = False
    run2.font.name = "微软雅黑"
    run2.font.color.rgb = BLUE_ACCENT

    # Source info
    p3 = tf.add_paragraph()
    p3.alignment = PP_ALIGN.CENTER
    p3.space_before = Pt(30)
    run3 = p3.add_run()
    run3.text = "基于《大语言模型：从理论到实践》课件整理"
    run3.font.size = Pt(20)
    run3.font.name = "黑体"
    run3.font.color.rgb = RGBColor(0x66, 0x66, 0x66)

    # URL
    p4 = tf.add_paragraph()
    p4.alignment = PP_ALIGN.CENTER
    p4.space_before = Pt(8)
    run4 = p4.add_run()
    run4.text = "LLMBook-zh.github.io"
    run4.font.size = Pt(18)
    run4.font.name = "Times New Roman"
    run4.font.color.rgb = BLUE_ACCENT


def make_toc_slide(prs_obj):
    """Create the table of contents slide."""
    blank_layout = prs_obj.slide_layouts[6]
    slide = prs_obj.slides.add_slide(blank_layout)

    add_header_bar(slide, prs_obj, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")

    # Title "目录"
    txbox = slide.shapes.add_textbox(
        Emu(500000), Emu(950000),
        Emu(3000000), Emu(600000)
    )
    tf = txbox.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = "目  录"
    run.font.size = Pt(36)
    run.font.bold = True
    run.font.name = "黑体"
    run.font.color.rgb = DARK_BLUE

    # Chapter list - two columns for 9 items
    start_y = 1700000
    col1_x = 800000
    col2_x = 6400000
    item_h = 520000
    gap = 80000

    for idx, (num, title, _) in enumerate(CHAPTERS):
        if idx < 5:
            x = col1_x
            y = start_y + idx * (item_h + gap)
        else:
            x = col2_x
            y = start_y + (idx - 5) * (item_h + gap)

        # Diamond shape
        diamond = slide.shapes.add_shape(
            MSO_SHAPE.DIAMOND,
            Emu(x), Emu(y),
            Emu(500000), Emu(440000)
        )
        diamond.fill.solid()
        diamond.fill.fore_color.rgb = BLUE_ACCENT
        diamond.line.fill.background()

        # Number on diamond
        if diamond.has_text_frame:
            diamond.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = diamond.text_frame.paragraphs[0].add_run()
            run.text = f"{idx + 1:02d}" if idx < 8 else "A"
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.name = "Times New Roman"
            run.font.color.rgb = WHITE

        # Chapter title rectangle
        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Emu(x + 580000), Emu(y + 20000),
            Emu(4600000), Emu(400000)
        )
        rect.fill.solid()
        rect.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xF7)
        rect.line.fill.background()

        if rect.has_text_frame:
            rect.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = rect.text_frame.paragraphs[0].add_run()
            run.text = f"{num} {title}"
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.name = "黑体"
            run.font.color.rgb = DARK_BLUE


def make_chapter_nav_slide(prs_obj, current_idx):
    """Create a chapter navigation slide highlighting current chapter."""
    blank_layout = prs_obj.slide_layouts[6]
    slide = prs_obj.slides.add_slide(blank_layout)

    cur_num, cur_title, _ = CHAPTERS[current_idx]
    full_label = f"{cur_num} {cur_title}" if cur_num != "附录" else cur_title

    add_header_bar(slide, prs_obj, f"{BOOK_TITLE}：{BOOK_SUBTITLE}")

    # Section indicator
    txbox = slide.shapes.add_textbox(
        Emu(500000), Emu(950000),
        Emu(11000000), Emu(600000)
    )
    tf = txbox.text_frame
    p = tf.paragraphs[0]
    run = p.add_run()
    run.text = f"当前章节"
    run.font.size = Pt(20)
    run.font.name = "黑体"
    run.font.color.rgb = GRAY_TEXT

    # Chapter list - two columns
    start_y = 1700000
    col1_x = 800000
    col2_x = 6400000
    item_h = 520000
    gap = 80000

    for idx, (num, title, _) in enumerate(CHAPTERS):
        is_current = (idx == current_idx)

        if idx < 5:
            x = col1_x
            y = start_y + idx * (item_h + gap)
        else:
            x = col2_x
            y = start_y + (idx - 5) * (item_h + gap)

        # Diamond
        diamond = slide.shapes.add_shape(
            MSO_SHAPE.DIAMOND,
            Emu(x), Emu(y),
            Emu(500000), Emu(440000)
        )
        if is_current:
            diamond.fill.solid()
            diamond.fill.fore_color.rgb = BLUE_ACCENT
        else:
            diamond.fill.solid()
            diamond.fill.fore_color.rgb = RGBColor(0xCC, 0xCC, 0xCC)
        diamond.line.fill.background()

        if diamond.has_text_frame:
            diamond.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = diamond.text_frame.paragraphs[0].add_run()
            run.text = f"{idx + 1:02d}" if idx < 8 else "A"
            run.font.size = Pt(16)
            run.font.bold = True
            run.font.name = "Times New Roman"
            run.font.color.rgb = WHITE

        # Chapter rect
        rect = slide.shapes.add_shape(
            MSO_SHAPE.ROUNDED_RECTANGLE,
            Emu(x + 580000), Emu(y + 20000),
            Emu(4600000), Emu(400000)
        )
        if is_current:
            rect.fill.solid()
            rect.fill.fore_color.rgb = BLUE_ACCENT
        else:
            rect.fill.solid()
            rect.fill.fore_color.rgb = RGBColor(0xE8, 0xEE, 0xF7)
        rect.line.fill.background()

        if rect.has_text_frame:
            rect.text_frame.paragraphs[0].alignment = PP_ALIGN.CENTER
            run = rect.text_frame.paragraphs[0].add_run()
            run.text = f"{num} {title}"
            run.font.size = Pt(18)
            run.font.bold = True
            run.font.name = "黑体"
            run.font.color.rgb = WHITE if is_current else DARK_BLUE


def render_pdf_pages(pdf_path, dpi=72):
    """Render all pages of a PDF to JPEG images. Returns list of image paths."""
    doc = pymupdf.open(pdf_path)
    paths = []
    base = os.path.splitext(os.path.basename(pdf_path))[0]
    mat = pymupdf.Matrix(dpi / 72, dpi / 72)

    for page_num in range(len(doc)):
        page = doc[page_num]
        pix = page.get_pixmap(matrix=mat)
        img_path = os.path.join(IMG_DIR, f"{base}_p{page_num:03d}.jpg")
        pix.save(img_path, jpg_quality=65)
        paths.append(img_path)

    doc.close()
    return paths


def add_pdf_page_slide(prs_obj, img_path):
    """Add a slide with a PDF page image filling the entire slide."""
    blank_layout = prs_obj.slide_layouts[6]
    slide = prs_obj.slides.add_slide(blank_layout)

    slide.shapes.add_picture(
        img_path,
        Emu(0), Emu(0),
        Emu(SLIDE_W), Emu(SLIDE_H)
    )


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
        print(f"\n--- Chapter {chap_idx + 1}: {num} {title} ---")

        # Chapter navigation slide
        make_chapter_nav_slide(prs, chap_idx)

        # Process each PDF
        for pdf_file in pdfs:
            pdf_path = os.path.join(SLIDES_DIR, chap_dir, pdf_file)
            print(f"  Processing: {pdf_file}...", end="", flush=True)

            img_paths = render_pdf_pages(pdf_path)
            print(f" {len(img_paths)} pages", flush=True)

            for img_path in img_paths:
                add_pdf_page_slide(prs, img_path)
                total_pages += 1

            # Clean up images after adding to free disk
            for img_path in img_paths:
                os.remove(img_path)

    print(f"\nTotal content slides: {total_pages}")
    print(f"Total slides (with nav): {len(prs.slides)}")
    print(f"Saving to {OUTPUT_PATH}...")
    prs.save(OUTPUT_PATH)
    size_mb = os.path.getsize(OUTPUT_PATH) / (1024 * 1024)
    print(f"Done! File size: {size_mb:.1f} MB")


if __name__ == "__main__":
    main()
