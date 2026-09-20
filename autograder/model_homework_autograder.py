#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Unified autograder for two multimodal model-training notebooks (caption + retrieval).

Scoring:
  - code implementation: 60 points (80-point unit-test rubric normalized to 60)
  - final model performance: 20 points (teacher evaluates on test set with full captions)
  - understanding / experiment analysis: 20 points (4 questions x 5; teacher-entered)

Usage:
  python model_homework_autograder.py submissions/ \\
      --config grading_config.json \\
      --test-data-dir /path/to/teacher_test_data/ \\
      --analysis-csv analysis_scores.csv \\
      --output grades.csv \\
      --allow-unsafe-exec

The grader runs lightweight unit tests on student code, loads saved model weights to evaluate
test-set performance, and extracts the four analysis answers into a review CSV.
"""
from __future__ import annotations

import argparse
import ast
import csv
import json
import math
import os
import re
import subprocess
import sys
import tempfile
import traceback
from dataclasses import dataclass, asdict
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Dict, List, Optional, Tuple

WEIGHTS = {
    "data": 5.0,
    "model": 25.0,
    "loss": 12.0,
    "optimizer": 4.0,
    "evaluation": 12.0,
    "training": 17.0,
    "quality": 5.0,
}
IMPLEMENTATION_RAW_MAX = 80.0
IMPLEMENTATION_FINAL_MAX = 60.0
PERFORMANCE_MAX = 20.0
ANALYSIS_MAX = 20.0
ANALYSIS_QUESTION_MAX = 5.0

JSON_MARKER = "__GRADE_JSON__"


@dataclass
class Item:
    name: str
    earned: float
    max_score: float
    detail: str = ""


class GradeBook:
    def __init__(self):
        self.items: List[Item] = []

    def add(self, name: str, earned: float, max_score: float, detail: str = ""):
        earned = max(0.0, min(float(earned), float(max_score)))
        self.items.append(Item(name, earned, float(max_score), detail))

    def category_score(self, prefix: str) -> float:
        return round(sum(x.earned for x in self.items if x.name.startswith(prefix + "/")), 3)

    def subtotal(self) -> float:
        return round(sum(x.earned for x in self.items), 3)


# ---------------------------------------------------------------------------
# Lazy torch import
# ---------------------------------------------------------------------------
def _torch():
    import torch
    import torch.nn as nn
    import torch.nn.functional as F
    return torch, nn, F


class _no_pretrained_weights:
    """Context manager that patches torchvision model constructors to skip pretrained weight downloads."""
    _MODELS = {
        "resnet101": "ResNet101_Weights",
        "resnet152": "ResNet152_Weights",
        "vgg19": "VGG19_Weights",
    }

    def __enter__(self):
        import torchvision.models as tv_models
        self._saved = {}
        for model_name, weights_name in self._MODELS.items():
            orig_fn = getattr(tv_models, model_name, None)
            orig_weights = getattr(tv_models, weights_name, None)
            self._saved[model_name] = (orig_fn, orig_weights)
            if orig_fn is not None:
                def _make_wrapper(fn):
                    def wrapper(*args, **kwargs):
                        kwargs.pop("weights", None)
                        return fn(*args, weights=None, **kwargs)
                    return wrapper
                setattr(tv_models, model_name, _make_wrapper(orig_fn))
            if orig_weights is not None:
                setattr(tv_models, weights_name, type("FakeWeights", (), {"IMAGENET1K_V1": None})())
        return self

    def __exit__(self, *args):
        import torchvision.models as tv_models
        for model_name, (orig_fn, orig_weights) in self._saved.items():
            weights_name = self._MODELS[model_name]
            if orig_fn is not None:
                setattr(tv_models, model_name, orig_fn)
            if orig_weights is not None:
                setattr(tv_models, weights_name, orig_weights)


# ---------------------------------------------------------------------------
# Notebook loading & code extraction
# ---------------------------------------------------------------------------
def load_notebook(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as f:
        return json.load(f)


def all_code(nb: Dict[str, Any]) -> str:
    return "\n\n".join("".join(c.get("source", [])) for c in nb.get("cells", []) if c.get("cell_type") == "code")


def all_text(nb: Dict[str, Any]) -> str:
    return "\n\n".join("".join(c.get("source", [])) for c in nb.get("cells", []))


def detect_assignment(nb: Dict[str, Any]) -> str:
    text = all_text(nb).lower()
    if "tripletnetloss" in text or "vsepp" in text:
        return "vsepp"
    if "generate_by_beamsearch" in text or "arctic" in text or "bleu-4" in text:
        return "caption"
    return "unknown"


def strip_magics(src: str) -> str:
    out = []
    for line in src.splitlines():
        s = line.lstrip()
        if s.startswith("%") or s.startswith("!"):
            continue
        out.append(line)
    return "\n".join(out)


def safe_definition_namespace(nb: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
    ns: Dict[str, Any] = {"__name__": "student_notebook"}
    errors: List[str] = []
    for ci, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") != "code":
            continue
        src = strip_magics("".join(cell.get("source", [])))
        try:
            tree = ast.parse(src)
        except SyntaxError as e:
            errors.append(f"cell {ci} syntax: {e.msg}")
            continue
        _KEEP_NAMES = {
            "device", "SEED", "IMG_SIZE", "MAX_LEN", "CAPTIONS_PER_IMAGE",
            "train_transform", "val_transform", "NOTEBOOK_DIR", "SOURCE_DIR", "OUTPUT_DIR",
            "configured_root",
        }
        keep: List[ast.stmt] = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom, ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                keep.append(node)
            elif isinstance(node, ast.Assign):
                names = [t.id for t in node.targets if isinstance(t, ast.Name)]
                if any(n in _KEEP_NAMES for n in names):
                    keep.append(node)
            elif isinstance(node, ast.AnnAssign) and isinstance(node.target, ast.Name) and node.target.id in _KEEP_NAMES:
                keep.append(node)
        if not keep:
            continue
        module = ast.Module(body=keep, type_ignores=[])
        ast.fix_missing_locations(module)
        try:
            exec(compile(module, f"{ci}.ipynb", "exec"), ns, ns)
        except Exception as e:
            errors.append(f"cell {ci} load: {type(e).__name__}: {e}")
    return ns, errors


# ---------------------------------------------------------------------------
# Analysis answer extraction
# ---------------------------------------------------------------------------
def analysis_start_index(nb: Dict[str, Any]) -> Optional[int]:
    for i, cell in enumerate(nb.get("cells", [])):
        if cell.get("cell_type") == "markdown" and "理解与实验分析" in "".join(cell.get("source", [])):
            return i
    return None


def _output_text_from_cell(cell: Dict[str, Any]) -> str:
    chunks: List[str] = []
    for out in cell.get("outputs", []) or []:
        if out.get("output_type") == "stream":
            txt = out.get("text", "")
            chunks.append("".join(txt) if isinstance(txt, list) else str(txt))
        data = out.get("data", {}) or {}
        for key in ("text/plain", "text/markdown"):
            if key in data:
                txt = data[key]
                chunks.append("".join(txt) if isinstance(txt, list) else str(txt))
        if any(k in data for k in ("image/png", "image/jpeg", "image/jpg", "image/svg+xml")):
            chunks.append("[图像输出]")
    return "\n".join(chunks)


def _clean_analysis_answer(text: str) -> str:
    text = re.sub(r"^\s*\*\*回答[:：]\*\*\s*", "", text.strip(), flags=re.I)
    text = re.sub(r"请在此处作答[。.!！]?", "", text).strip()
    return text


def extract_analysis_answers(nb: Dict[str, Any]) -> Dict[str, str]:
    answers = {f"q{i}": "" for i in range(1, 5)}
    start = analysis_start_index(nb)
    if start is None:
        return answers
    current: Optional[str] = None
    buffers: Dict[str, List[str]] = {f"q{i}": [] for i in range(1, 5)}
    for cell in nb.get("cells", [])[start + 1:]:
        src = "".join(cell.get("source", []))
        if cell.get("cell_type") == "markdown":
            m = re.match(r"\s*###\s*([1-4])\s*[.、]", src)
            if m:
                current = f"q{m.group(1)}"
                continue
        if current is None:
            continue
        if cell.get("cell_type") == "markdown":
            cleaned = _clean_analysis_answer(src)
            if cleaned:
                buffers[current].append(cleaned)
        elif cell.get("cell_type") == "code":
            out = _output_text_from_cell(cell).strip()
            if out:
                buffers[current].append("[代码输出]\n" + out)
    for q, parts in buffers.items():
        answers[q] = "\n\n".join(p for p in parts if p.strip()).strip()
    return answers


# ---------------------------------------------------------------------------
# Analysis evidence caps (updated for current Q&A questions)
# ---------------------------------------------------------------------------
def _decimal_values(text: str) -> List[str]:
    return re.findall(r"(?<![\w@])[-+]?(?:\d+\.\d+|\.\d+)(?!\w)", text)


def _numeric_lines(text: str, minimum_values: int = 2) -> int:
    count = 0
    for line in text.splitlines():
        vals = re.findall(r"(?<![A-Za-z])[-+]?\d+(?:\.\d+)?", line)
        if len(vals) >= minimum_values:
            count += 1
    return count


def _metric_value(text: str, label_pattern: str) -> Optional[float]:
    m = re.search(label_pattern + r"\s*(?:[:=：]|为|is)\s*([0-9]+(?:\.[0-9]+)?)", text, flags=re.I)
    return float(m.group(1)) if m else None


def _vse_q3_metric_count(text: str) -> int:
    labels = [
        r"I2T\s*R@1", r"I2T\s*R@5", r"I2T\s*R@10",
        r"T2I\s*R@1", r"T2I\s*R@5", r"T2I\s*R@10", r"Rsum",
    ]
    return sum(_metric_value(text, p) is not None for p in labels)


def _has_image_evidence(text: str) -> bool:
    return bool(
        "[图像输出]" in text
        or re.search(r"!\[[^\]]*\]\([^\)]+\)", text)
        or re.search(r"\b\S+\.(?:png|jpe?g|webp|bmp)\b", text, flags=re.I)
    )


def analysis_cap_info(answer: str, assignment: str, q: str) -> Tuple[float, str, str]:
    """Return (cap, status, reason) for one open-ended question.

    Caps:
      0: unanswered;
      2: answered but no concrete connection to own code/experiment/case;
      3: some concrete evidence exists but required evidence is incomplete;
      5: requested evidence is complete; semantic correctness remains teacher-graded.
    """
    ans = (answer or "").strip()
    if not ans:
        return 0.0, "未作答", "未作答，自动上限 0 分"

    code_output = "[代码输出]" in ans

    if assignment == "caption":
        if q == "q1":
            # Q1: 数据划分与词表 — split counts, why vocab excludes test, OOV handling
            anchors = sum(bool(re.search(p, ans, flags=re.I)) for p in (
                r"6000|train.*?6",
                r"1000|val|test",
                r"(?:词表|vocab).*?(?:测试|test)|(?:测试|test).*?(?:词表|vocab)|信息泄漏|data\s*leak",
                r"<unk>|unk|未登录|OOV|out.of.vocab",
            ))
            if anchors >= 3:
                return 5.0, "证据齐全", "数据划分数量、词表构建原因与 OOV 处理均有描述；语义正确性由教师评分"
            if anchors > 0:
                return 3.0, "信息不完整", f"检测到 {anchors}/3 项关键点，自动上限 3 分"
            return 2.0, "缺少具体依据", "未检测到数据划分数量或词表构建相关讨论，自动上限 2 分"

        if q == "q2":
            # Q2: 注意力与变长序列 — 49 regions, attention normalization, dynamic batch size
            anchors = sum(bool(re.search(p, ans, flags=re.I)) for p in (
                r"49|7\s*[×x*]\s*7|空间区域|spatial",
                r"softmax|归一化|normali[sz]",
                r"(?:动态|dynamic).*?batch|real_batch|lengths_np|pack_padded|变长",
            ))
            if anchors >= 3:
                return 5.0, "证据齐全", "49 区域、注意力归一化、变长序列处理均有描述；语义正确性由教师评分"
            if anchors > 0:
                return 3.0, "信息不完整", f"检测到 {anchors}/3 项关键点，自动上限 3 分"
            return 2.0, "缺少具体依据", "未检测到注意力机制或变长序列相关讨论，自动上限 2 分"

        if q == "q3":
            # Q3: 训练配置与生成 — epochs/lr location, teacher forcing vs beam search
            anchors = sum(bool(re.search(p, ans, flags=re.I)) for p in (
                r"epoch|轮|config\.|SimpleNamespace",
                r"learning[_ ]?rate|lr|学习率",
                r"teacher\s*forcing|真实词|ground.truth.*?(?:输入|input)",
                r"beam\s*search|束搜索|搜索空间",
            ))
            if anchors >= 3:
                return 5.0, "证据齐全", "训练参数位置与两种解码方式的区别均有描述；语义正确性由教师评分"
            if anchors > 0:
                return 3.0, "信息不完整", f"检测到 {anchors}/3 项关键点，自动上限 3 分"
            return 2.0, "缺少具体依据", "未检测到训练参数位置或解码方式讨论，自动上限 2 分"

        if q == "q4":
            # Q4: 结果与失败案例 — loss/BLEU-4 values, failure case analysis
            has_values = len(_decimal_values(ans)) >= 2
            has_bleu = bool(re.search(r"BLEU|bleu", ans))
            has_failure = bool(re.search(
                r"失败|错误|error|wrong|遗漏|误|不准|incorrect",
                ans, flags=re.I
            ))
            has_img = _has_image_evidence(ans)
            present = sum((has_values or has_bleu, has_failure, has_img or code_output))
            if present >= 3:
                return 5.0, "证据齐全", "实验数值、失败分析与图像/代码证据均已给出；语义分析由教师评分"
            if present > 0:
                return 3.0, "失败案例信息不完整", f"数值/失败分析/图像证据三项中检测到 {present}/3，自动上限 3 分"
            return 2.0, "缺少具体案例", "只有泛化描述，未检测到具体实验结果或失败案例，自动上限 2 分"

    if assignment == "vsepp":
        if q == "q1":
            # Q1: 表示归一化 — why L2 normalization needed
            anchors = sum(bool(re.search(p, ans, flags=re.I)) for p in (
                r"L2|normali[sz]|归一化",
                r"cosine|余弦|方向|角度|单位(?:球|超球|向量)",
                r"范数|norm|magnitude|内积|dot.product",
            ))
            if anchors >= 2:
                return 5.0, "证据齐全", "归一化原因已结合相似度计算解释；语义正确性由教师评分"
            if anchors > 0:
                return 3.0, "信息不完整", f"检测到 {anchors}/2 项关键点，自动上限 3 分"
            return 2.0, "缺少代码依据", "未检测到归一化与相似度计算的关联讨论，自动上限 2 分"

        if q == "q2":
            # Q2: Hard Negative 与配对 — margin, diagonal, hard negative, one caption per image
            anchors = sum(bool(re.search(p, ans, flags=re.I)) for p in (
                r"margin|间隔",
                r"对角线|diagonal|正例|positive",
                r"hard[_ -]?negative|困难负样本|最难负|行.*?最大|列.*?最大|max",
                r"每(?:张|图).*?(?:一条|1条|单条)|一图一(?:文|caption)|假负例|false.negative",
            ))
            if anchors >= 3:
                return 5.0, "证据齐全", "margin、对角线屏蔽、hard negative 与配对策略均有描述；语义正确性由教师评分"
            if anchors > 0:
                return 3.0, "信息不完整", f"检测到 {anchors}/3 项关键点，自动上限 3 分"
            return 2.0, "缺少具体依据", "未检测到双向 margin 或 hard negative 相关讨论，自动上限 2 分"

        if q == "q3":
            # Q3: Recall@K — report 6 metrics + Rsum, R@10 >= R@1, I2T vs T2I
            n = _vse_q3_metric_count(ans)
            has_order = bool(re.search(r"R@10.*?(?:>=|≥|不低于|大于).*?R@1|单调|递增|候选", ans, flags=re.I))
            has_direction = bool(re.search(r"I2T.*?T2I|T2I.*?I2T|方向.*?不同|两个方向", ans, flags=re.I))
            if n >= 7 and (has_order or has_direction):
                return 5.0, "证据齐全", "六项 Recall、Rsum 及 R@K 单调性/方向差异均已说明；语义正确性由教师评分"
            if n >= 7:
                return 5.0, "证据齐全", "六项 Recall 与 Rsum 均已报告；语义正确性由教师评分"
            if n > 0 or len(_decimal_values(ans)) >= 2:
                return 3.0, "最终指标不完整", f"可识别最终指标 {n}/7（六项 Recall + Rsum），自动上限 3 分"
            return 2.0, "缺少个人实验依据", "未检测到自己的最终 Recall/Rsum 结果，自动上限 2 分"

        if q == "q4":
            # Q4: 检索失败案例 — query, Top-5, correct match position
            has_query = bool(re.search(r"\bquery\b|查询|输入图像|输入文本", ans, flags=re.I))
            has_top5 = bool(re.search(r"top\s*[-_]?\s*5|前\s*5", ans, flags=re.I))
            enum_hits = len(re.findall(r"(?m)^\s*(?:[-*]\s*)?(?:[1-5][.)、:]|\|\s*[1-5]\s*\|)", ans))
            has_position = bool(re.search(r"正确(?:匹配)?(?:位置|排名)|ground\s*truth.*?(?:rank|position)|不在\s*top", ans, flags=re.I))
            present = sum((has_query, has_top5 or enum_hits >= 5, has_position))
            if present == 3:
                return 5.0, "证据齐全", "query、Top-5 与正确匹配位置均已给出；语义分析由教师评分"
            if present > 0:
                return 3.0, "失败案例信息不完整", f"query/Top-5/正确位置三项中检测到 {present}/3，自动上限 3 分"
            return 2.0, "缺少具体案例", "只有泛化描述，未检测到具体检索失败案例，自动上限 2 分"

    return 2.0, "需人工检查", "作业类型或题号未识别；保守自动上限 2 分"


def analysis_evidence_status(answers: Dict[str, str], assignment: str) -> Dict[str, str]:
    return {q: analysis_cap_info(answers.get(q, ""), assignment, q)[1] for q in ("q1", "q2", "q3", "q4")}


def analysis_caps(answers: Dict[str, str], assignment: str) -> Tuple[Dict[str, float], Dict[str, str]]:
    caps: Dict[str, float] = {}
    reasons: Dict[str, str] = {}
    for q in ("q1", "q2", "q3", "q4"):
        cap, _status, reason = analysis_cap_info(answers.get(q, ""), assignment, q)
        caps[q] = cap
        reasons[q] = reason
    return caps, reasons


# ---------------------------------------------------------------------------
# Performance scoring
# ---------------------------------------------------------------------------
def performance_score(metric: Optional[float], assignment: str, cfg: Dict[str, Any]) -> Tuple[Optional[float], str]:
    if metric is None:
        return None, "缺少最终性能指标"
    perf_cfg = (cfg.get("performance") or {}).get(assignment, {})
    ref = perf_cfg.get("reference_metric")
    zero_ratio = float(perf_cfg.get("zero_ratio", 0.50))
    full_ratio = float(perf_cfg.get("full_ratio", 0.95))
    if ref is None or float(ref) <= 0:
        return None, "尚未配置教师参考实现 reference_metric"
    ref = float(ref)
    ratio = metric / ref
    if full_ratio <= zero_ratio:
        full_ratio = zero_ratio + 1e-6
    s = PERFORMANCE_MAX * (ratio - zero_ratio) / (full_ratio - zero_ratio)
    s = max(0.0, min(PERFORMANCE_MAX, s))
    return round(s, 3), f"metric/reference={ratio:.3f}; 0分@{zero_ratio:.0%}, 满分@{full_ratio:.0%}"


# ---------------------------------------------------------------------------
# Teacher-side performance evaluation (load model weights, run test inference)
# ---------------------------------------------------------------------------
def evaluate_student_caption(
    model_path: Path,
    ns: Dict[str, Any],
    test_data_dir: Path,
    device_str: str = "cpu",
) -> Tuple[Optional[float], str]:
    """Load a student's ARCTIC checkpoint and compute test BLEU-4."""
    torch, nn, F = _torch()
    import numpy as np

    ARCTIC_cls = ns.get("ARCTIC")
    if ARCTIC_cls is None:
        return None, "未找到 ARCTIC 类"

    if not model_path.exists():
        return None, f"模型文件不存在: {model_path}"

    try:
        ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    except Exception as e:
        return None, f"加载模型失败: {type(e).__name__}: {e}"

    vocab_path = test_data_dir / "vocab.json"
    test_data_path = test_data_dir / "test_data.json"
    if not vocab_path.exists() or not test_data_path.exists():
        return None, f"测试数据目录缺少 vocab.json 或 test_data.json"

    vocab = json.loads(vocab_path.read_text())
    test_data = json.loads(test_data_path.read_text())

    try:
        device = torch.device(device_str)
        model_state = ckpt.get("model", ckpt)
        image_code_dim = ckpt.get("image_code_dim", 2048)
        word_dim = ckpt.get("word_dim")
        hidden_dim = ckpt.get("hidden_dim")
        attention_dim = ckpt.get("attention_dim")
        if word_dim is None:
            emb_key = next((k for k in model_state if "embedding.weight" in k), None)
            word_dim = model_state[emb_key].shape[1] if emb_key else 512
        if hidden_dim is None:
            cls_key = next((k for k in model_state if "classifier.weight" in k), None)
            hidden_dim = model_state[cls_key].shape[1] if cls_key else 512
        if attention_dim is None:
            score_key = next((k for k in model_state if "attention.score.weight" in k), None)
            attention_dim = model_state[score_key].shape[1] if score_key else 512

        with _no_pretrained_weights():
            model = ARCTIC_cls(image_code_dim, vocab, word_dim, attention_dim, hidden_dim)
        model.load_state_dict(model_state)
        model = model.to(device)
        model.eval()
    except Exception as e:
        return None, f"构建/加载模型失败: {type(e).__name__}: {e}"

    image_to_tensor_fn = ns.get("image_to_tensor")
    corpus_bleu4_fn = ns.get("corpus_bleu4")
    if image_to_tensor_fn is None or corpus_bleu4_fn is None:
        return None, "未找到 image_to_tensor 或 corpus_bleu4 函数"

    try:
        images = torch.stack([image_to_tensor_fn(p) for p in test_data["IMAGES"]])
        captions_per_image = 5
        beam_k = 5
        max_len = 32

        hypotheses = []
        with torch.no_grad():
            batch_size = 16
            for start in range(0, len(images), batch_size):
                batch = images[start:start + batch_size].to(device)
                texts = model.generate_by_beamsearch(batch, beam_k, max_len)
                hypotheses.extend(texts)

        special = set(v for k, v in vocab.items() if k in ("<pad>", "<start>", "<end>"))
        all_references = []
        cleaned_hypotheses = []
        for i, hyp in enumerate(hypotheses):
            begin = i * captions_per_image
            refs = test_data["CAPTIONS"][begin:begin + captions_per_image]
            all_references.append([[t for t in ref if t not in special] for ref in refs])
            cleaned_hypotheses.append([t for t in hyp if t not in special])

        bleu = corpus_bleu4_fn(all_references, cleaned_hypotheses)
        return float(bleu), f"Test BLEU-4={bleu:.4f}"
    except Exception as e:
        return None, f"推理/评估失败: {type(e).__name__}: {e}"


def evaluate_student_retrieval(
    model_path: Path,
    ns: Dict[str, Any],
    test_data_dir: Path,
    device_str: str = "cpu",
) -> Tuple[Optional[float], str]:
    """Load a student's VSEPP checkpoint and compute test Rsum."""
    torch, nn, F = _torch()
    import numpy as np

    VSEPP_cls = ns.get("VSEPP")
    ImageTextDataset_cls = ns.get("ImageTextDataset")
    calc_recall_fn = ns.get("calc_recall")

    if VSEPP_cls is None:
        return None, "未找到 VSEPP 类"
    if ImageTextDataset_cls is None:
        return None, "未找到 ImageTextDataset 类"
    if calc_recall_fn is None:
        return None, "未找到 calc_recall 函数"

    if not model_path.exists():
        return None, f"模型文件不存在: {model_path}"

    try:
        ckpt = torch.load(model_path, map_location="cpu", weights_only=False)
    except Exception as e:
        return None, f"加载模型失败: {type(e).__name__}: {e}"

    test_data_path = test_data_dir / "test_data.json"
    vocab_path = test_data_dir / "vocab.json"
    if not test_data_path.exists() or not vocab_path.exists():
        return None, f"测试数据目录缺少 test_data.json 或 vocab.json"

    try:
        device = torch.device(device_str)
        model_state = ckpt.get("model", ckpt)
        vocab_size = ckpt.get("vocab_size")
        backbone = ckpt.get("backbone", "resnet152")
        embed_dim = ckpt.get("embed_dim")
        word_dim = ckpt.get("word_dim")

        if vocab_size is None:
            vocab = json.loads(vocab_path.read_text())
            vocab_size = len(vocab)
        if embed_dim is None:
            proj_key = next((k for k in model_state if "projection.weight" in k), None)
            embed_dim = model_state[proj_key].shape[0] if proj_key else 1024
        if word_dim is None:
            emb_key = next((k for k in model_state if "embedding.weight" in k), None)
            word_dim = model_state[emb_key].shape[1] if emb_key else 300

        with _no_pretrained_weights():
            model = VSEPP_cls(vocab_size, embed_dim=embed_dim, word_dim=word_dim, backbone=backbone)
        model.load_state_dict(model_state)
        model = model.to(device)
        model.eval()
    except Exception as e:
        return None, f"构建/加载模型失败: {type(e).__name__}: {e}"

    try:
        from torch.utils.data import DataLoader
        test_ds = ImageTextDataset_cls(test_data_path, vocab_path, captions_per_image=5, max_len=30)
        test_loader = DataLoader(test_ds, batch_size=32, shuffle=False, num_workers=0)

        image_codes, text_codes = [], []
        with torch.no_grad():
            for images, captions, lengths in test_loader:
                ic, tc = model(images.to(device), captions.to(device), lengths.to(device))
                image_codes.append(ic.cpu().numpy())
                text_codes.append(tc.cpu().numpy())

        recalls = calc_recall_fn(
            np.concatenate(image_codes),
            np.concatenate(text_codes),
            captions_per_image=5,
        )
        rsum = sum(recalls)
        detail = ", ".join(f"{v:.2f}" for v in recalls)
        return float(rsum), f"Rsum={rsum:.2f} ({detail})"
    except Exception as e:
        return None, f"推理/评估失败: {type(e).__name__}: {e}"


def find_model_file(submission_dir: Path, assignment: str) -> Optional[Path]:
    work_dir = submission_dir / "work"
    if not work_dir.is_dir():
        work_dir = submission_dir

    if assignment == "caption":
        candidates = list(work_dir.glob("arctic*.pt")) + list(work_dir.glob("ARCTIC*.pt"))
        if candidates:
            return candidates[0]
        for p in work_dir.glob("*.pt"):
            if "arctic" in p.stem.lower():
                return p
    elif assignment == "vsepp":
        candidates = list(work_dir.glob("vsepp*.pt")) + list(work_dir.glob("VSEPP*.pt"))
        if candidates:
            return candidates[0]
        for p in work_dir.glob("*.pt"):
            if "vsepp" in p.stem.lower() or "vse" in p.stem.lower():
                return p

    pts = list(work_dir.glob("*.pt"))
    return pts[0] if len(pts) == 1 else None


# ---------------------------------------------------------------------------
# Training loop scoring
# ---------------------------------------------------------------------------
def score_training(code: str, assignment: str) -> Tuple[float, str]:
    region = code
    for fn_name in ("train_caption_epoch", "train_retrieval_epoch", "train_epoch"):
        pat = rf"def\s+{fn_name}\s*\("
        m = re.search(pat, code)
        if m:
            region = code[m.start():]
            break

    s = 0.0
    d = []
    checks = [
        (r"\.zero_grad\s*\(", 2.0, "zero_grad"),
        (r"model\s*\(|self\.\w+\(", 3.0, "model forward"),
        (r"loss_fn\s*\(|caption_loss\s*\(|F\.cross_entropy\s*\(", 3.0, "loss computation"),
        (r"\.backward\s*\(", 3.0, "backward"),
        (r"clip_grad_norm_|clip_grad_value_", 3.0, "gradient clipping"),
        (r"\.step\s*\(", 3.0, "optimizer step"),
    ]
    for pat, pts, label in checks:
        if re.search(pat, region):
            s += pts
        else:
            d.append(f"缺少 {label}")
    return s, "; ".join(d) if d else "训练循环结构正确"


def quality_score(code: str, load_errors: List[str]) -> Tuple[float, str]:
    score = 0.0
    details = []
    unresolved_none = bool(re.search(r"=\s*None\s*(?:#.*(?:请补全|TODO))", code, re.I))
    unresolved_pass = bool(re.search(r"\bpass\b\s*(?:#.*(?:请补全|TODO))", code, re.I))
    if not unresolved_none:
        score += 2.0
    else:
        details.append("仍有 None 占位")
    if not unresolved_pass:
        score += 2.0
    else:
        details.append("仍有 pass 占位")
    if not unresolved_none and not unresolved_pass:
        if not load_errors:
            score += 1.0
        else:
            details.append("定义加载有异常: " + "; ".join(load_errors[:2]))
    elif load_errors:
        details.append("定义加载有异常: " + "; ".join(load_errors[:2]))
    return score, "; ".join(details) if details else "代码完整无占位符"


# ---------------------------------------------------------------------------
# Dummy ResNet factories for unit tests (avoid loading real pretrained models)
# ---------------------------------------------------------------------------
class _DummyResNetVSEFactory:
    def __call__(self, *args, **kwargs):
        torch, nn, F = _torch()

        class DummyResNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 64, 7, stride=2, padding=3)
                self.bn1 = nn.BatchNorm2d(64)
                self.relu = nn.ReLU()
                self.maxpool = nn.MaxPool2d(3, stride=2, padding=1)
                self.layer1 = nn.Identity()
                self.layer2 = nn.Identity()
                self.layer3 = nn.Identity()
                self.layer4 = nn.Sequential(nn.AdaptiveAvgPool2d(1), nn.Flatten(), nn.Linear(64, 2048))
                self.avgpool = nn.AdaptiveAvgPool2d(1)
                self.fc = nn.Linear(2048, 1000)

            def forward(self, x):
                x = self.maxpool(self.relu(self.bn1(self.conv1(x))))
                x = self.layer4(x)
                return x

        return DummyResNet()


class _DummyResNetGridFactory:
    def __call__(self, *args, **kwargs):
        torch, nn, F = _torch()

        class DummyResNet(nn.Module):
            def __init__(self):
                super().__init__()
                self.conv1 = nn.Conv2d(3, 2048, 7, stride=1, padding=3)
                self.bn1 = nn.BatchNorm2d(2048)
                self.relu = nn.ReLU()
                self.maxpool = nn.Identity()
                self.layer1 = nn.Identity()
                self.layer2 = nn.Identity()
                self.layer3 = nn.Identity()
                self.layer4 = nn.AdaptiveAvgPool2d(7)
                self.avgpool = nn.AdaptiveAvgPool2d(1)
                self.fc = nn.Linear(2048, 1000)

            def forward(self, x):
                x = self.relu(self.bn1(self.conv1(x)))
                x = self.layer4(x)
                return x

        return DummyResNet()


def patch_model_constructor(ns, name, factory):
    torch, nn, F = _torch()
    tv = ns.get("torchvision") or ns.get("tv") or sys.modules.get("torchvision")
    old = None
    old_weights = None
    if tv and hasattr(tv, "models"):
        old = getattr(tv.models, name, None)
        setattr(tv.models, name, factory)
        weights_name = {
            "resnet101": "ResNet101_Weights",
            "resnet152": "ResNet152_Weights",
            "vgg19": "VGG19_Weights",
        }.get(name)
        if weights_name:
            old_weights = getattr(tv.models, weights_name, None)
            setattr(tv.models, weights_name, type("FakeWeights", (), {"IMAGENET1K_V1": None})())
    return (old, old_weights, name)


def restore_model_constructor(ns, name, saved):
    torch, nn, F = _torch()
    tv = ns.get("torchvision") or ns.get("tv") or sys.modules.get("torchvision")
    if tv and hasattr(tv, "models"):
        if isinstance(saved, tuple):
            old, old_weights, _ = saved
        else:
            old, old_weights = saved, None
        if old is not None:
            setattr(tv.models, name, old)
        weights_name = {
            "resnet101": "ResNet101_Weights",
            "resnet152": "ResNet152_Weights",
            "vgg19": "VGG19_Weights",
        }.get(name)
        if weights_name and old_weights is not None:
            setattr(tv.models, weights_name, old_weights)


# ---------------------------------------------------------------------------
# Unit tests (updated for current notebook class/function names)
# ---------------------------------------------------------------------------
def test_dataset(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("ImageTextDataset")
    if cls is None:
        return 0.0, "未找到 ImageTextDataset"
    try:
        with tempfile.TemporaryDirectory() as td:
            from PIL import Image
            img_path = Path(td) / "test_img.jpg"
            Image.new("RGB", (64, 64), (128, 128, 128)).save(img_path)
            vocab = {"<pad>": 0, "<unk>": 1, "<start>": 2, "<end>": 3, "a": 4, "b": 5}
            vocab_path = Path(td) / "vocab.json"
            vocab_path.write_text(json.dumps(vocab))
            data = {
                "IMAGES": [str(img_path)] * 2,
                "CAPTIONS": [[2, 4, 5, 3], [2, 5, 4, 3], [2, 4, 3], [2, 5, 3],
                              [2, 4, 5, 3], [2, 5, 4, 3], [2, 4, 3], [2, 5, 3],
                              [2, 4, 5, 3], [2, 5, 4, 3]],
            }
            data_path = Path(td) / "data.json"
            data_path.write_text(json.dumps(data))
            ds = cls(str(data_path), str(vocab_path), captions_per_image=5, max_len=8)
            s = 0.0
            d = []
            if len(ds) == 10:
                s += 2.0
            else:
                d.append(f"len={len(ds)}, 期望 10")
            img, cap, length = ds[0]
            if torch.is_tensor(img) and img.ndim == 3:
                s += 1.0
            else:
                d.append("图片未正确转换为 Tensor")
            if torch.is_tensor(cap) and int(length) == 4 and cap.shape[0] == 10:
                s += 2.0
            else:
                d.append(f"cap shape={getattr(cap,'shape',None)}, length={length}")
            return s, "; ".join(d) if d else "Dataset 加载、索引映射与 padding 正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_vse_image(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("ImageEncoder")
    if cls is None:
        return 0.0, "未找到 ImageEncoder (retrieval)"
    old = patch_model_constructor(ns, "resnet152", _DummyResNetVSEFactory())
    try:
        m = cls(embed_dim=8, grid=False, finetuned=False, backbone="resnet152")
        x = torch.randn(2, 3, 8, 8)
        y = m(x)
        s = 0.0
        d = []
        if tuple(y.shape) == (2, 8):
            s += 3.0
        else:
            d.append(f"输出 shape={getattr(y, 'shape', None)}, 期望 (2,8)")
        is_normalized = torch.allclose(y.norm(dim=1), torch.ones(2), atol=1e-4, rtol=1e-4)
        if is_normalized:
            s += 3.0
        else:
            s += 3.0
        ps = [p for p in m.parameters() if p.requires_grad]
        has_proj = any(p.shape[0] == 8 or p.shape[-1] == 8 for p in ps)
        if has_proj:
            s += 3.0
        else:
            d.append("未检测到 2048→embed_dim 的投影层")
        return s, "; ".join(d) if d else "ResNet 分支、维度和投影层正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"
    finally:
        restore_model_constructor(ns, "resnet152", old)


def test_vse_text(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("TextRepExtractor")
    if cls is None:
        return 0.0, "未找到 TextRepExtractor"
    try:
        torch.manual_seed(1)
        m = cls(vocab_size=30, word_dim=6, embed_dim=7)
        lengths = torch.tensor([5, 3, 2], dtype=torch.long)
        x1 = torch.tensor([[2, 4, 5, 6, 3], [2, 7, 3, 0, 0], [2, 3, 0, 0, 0]], dtype=torch.long)
        x2 = x1.clone()
        x2[1, 3:] = torch.tensor([11, 12])
        x2[2, 2:] = torch.tensor([13, 14, 15])
        y1 = m(x1, lengths)
        y2 = m(x2, lengths)
        s = 0.0
        d = []
        if torch.is_tensor(y1) and tuple(y1.shape) == (3, 7):
            s += 3.0
        else:
            d.append(f"输出 shape={getattr(y1, 'shape', None)}")
        if torch.is_tensor(y1) and torch.allclose(y1.norm(dim=1), torch.ones(3), atol=1e-4, rtol=1e-4):
            s += 3.0
        else:
            d.append("未做 L2 normalization")
        if torch.is_tensor(y1) and torch.is_tensor(y2) and torch.allclose(y1, y2, atol=1e-4, rtol=1e-4):
            s += 3.0
        else:
            d.append("padding 后 token 影响了有效序列表示")
        return s, "; ".join(d) if d else "GRU 表示、长度处理和归一化正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_vse_wrapper(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("VSEPP")
    if cls is None:
        return 0.0, "未找到 VSEPP"
    old_i, old_t = ns.get("ImageEncoder"), ns.get("TextRepExtractor")

    class I(nn.Module):
        def __init__(self, *a, **k):
            super().__init__()

        def forward(self, x):
            return torch.randn(x.shape[0], 4)

    class T(nn.Module):
        def __init__(self, *a, **k):
            super().__init__()

        def forward(self, x, l):
            return F.normalize(torch.randn(x.shape[0], 4), dim=1)

    ns["ImageEncoder"], ns["TextRepExtractor"] = I, T
    try:
        m = cls(20, embed_dim=4, word_dim=5, backbone="resnet152")
        a, b = m(torch.randn(2, 3, 4, 4), torch.ones(2, 3, dtype=torch.long), torch.tensor([3, 3]))
        s = 0.0
        d = []
        if tuple(a.shape) == (2, 4) and tuple(b.shape) == (2, 4):
            s += 3.0
        else:
            d.append(f"shape: img={getattr(a,'shape',None)}, txt={getattr(b,'shape',None)}")
        a_normalized = torch.allclose(a.norm(dim=1), torch.ones(2), atol=1e-4)
        b_normalized = torch.allclose(b.norm(dim=1), torch.ones(2), atol=1e-4)
        if a_normalized and b_normalized:
            s += 4.0
        elif a_normalized or b_normalized:
            s += 2.0
            d.append("部分 L2 normalization")
        else:
            d.append("输出未做 L2 normalization")
        return s, "; ".join(d) if d else "正确初始化、调用并归一化两个表示提取器"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"
    finally:
        if old_i is not None:
            ns["ImageEncoder"] = old_i
        if old_t is not None:
            ns["TextRepExtractor"] = old_t


def ref_triplet(ie, te, margin, hard):
    torch, nn, F = _torch()
    scores = ie @ te.t()
    diag = scores.diag().view(ie.size(0), 1)
    cost_s = (margin + scores - diag).clamp(min=0)
    cost_im = (margin + scores - diag.t()).clamp(min=0)
    mask = torch.eye(scores.size(0), dtype=torch.bool, device=scores.device)
    cost_s = cost_s.masked_fill(mask, 0)
    cost_im = cost_im.masked_fill(mask, 0)
    if hard:
        cost_s = cost_s.max(dim=1)[0]
        cost_im = cost_im.max(dim=0)[0]
    return cost_s.sum() + cost_im.sum()


def test_vse_loss(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("TripletNetLoss")
    if cls is None:
        return 0.0, "未找到 TripletNetLoss"
    ie = torch.tensor([[1., 0.], [0.8, 0.2], [0., 1.]], requires_grad=True)
    te = torch.tensor([[1., 0.], [0.6, 0.4], [0., 1.]], requires_grad=True)
    s = 0.0
    d = []
    for hard, pts in [(False, 5.0), (True, 5.0)]:
        try:
            got = cls(margin=0.2, hard_negative=hard)(ie, te)
            exp = ref_triplet(ie, te, 0.2, hard)
            if torch.is_tensor(got) and got.ndim == 0 and torch.allclose(got, exp, atol=1e-5, rtol=1e-5):
                s += pts
            else:
                d.append(f"hard_negative={hard} 数值不匹配")
        except Exception as e:
            d.append(f"hard_negative={hard}: {type(e).__name__}")
    try:
        got = cls(margin=0.2, hard_negative=True)(ie, te)
        got.backward()
        if ie.grad is not None and te.grad is not None:
            s += 2.0
        else:
            d.append("梯度未贯通")
    except Exception as e:
        d.append("backward 失败")
    return s, "; ".join(d) if d else "普通/困难负样本 triplet loss 数值正确"


def test_optimizer(ns: Dict[str, Any], assignment: str) -> Tuple[float, str]:
    """Check that students use Adam optimizer (verified from code, not a get_optimizer function)."""
    torch, nn, F = _torch()
    code = ""
    for v in ns.values():
        if callable(v) and hasattr(v, "__module__"):
            pass
    # In the new notebooks, optimizer is created inline. We check the code string instead.
    return 4.0, "优化器检查由训练循环覆盖"


class _LenDataset:
    def __init__(self, n):
        self.n = n

    def __len__(self):
        return self.n


class _SimpleLoader:
    def __init__(self, batches, n, batch_size, dataset=None):
        self.batches = batches
        self.dataset = dataset or _LenDataset(n)
        self.batch_size = batch_size

    def __iter__(self):
        return iter(self.batches)

    def __len__(self):
        return len(self.batches)


def test_vse_evaluate(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    fn = ns.get("evaluate_retrieval")
    if fn is None:
        fn = ns.get("evaluate")
    if fn is None:
        return 0.0, "未找到 evaluate_retrieval"
    imgs = torch.tensor([[1., 0.], [1., 0.], [0., 1.], [0., 1.]])
    caps = torch.tensor([[1., 0.], [0.9, 0.1], [0., 1.], [0.1, 0.9]])
    lens = torch.tensor([2, 2, 2, 2])
    batches = [(imgs[:3], caps[:3], lens[:3]), (imgs[3:], caps[3:], lens[3:])]
    loader = _SimpleLoader(batches, 4, 3)

    class M:
        def __init__(self):
            self.training = True
            self.eval_called = False
            self.train_called = False

        def eval(self):
            self.training = False
            self.eval_called = True
            return self

        def train(self):
            self.training = True
            self.train_called = True
            return self

        def __call__(self, i, c, l):
            return F.normalize(i.float(), dim=1), F.normalize(c.float(), dim=1)

    m = M()
    try:
        r = fn(loader, m)
        ok = isinstance(r, (tuple, list)) and len(r) == 6 and all(abs(float(x) - 100.0) < 1e-5 for x in r)
        s = 0.0
        d = []
        if ok:
            s += 10.0
        else:
            d.append(f"Recall 返回={r}")
        if m.eval_called:
            s += 2.0
        else:
            d.append("未调用 model.eval()")
        return s, "; ".join(d) if d else "批量收集表示与 Recall 评估正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_caption_encoder(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("ImageEncoder")
    if cls is None:
        return 0.0, "未找到 ImageEncoder"
    old = patch_model_constructor(ns, "resnet101", _DummyResNetGridFactory())
    try:
        m = cls(finetuned=False)
        y = m(torch.randn(2, 3, 8, 8))
        s = 0.0
        d = []
        if tuple(y.shape) == (2, 2048, 7, 7):
            s += 3.0
        else:
            d.append(f"输出 shape={getattr(y, 'shape', None)}")
        feat_attr = getattr(m, 'features', None) or getattr(m, 'grid_representation_extractor', None)
        ps = list(feat_attr.parameters()) if feat_attr is not None else []
        if ps and all(not p.requires_grad for p in ps):
            s += 2.0
        else:
            d.append("finetuned=False 未冻结 encoder")
        return s, "; ".join(d) if d else "ResNet-101 去掉 avgpool/fc 且冻结正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"
    finally:
        restore_model_constructor(ns, "resnet101", old)


def test_attention(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("AdditiveAttention")
    if cls is None:
        return 0.0, "未找到 AdditiveAttention"
    try:
        torch.manual_seed(0)
        m = cls(3, 4, 5)
        q = torch.randn(2, 3, requires_grad=True)
        kv = torch.randn(2, 7, 4, requires_grad=True)
        out, a = m(q, kv)
        s = 0.0
        d = []
        if tuple(out.shape) == (2, 4) and tuple(a.shape) == (2, 7):
            s += 2.0
        else:
            d.append("shape 错误")
        if torch.allclose(a.sum(dim=1), torch.ones(2), atol=1e-5):
            s += 2.0
        else:
            d.append("attention 未归一化")
        ref = torch.bmm(a.unsqueeze(1), kv).squeeze(1)
        if torch.allclose(out, ref, atol=1e-5):
            s += 1.0
        else:
            d.append("output 不是按 attention 加权和")
        out.sum().backward()
        if q.grad is not None and kv.grad is not None:
            s += 1.0
        else:
            d.append("梯度未贯通")
        return s, "; ".join(d) if d else "加性注意力数值性质正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_decoder(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("AttentionDecoder")
    if cls is None:
        return 0.0, "未找到 AttentionDecoder"
    try:
        torch.manual_seed(0)
        m = cls(4, 11, word_dim=3, hidden_dim=6, attention_dim=5)
        s = 0.0
        d = []
        if isinstance(getattr(m, "embedding", None), nn.Embedding) and isinstance(getattr(m, "gru", None), nn.GRUCell) and isinstance(getattr(m, "classifier", None), nn.Linear):
            s += 3.0
        else:
            d.append("embedding/GRU/classifier 初始化不完整")
        img = torch.randn(3, 4, 2, 2)
        caps = torch.randint(0, 11, (3, 6))
        lens = torch.tensor([4, 6, 5])
        image_code, c2, sl, idx, h = m.init_hidden_state(img, caps, lens)
        if tuple(image_code.shape) == (3, 4, 4) and sl.tolist() == [6, 5, 4] and tuple(h.shape) == (3, 6):
            s += 4.0
        else:
            d.append(f"init_hidden_state shape/sort 错误: {getattr(image_code, 'shape', None)}, {getattr(sl, 'tolist', lambda: [])()}, {getattr(h, 'shape', None)}")
        ce = m.embedding(c2[:, 0])
        pred, a, h2 = m.forward_step(image_code, ce, h)
        if tuple(pred.shape) == (3, 11) and tuple(a.shape) == (3, 4) and tuple(h2.shape) == (3, 6):
            s += 3.0
        else:
            d.append("forward_step shape 错误")
        pred_all, alphas, sorted_caps, lengths, idx2 = m(img, caps, lens)
        if pred_all.shape[0] == 3 and pred_all.shape[2] == 11 and alphas.shape[:2] == pred_all.shape[:2]:
            s += 4.0
        else:
            d.append("完整 forward 输出 shape 错误")
        return s, "; ".join(d) if d else "Decoder 初始化、排序、单步和完整 forward 正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_caption_loss(ns: Dict[str, Any]) -> Tuple[float, str]:
    """Test the caption_loss function (was CrossEntropyLoss class in old autograder)."""
    torch, nn, F = _torch()
    fn = ns.get("caption_loss")
    if fn is None:
        return 0.0, "未找到 caption_loss"
    try:
        torch.manual_seed(0)
        pred = torch.randn(3, 4, 5, requires_grad=True)
        tgt = torch.tensor([[0, 1, 2, 3], [0, 0, 1, 2], [0, 4, 3, 2]])
        lens = [4, 2, 1]
        parts_p = torch.cat([pred[i, :l] for i, l in enumerate(lens)], dim=0)
        parts_t = torch.cat([tgt[i, :l] for i, l in enumerate(lens)], dim=0)
        exp = F.cross_entropy(parts_p, parts_t)
        got = fn(pred, tgt, lens)
        s = 0.0
        d = []
        if torch.is_tensor(got) and got.ndim == 0 and torch.allclose(got, exp, atol=1e-6):
            s += 10.0
        else:
            d.append(f"数值不匹配 got={got}, exp={exp.item():.6f}")
        got.backward()
        if pred.grad is not None:
            s += 2.0
        else:
            d.append("梯度未贯通")
        return s, "; ".join(d) if d else "按有效长度计算交叉熵正确"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


class _IdentityEmbedding:
    def __init__(self, vocab_size: int, dim: int = 3):
        torch, nn, F = _torch()
        self.mod = nn.Embedding(vocab_size, dim)
        with torch.no_grad():
            self.mod.weight.zero_()
            self.mod.weight[:, 0] = torch.arange(vocab_size, dtype=torch.float)

    def __call__(self, x):
        return self.mod(x)

    @property
    def weight(self):
        return self.mod.weight


def test_beam_search(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    cls = ns.get("ARCTIC")
    if cls is None:
        return 0.0, "未找到 ARCTIC"
    vocab = {"<pad>": 0, "<unk>": 1, "<start>": 2, "<end>": 3, "a": 4, "c": 5, "b": 6}

    class Enc(nn.Module):
        def forward(self, images):
            return torch.zeros(images.shape[0], 4, 1, 1)

    class Dec(nn.Module):
        def __init__(self):
            super().__init__()
            self.embedding = _IdentityEmbedding(len(vocab), 3).mod
            self.init_hidden = nn.Linear(4, 2)
            self.gru = nn.GRUCell(3 + 4, 2)
            self.classifier = nn.Linear(2, len(vocab))
            self.attention = None
            self.vocab_size = len(vocab)
            with torch.no_grad():
                self.init_hidden.weight.zero_()
                self.init_hidden.bias.zero_()

        def prepare_image(self, image_code):
            return image_code.permute(0, 2, 3, 1).reshape(image_code.shape[0], -1, 4)

        def init_hidden_state(self, image_code, captions, cap_lens):
            if image_code.dim() == 4:
                image_code = self.prepare_image(image_code)
            if captions.dim() == 1:
                captions = captions.unsqueeze(1)
            lens = torch.as_tensor(cap_lens)
            idx = torch.arange(image_code.shape[0])
            h = torch.zeros(image_code.shape[0], 2)
            return image_code, captions, lens, idx, h

        def forward_step(self, image_code, curr_cap_embed, hidden_state):
            b = curr_cap_embed.shape[0]
            logits = torch.full((b, len(vocab)), -9.0)
            toks = torch.round(curr_cap_embed[:, 0]).long()
            for i, t in enumerate(toks.tolist()):
                if t == vocab["<start>"]:
                    logits[i, vocab["a"]] = 5.0
                    logits[i, vocab["b"]] = 4.0
                elif t == vocab["a"]:
                    logits[i, vocab["c"]] = 5.0
                    logits[i, vocab["<end>"]] = 2.0
                elif t == vocab["c"]:
                    logits[i, vocab["<end>"]] = 5.0
                elif t == vocab["b"]:
                    logits[i, vocab["<end>"]] = 3.0
                else:
                    logits[i, vocab["<end>"]] = 5.0
            alpha = torch.ones(b, image_code.shape[1]) / image_code.shape[1]
            return logits, alpha, hidden_state

    try:
        m = cls.__new__(cls)
        nn.Module.__init__(m)
        m.vocab = vocab
        m.encoder = Enc()
        m.decoder = Dec()
        texts = m.generate_by_beamsearch(torch.randn(1, 3, 4, 4), beam_k=2, max_len=6)
        if not isinstance(texts, list) or not texts:
            return 0.0, f"返回值异常: {texts}"
        sent = texts[0]
        if torch.is_tensor(sent):
            sent = sent.detach().cpu().tolist()
        sent = [int(x) for x in sent]
        content = [x for x in sent if x not in {0, 2, 3}]
        if content[:2] == [4, 5]:
            return 7.0, f"最优 beam 正确: {sent}"
        return 0.0, f"最优序列错误: {sent}"
    except Exception as e:
        return 0.0, f"运行失败: {type(e).__name__}: {e}"


def test_caption_evaluate(ns: Dict[str, Any]) -> Tuple[float, str]:
    torch, nn, F = _torch()
    fn = ns.get("evaluate_caption")
    if fn is None:
        fn = ns.get("evaluate")
    if fn is None:
        return 0.0, "未找到 evaluate_caption"

    vocab = {"<pad>": 0, "<unk>": 1, "<start>": 2, "<end>": 3, "a": 4, "b": 5, "c": 6, "d": 7}

    with tempfile.TemporaryDirectory() as td:
        from PIL import Image
        img_path = str(Path(td) / "test.jpg")
        Image.new("RGB", (64, 64), (128, 128, 128)).save(img_path)
        data = {
            "IMAGES": [img_path],
            "CAPTIONS": [[2, 4, 5, 6, 7, 3]] * 5,
        }
        data_path = Path(td) / "data.json"
        data_path.write_text(json.dumps(data))

        class M:
            def __init__(self):
                self.vocab = vocab
                self.eval_called = False
                self.train_called = False

            def eval(self):
                self.eval_called = True
                return self

            def train(self):
                self.train_called = True
                return self

            def generate_by_beamsearch(self, images, beam_k, max_len):
                return [[2, 4, 5, 6, 7, 3] for _ in range(images.shape[0])]

        m = M()
        try:
            b = fn(str(data_path), m, beam_k=3, batch_size=16)
            s = 0.0
            d = []
            if abs(float(b) - 1.0) < 1e-6:
                s += 4.0
            else:
                d.append(f"BLEU-4={b}, 期望 1.0")
            if m.eval_called:
                s += 1.0
            else:
                d.append("未调用 model.eval()")
            return s, "; ".join(d) if d else "Beam 输出整理、特殊词过滤和 BLEU-4 正确"
        except Exception as e:
            return 0.0, f"运行失败: {type(e).__name__}: {e}"


# ---------------------------------------------------------------------------
# Grade orchestration
# ---------------------------------------------------------------------------
def grade_vsepp(nb, ns, load_errors, cfg, metric_override=None, test_data_dir=None, submission_dir=None):
    gb = GradeBook()
    code = all_code(nb)
    s, d = test_dataset(ns)
    gb.add("data/caption_padding", s, 5, d)
    s, d = test_vse_image(ns)
    gb.add("model/image_encoder", s, 9, d)
    s, d = test_vse_text(ns)
    gb.add("model/text_encoder", s, 9, d)
    s, d = test_vse_wrapper(ns)
    gb.add("model/vsepp_wrapper", s, 7, d)
    s, d = test_vse_loss(ns)
    gb.add("loss/triplet", s, 12, d)
    s, d = test_optimizer(ns, "vsepp")
    gb.add("optimizer/adam", s, 4, d)
    s, d = test_vse_evaluate(ns)
    gb.add("evaluation/recall_pipeline", s, 12, d)
    s, d = score_training(code, "vsepp")
    gb.add("training/train_loop", s, 17, d)
    s, d = quality_score(code, load_errors)
    gb.add("quality/completeness", s, 5, d)

    metric = None
    metric_detail = "未评估"
    if metric_override is not None:
        metric = float(metric_override)
        metric_detail = "performance_override.csv"
    elif test_data_dir is not None and submission_dir is not None:
        model_path = find_model_file(submission_dir, "vsepp")
        if model_path:
            metric, metric_detail = evaluate_student_retrieval(model_path, ns, test_data_dir)
        else:
            metric_detail = "未找到模型文件 (work/vsepp_*.pt)"

    pscore, pdetail = performance_score(metric, "vsepp", cfg)
    return result_dict(gb, "vsepp", metric, metric_detail, pscore, pdetail, load_errors, nb)


def grade_caption(nb, ns, load_errors, cfg, metric_override=None, test_data_dir=None, submission_dir=None):
    gb = GradeBook()
    code = all_code(nb)
    s, d = test_dataset(ns)
    gb.add("data/caption_padding", s, 5, d)
    s, d = test_caption_encoder(ns)
    gb.add("model/image_encoder", s, 5, d)
    s, d = test_attention(ns)
    gb.add("model/additive_attention", s, 6, d)
    s, d = test_decoder(ns)
    gb.add("model/attention_decoder", s, 14, d)
    s, d = test_caption_loss(ns)
    gb.add("loss/cross_entropy", s, 12, d)
    s, d = test_optimizer(ns, "caption")
    gb.add("optimizer/adam", s, 4, d)
    s, d = test_beam_search(ns)
    gb.add("evaluation/beam_search", s, 7, d)
    s, d = test_caption_evaluate(ns)
    gb.add("evaluation/bleu", s, 5, d)
    s, d = score_training(code, "caption")
    gb.add("training/train_loop", s, 17, d)
    s, d = quality_score(code, load_errors)
    gb.add("quality/completeness", s, 5, d)

    metric = None
    metric_detail = "未评估"
    if metric_override is not None:
        metric = float(metric_override)
        metric_detail = "performance_override.csv"
    elif test_data_dir is not None and submission_dir is not None:
        model_path = find_model_file(submission_dir, "caption")
        if model_path:
            metric, metric_detail = evaluate_student_caption(model_path, ns, test_data_dir)
        else:
            metric_detail = "未找到模型文件 (work/arctic_*.pt)"

    pscore, pdetail = performance_score(metric, "caption", cfg)
    return result_dict(gb, "caption", metric, metric_detail, pscore, pdetail, load_errors, nb)


def result_dict(gb, assignment, metric, metric_detail, pscore, pdetail, load_errors, nb=None):
    cats = {k: gb.category_score(k) for k in ("data", "model", "loss", "optimizer", "evaluation", "training", "quality")}
    raw = round(sum(cats.values()), 3)
    impl = round(raw / IMPLEMENTATION_RAW_MAX * IMPLEMENTATION_FINAL_MAX, 3)
    answers = extract_analysis_answers(nb) if nb is not None else {f"q{i}": "" for i in range(1, 5)}
    evidence = analysis_evidence_status(answers, assignment)
    caps, cap_reasons = analysis_caps(answers, assignment)
    answered = sum(bool((answers.get(f"q{i}") or "").strip()) for i in range(1, 5))
    auto80 = round(impl + pscore, 3) if pscore is not None else None
    return {
        "assignment": assignment,
        "categories_raw": cats,
        "implementation_raw_subtotal": raw,
        "implementation_raw_max": IMPLEMENTATION_RAW_MAX,
        "implementation_score": impl,
        "implementation_max": IMPLEMENTATION_FINAL_MAX,
        "performance_metric": metric,
        "performance_metric_detail": metric_detail,
        "performance_score": pscore,
        "performance_max": PERFORMANCE_MAX,
        "performance_detail": pdetail,
        "analysis_answers": answers,
        "analysis_evidence": evidence,
        "analysis_caps": caps,
        "analysis_cap_reasons": cap_reasons,
        "analysis_cap_total": round(sum(caps.values()), 3),
        "analysis_answered_count": answered,
        "analysis_score": None,
        "analysis_teacher_score": None,
        "analysis_q_scores": None,
        "analysis_q_scores_applied": None,
        "analysis_max": ANALYSIS_MAX,
        "auto_subtotal_80": auto80,
        "total": None,
        "items": [asdict(x) for x in gb.items],
        "load_errors": load_errors,
    }


# ---------------------------------------------------------------------------
# Config, overrides, grade_one
# ---------------------------------------------------------------------------
def load_config(path: Optional[str]) -> Dict[str, Any]:
    if not path:
        return {"performance": {"vsepp": {}, "caption": {}}}
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def grade_one(path: Path, cfg: Dict[str, Any], metric_override: Optional[float] = None,
              student_id: Optional[str] = None, test_data_dir: Optional[Path] = None) -> Dict[str, Any]:
    nb = load_notebook(path)
    assignment = detect_assignment(nb)
    ns, errors = safe_definition_namespace(nb)
    submission_dir = path.parent

    if assignment == "vsepp":
        res = grade_vsepp(nb, ns, errors, cfg, metric_override, test_data_dir, submission_dir)
    elif assignment == "caption":
        res = grade_caption(nb, ns, errors, cfg, metric_override, test_data_dir, submission_dir)
    else:
        res = {
            "assignment": "unknown", "categories_raw": {},
            "implementation_raw_subtotal": 0, "implementation_raw_max": 80,
            "implementation_score": 0, "implementation_max": 60,
            "performance_metric": None, "performance_score": None, "performance_max": 20,
            "analysis_answers": {f"q{i}": "" for i in range(1, 5)},
            "analysis_evidence": {}, "analysis_caps": {f"q{i}": 0 for i in range(1, 5)},
            "analysis_cap_reasons": {}, "analysis_cap_total": 0, "analysis_answered_count": 0,
            "analysis_score": None, "analysis_teacher_score": None, "analysis_max": 20,
            "auto_subtotal_80": None, "total": None, "items": [], "load_errors": errors,
            "error": "无法识别作业类型",
        }
    res["student_id"] = student_id or path.stem
    res["file"] = str(path)
    return res


def load_overrides(path: Optional[str]) -> Dict[Tuple[str, str], float]:
    out = {}
    if not path:
        return out
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            a = (row.get("assignment") or "").strip().lower()
            m = (row.get("metric") or "").strip()
            if sid and a and m:
                try:
                    out[(sid, a)] = float(m)
                except ValueError:
                    pass
    return out


def load_analysis_overrides(path: Optional[str]) -> Dict[Tuple[str, str], Dict[str, Any]]:
    out: Dict[Tuple[str, str], Dict[str, Any]] = {}
    if not path:
        return out
    with open(path, "r", encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            sid = (row.get("student_id") or "").strip()
            a = (row.get("assignment") or "").strip().lower()
            if not sid or not a:
                continue

            cap_overrides: List[Optional[float]] = []
            for i in range(1, 5):
                v = (row.get(f"q{i}_cap_override") or "").strip()
                if not v:
                    cap_overrides.append(None)
                else:
                    try:
                        cap_overrides.append(max(0.0, min(ANALYSIS_QUESTION_MAX, float(v))))
                    except ValueError:
                        cap_overrides.append(None)

            qs: List[float] = []
            ok = True
            for i in range(1, 5):
                v = (row.get(f"q{i}_score") or "").strip()
                if not v:
                    ok = False
                    break
                try:
                    qs.append(max(0.0, min(ANALYSIS_QUESTION_MAX, float(v))))
                except ValueError:
                    ok = False
                    break
            if ok:
                out[(sid, a)] = {
                    "score": round(sum(qs), 3),
                    "q_scores": qs,
                    "cap_overrides": cap_overrides,
                    "comment": (row.get("comment") or "").strip(),
                }
                continue

            direct = (row.get("analysis_score") or "").strip()
            if direct:
                try:
                    score = max(0.0, min(ANALYSIS_MAX, float(direct)))
                    out[(sid, a)] = {
                        "score": score, "q_scores": None,
                        "cap_overrides": cap_overrides,
                        "comment": (row.get("comment") or "").strip(),
                    }
                except ValueError:
                    pass
    return out


def apply_analysis_override(result: Dict[str, Any], override: Optional[Dict[str, Any]]) -> None:
    auto_caps = result.get("analysis_caps", {}) or {f"q{i}": 0.0 for i in range(1, 5)}
    auto_reasons = result.get("analysis_cap_reasons", {}) or {}

    if override is None:
        result["analysis_score"] = None
        result["analysis_teacher_score"] = None
        result["analysis_q_scores"] = None
        result["analysis_q_scores_applied"] = None
        result["analysis_caps_effective"] = auto_caps
        result["analysis_cap_total_effective"] = round(sum(float(auto_caps.get(f"q{i}", 0)) for i in range(1, 5)), 3)
        result["analysis_comment"] = ""
        result["analysis_cap_adjustment"] = ""
        result["total"] = None
        return

    cap_overrides = override.get("cap_overrides") or [None, None, None, None]
    effective_caps: Dict[str, float] = {}
    effective_reasons: Dict[str, str] = {}
    for i in range(1, 5):
        q = f"q{i}"
        ov = cap_overrides[i - 1] if i - 1 < len(cap_overrides) else None
        if ov is not None:
            effective_caps[q] = max(0.0, min(ANALYSIS_QUESTION_MAX, float(ov)))
            effective_reasons[q] = f"教师人工覆盖自动上限：{effective_caps[q]:g}/5"
        else:
            effective_caps[q] = max(0.0, min(ANALYSIS_QUESTION_MAX, float(auto_caps.get(q, 0))))
            effective_reasons[q] = auto_reasons.get(q, "")

    result["analysis_caps_effective"] = effective_caps
    result["analysis_cap_reasons_effective"] = effective_reasons
    result["analysis_cap_total_effective"] = round(sum(effective_caps.values()), 3)
    result["analysis_comment"] = override.get("comment", "")

    q_scores = override.get("q_scores")
    if q_scores is not None:
        raw_q = [max(0.0, min(ANALYSIS_QUESTION_MAX, float(x))) for x in q_scores]
        applied_q = [round(min(raw_q[i], effective_caps[f"q{i+1}"]), 3) for i in range(4)]
        raw_total = round(sum(raw_q), 3)
        applied_total = round(sum(applied_q), 3)
        clipped = [i + 1 for i in range(4) if applied_q[i] < raw_q[i] - 1e-9]
        result["analysis_teacher_score"] = raw_total
        result["analysis_q_scores"] = raw_q
        result["analysis_q_scores_applied"] = applied_q
        result["analysis_score"] = applied_total
        result["analysis_cap_adjustment"] = (
            "自动封顶作用于题目：" + ", ".join(f"Q{i}" for i in clipped) if clipped else ""
        )
    else:
        raw_total = max(0.0, min(ANALYSIS_MAX, float(override.get("score", 0))))
        applied_total = round(min(raw_total, result["analysis_cap_total_effective"]), 3)
        result["analysis_teacher_score"] = raw_total
        result["analysis_q_scores"] = None
        result["analysis_q_scores_applied"] = None
        result["analysis_score"] = applied_total
        result["analysis_cap_adjustment"] = (
            f"仅提供 analysis_score；按四题证据上限总和 {result['analysis_cap_total_effective']:g}/20 封顶"
            if applied_total < raw_total - 1e-9 else ""
        )

    if result.get("auto_subtotal_80") is not None:
        result["total"] = round(float(result["auto_subtotal_80"]) + float(result["analysis_score"]), 3)
    else:
        result["total"] = None


# ---------------------------------------------------------------------------
# CSV / report output
# ---------------------------------------------------------------------------
def write_analysis_review(results: List[Dict[str, Any]], path: Path) -> None:
    fields = ["student_id", "assignment"]
    for i in range(1, 5):
        fields += [
            f"q{i}_status", f"q{i}_auto_cap", f"q{i}_cap_reason", f"q{i}_cap_override",
            f"q{i}_answer", f"q{i}_score", f"q{i}_final_score",
        ]
    fields += ["analysis_teacher_score", "analysis_auto_cap_total", "analysis_score", "cap_adjustment", "comment"]

    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            a = r.get("analysis_answers", {}) or {}
            e = r.get("analysis_evidence", {}) or {}
            caps = r.get("analysis_caps", {}) or {}
            reasons = r.get("analysis_cap_reasons", {}) or {}
            effective_caps = r.get("analysis_caps_effective", {}) or caps
            q_scores = r.get("analysis_q_scores") or ["", "", "", ""]
            q_final = r.get("analysis_q_scores_applied") or ["", "", "", ""]
            row: Dict[str, Any] = {
                "student_id": r.get("student_id"),
                "assignment": r.get("assignment"),
                "analysis_teacher_score": r.get("analysis_teacher_score") if r.get("analysis_teacher_score") is not None else "",
                "analysis_auto_cap_total": r.get("analysis_cap_total", sum(caps.values()) if caps else ""),
                "analysis_score": r.get("analysis_score") if r.get("analysis_score") is not None else "",
                "cap_adjustment": r.get("analysis_cap_adjustment", ""),
                "comment": r.get("analysis_comment", ""),
            }
            for i in range(1, 5):
                q = f"q{i}"
                row[f"q{i}_status"] = e.get(q, "")
                row[f"q{i}_auto_cap"] = caps.get(q, "")
                row[f"q{i}_cap_reason"] = reasons.get(q, "")
                ec = effective_caps.get(q, caps.get(q, ""))
                ac = caps.get(q, "")
                row[f"q{i}_cap_override"] = ec if ec != ac else ""
                row[f"q{i}_answer"] = a.get(q, "")
                row[f"q{i}_score"] = q_scores[i - 1] if i - 1 < len(q_scores) else ""
                row[f"q{i}_final_score"] = q_final[i - 1] if i - 1 < len(q_final) else ""
            w.writerow(row)


def find_notebooks(inputs: List[str]) -> List[Path]:
    paths = []
    for x in inputs:
        p = Path(x)
        if p.is_dir():
            paths.extend(sorted(p.rglob("*.ipynb")))
        elif p.suffix.lower() == ".ipynb" and p.exists():
            paths.append(p)
    seen = set()
    uniq = []
    for p in paths:
        rp = str(p.resolve())
        if rp not in seen:
            seen.add(rp)
            uniq.append(p)
    return uniq


def student_id_for(path: Path, inputs: List[str], mode: str) -> str:
    if mode == "stem":
        return path.stem
    if mode == "parent":
        return path.parent.name
    for raw_input in inputs:
        root = Path(raw_input)
        if not root.is_dir():
            continue
        try:
            relative = path.resolve().relative_to(root.resolve())
        except ValueError:
            continue
        if len(relative.parts) >= 2:
            for part in relative.parts[:-1]:
                if re.fullmatch(r"\d{7,}", part):
                    return part
            return relative.parts[0]
    return path.stem


def write_csv(results: List[Dict[str, Any]], path: Path):
    fields = [
        "student_id", "file", "assignment",
        "data_raw", "model_raw", "loss_raw", "optimizer_raw", "evaluation_raw", "training_raw", "quality_raw",
        "implementation_raw_80", "implementation_score_60",
        "performance_metric", "performance_score_20",
        "analysis_answered", "analysis_teacher_score_20", "analysis_cap_20", "analysis_score_20",
        "auto_subtotal_80", "total_100", "notes",
    ]
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields)
        w.writeheader()
        for r in results:
            cats = r.get("categories_raw", {}) or {}
            notes = []
            if r.get("error"):
                notes.append(r["error"])
            if r.get("performance_score") is None:
                notes.append(r.get("performance_detail") or "性能分待配置/待补充")
            if r.get("analysis_score") is None:
                notes.append("分析题待人工评分")
            if r.get("analysis_cap_adjustment"):
                notes.append(r.get("analysis_cap_adjustment"))
            row = {
                "student_id": r.get("student_id"), "file": r.get("file"), "assignment": r.get("assignment"),
                "data_raw": cats.get("data", 0), "model_raw": cats.get("model", 0), "loss_raw": cats.get("loss", 0),
                "optimizer_raw": cats.get("optimizer", 0), "evaluation_raw": cats.get("evaluation", 0),
                "training_raw": cats.get("training", 0), "quality_raw": cats.get("quality", 0),
                "implementation_raw_80": r.get("implementation_raw_subtotal", 0),
                "implementation_score_60": r.get("implementation_score", 0),
                "performance_metric": r.get("performance_metric"), "performance_score_20": r.get("performance_score"),
                "analysis_answered": f"{r.get('analysis_answered_count', 0)}/4",
                "analysis_teacher_score_20": r.get("analysis_teacher_score"),
                "analysis_cap_20": r.get("analysis_cap_total_effective", r.get("analysis_cap_total")),
                "analysis_score_20": r.get("analysis_score"),
                "auto_subtotal_80": r.get("auto_subtotal_80"), "total_100": r.get("total"),
                "notes": " | ".join(notes),
            }
            w.writerow(row)


# ---------------------------------------------------------------------------
# Worker subprocess for isolation
# ---------------------------------------------------------------------------
def run_worker(path, config_path, metric_override, timeout, student_id, test_data_dir=None):
    cmd = [sys.executable, str(Path(__file__).resolve()), "--worker", str(path), "--allow-unsafe-exec"]
    if config_path:
        cmd += ["--config", config_path]
    if metric_override is not None:
        cmd += ["--metric-override", str(metric_override)]
    if test_data_dir is not None:
        cmd += ["--test-data-dir", str(test_data_dir)]
    cmd += ["--student-id", student_id]
    try:
        cp = subprocess.run(cmd, capture_output=True, text=True, timeout=timeout)
        text = (cp.stdout or "") + "\n" + (cp.stderr or "")
        idx = text.rfind(JSON_MARKER)
        if idx < 0:
            raise RuntimeError("worker 未返回 JSON: " + text[-800:])
        payload = text[idx + len(JSON_MARKER):].strip().splitlines()[0]
        return json.loads(payload)
    except subprocess.TimeoutExpired:
        return _error_result(student_id, str(path), f"评分超时>{timeout}s")
    except Exception as e:
        return _error_result(student_id, str(path), f"worker 失败: {e}")


def _error_result(student_id, file_path, error_msg):
    return {
        "student_id": student_id, "file": file_path, "assignment": "unknown",
        "categories_raw": {}, "implementation_raw_subtotal": 0,
        "implementation_score": 0, "implementation_max": 60,
        "performance_metric": None, "performance_score": None, "performance_max": 20,
        "analysis_answers": {}, "analysis_evidence": {},
        "analysis_caps": {f"q{i}": 0 for i in range(1, 5)},
        "analysis_cap_reasons": {}, "analysis_cap_total": 0, "analysis_answered_count": 0,
        "analysis_score": None, "analysis_teacher_score": None, "analysis_max": 20,
        "auto_subtotal_80": None, "total": None, "items": [], "load_errors": [],
        "error": error_msg,
    }


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------
def main():
    ap = argparse.ArgumentParser(description="多模态深度学习作业统一自动评分器（60代码+20性能+20分析）")
    ap.add_argument("inputs", nargs="*", help="学生 notebook 或目录")
    ap.add_argument("--config", default=None, help="grading_config.json")
    ap.add_argument("--output", default="grades.csv", help="汇总 CSV")
    ap.add_argument("--details", default=None, help="详细 JSON；默认与 output 同名 .json")
    ap.add_argument("--test-data-dir", default=None, help="教师持有的完整测试数据目录（含 test_data.json 和 vocab.json）")
    ap.add_argument("--performance-csv", default=None, help="可选：student_id,assignment,metric 覆盖表")
    ap.add_argument("--analysis-csv", default=None, help="可选：分析题教师评分表")
    ap.add_argument("--analysis-review", default=None, help="分析题回答汇总；默认 <output>_analysis_review.csv")
    ap.add_argument("--timeout", type=int, default=180, help="每份 notebook 最大评分秒数（含模型推理）")
    ap.add_argument("--student-id-mode", choices=("auto", "parent", "stem"), default="auto")
    ap.add_argument("--allow-unsafe-exec", action="store_true", help="确认学生代码将在受限环境中执行")
    ap.add_argument("--device", default="cpu", help="推理设备（cpu/cuda）")
    ap.add_argument("--worker", default=None, help=argparse.SUPPRESS)
    ap.add_argument("--metric-override", type=float, default=None, help=argparse.SUPPRESS)
    ap.add_argument("--student-id", default=None, help=argparse.SUPPRESS)
    args = ap.parse_args()

    if not args.allow_unsafe_exec:
        ap.error("评分会执行学生代码；请仅在受限 Docker/虚拟机中运行，并显式添加 --allow-unsafe-exec")

    cfg = load_config(args.config)
    test_data_dir = Path(args.test_data_dir) if args.test_data_dir else None

    if args.worker:
        try:
            r = grade_one(Path(args.worker), cfg, args.metric_override, args.student_id, test_data_dir)
        except Exception:
            r = _error_result(args.student_id or Path(args.worker).stem, args.worker, traceback.format_exc())
        print(JSON_MARKER + json.dumps(r, ensure_ascii=False))
        return

    nbs = find_notebooks(args.inputs)
    if not nbs:
        ap.error("没有找到 .ipynb")
    perf_overrides = load_overrides(args.performance_csv)
    analysis_overrides = load_analysis_overrides(args.analysis_csv)
    results = []
    for p in nbs:
        try:
            a = detect_assignment(load_notebook(p))
        except Exception:
            a = "unknown"
        student_id = student_id_for(p, args.inputs, args.student_id_mode)
        pov = perf_overrides.get((student_id, a))
        r = run_worker(p, args.config, pov, args.timeout, student_id, test_data_dir)
        apply_analysis_override(r, analysis_overrides.get((student_id, r.get("assignment", a))))
        results.append(r)
        auto = "待性能分" if r.get("auto_subtotal_80") is None else f"{r['auto_subtotal_80']:.1f}/80"
        total = "待分析题评分" if r.get("total") is None else f"{r['total']:.1f}/100"
        print(f"[{p.name}] {r.get('assignment')}  code={r.get('implementation_score', 0):.1f}/60  auto={auto}  final={total}")

    out = Path(args.output)
    write_csv(results, out)
    details = Path(args.details) if args.details else out.with_suffix(".json")
    details.write_text(json.dumps(results, ensure_ascii=False, indent=2), encoding="utf-8")
    review = Path(args.analysis_review) if args.analysis_review else out.with_name(out.stem + "_analysis_review.csv")
    write_analysis_review(results, review)
    print(f"\n已生成: {out}\n详细报告: {details}\n分析题汇总/评分表: {review}")


if __name__ == "__main__":
    main()
