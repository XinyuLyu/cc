# Multimodal Homework Autograder

自动评测学生提交的 Image Captioning (ARCTIC) 和 Visual Semantic Embedding (VSE++) 作业。

## 评分结构

| 模块 | 满分 | 说明 |
|------|------|------|
| Implementation | 60 | 80 分原始分 × 0.75 归一化 |
| Performance | 20 | 加载学生模型权重，在测试集上推理 |
| Analysis | 20 | 4 题 × 5 分，自动提取证据上限 |
| **Total** | **100** | |

### Performance 评分公式

```
score = 20 × (metric/reference − zero_ratio) / (full_ratio − zero_ratio)
```

- `zero_ratio = 0.5` → metric 达到参考值 50% 时开始得分
- `full_ratio = 0.95` → metric 达到参考值 95% 时满分

若无参考值 (`reference_metric: null`)，则 metric 直接作为比率使用。

## 文件说明

| 文件 | 用途 |
|------|------|
| `model_homework_autograder.py` | 主评测脚本 |
| `grading_config.json` | 评分配置（权重、阈值） |
| `performance_override.csv` | 手动覆盖学生 performance 指标（可选） |
| `analysis_scores_template.csv` | 教师手动评分分析题模板（可选） |
| `requirements.txt` | Python 依赖 |

## 使用方法

### 1. 准备测试数据

将完整的测试集数据放在一个目录中，需包含：
- `dataset_flickr8k.json` — 完整的数据集标注（含测试集 captions）
- `Images/` — Flickr8k 图片目录

### 2. 评测单个学生

```bash
python model_homework_autograder.py \
    path/to/student/notebook.ipynb \
    --test-data-dir path/to/test_data/ \
    --output grades.csv
```

### 3. 批量评测

```bash
python model_homework_autograder.py \
    submissions/ \
    --test-data-dir path/to/test_data/ \
    --output grades.csv \
    --analysis-csv analysis_scores.csv \
    --timeout 300
```

脚本会自动：
1. 遍历 `submissions/` 下所有 `.ipynb` 文件
2. 检测作业类型（caption / vsepp）
3. 运行实现测试（unit tests）
4. 加载学生模型权重进行推理
5. 提取分析题回答并计算证据上限
6. 生成成绩 CSV 和分析题回顾 CSV

### 4. 可选覆盖

**Performance 覆盖**（当自动推理失败时手动填入指标）：

```csv
student_id,assignment,metric
student001,caption,0.182
student002,vsepp,312.5
```

```bash
python model_homework_autograder.py submissions/ \
    --test-data-dir path/to/test_data/ \
    --performance-csv performance_override.csv \
    --output grades.csv
```

**Analysis 评分覆盖**（教师手动评分后导入）：

```csv
student_id,assignment,score,comment,q1_cap_override,q2_cap_override,q3_cap_override,q4_cap_override
student001,caption,18,good analysis,5,5,4,4
```

## CLI 参数

| 参数 | 默认值 | 说明 |
|------|--------|------|
| `path` | (必需) | 单个 .ipynb 或包含 .ipynb 的目录 |
| `--config` | `grading_config.json` | 评分配置文件 |
| `--test-data-dir` | (无) | 教师测试数据目录 |
| `--output` | `grades.csv` | 输出成绩 CSV |
| `--performance-csv` | (无) | Performance 指标覆盖表 |
| `--analysis-csv` | (无) | 分析题教师评分表 |
| `--analysis-review` | (自动) | 分析题回答汇总 CSV |
| `--timeout` | 180 | 单个学生评测超时（秒） |
| `--device` | `cpu` | 模型推理设备 |
| `--jobs` | 1 | 并行评测进程数 |
