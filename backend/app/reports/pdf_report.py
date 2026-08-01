from __future__ import annotations

from datetime import date
from html import escape
from io import BytesIO
import math
from pathlib import Path
from typing import Any

from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet
from reportlab.lib.units import mm
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont
from reportlab.platypus import (
    BaseDocTemplate,
    Flowable,
    Frame,
    KeepTogether,
    NextPageTemplate,
    PageBreak,
    PageTemplate,
    Paragraph,
    Spacer,
    Table,
    TableStyle,
)

from ..indicators import format_indicator_value, indicator_name
from ..ai.report_builder import report_title
from ..ai.schemas import AnalysisInsights, PDFReportRequest


PAGE_WIDTH, PAGE_HEIGHT = A4
BLUE = colors.HexColor("#3B82F6")
BLUE_DARK = colors.HexColor("#1D4ED8")
BLUE_LIGHT = colors.HexColor("#DBEAFE")
MINT = colors.HexColor("#34D399")
INK = colors.HexColor("#0F172A")
MUTED = colors.HexColor("#64748B")
BORDER = colors.HexColor("#E5E7EB")
PAPER = colors.HexColor("#F8FAFC")
FONT_DIR = Path(__file__).resolve().parent / "fonts"
CHINESE_FONT_PATH = FONT_DIR / "NotoSansCJKsc-VF.ttf"


def build_pdf_report(
    context: dict[str, Any],
    request: PDFReportRequest,
    generated_on: date | None = None,
) -> bytes:
    generated_on = generated_on or date.today()
    font = _font_for_locale(request.locale)
    styles = _styles(font)
    output = BytesIO()
    document = BaseDocTemplate(
        output,
        pagesize=A4,
        leftMargin=18 * mm,
        rightMargin=18 * mm,
        topMargin=19 * mm,
        bottomMargin=18 * mm,
        title=report_title(request.locale, request.ai_insights_applied),
        author="UrbanInsight AI",
    )
    frame = Frame(
        document.leftMargin,
        document.bottomMargin,
        document.width,
        document.height,
        id="content",
    )
    document.addPageTemplates(
        [
            PageTemplate(id="cover", frames=[frame], onPage=_cover_page),
            PageTemplate(
                id="content",
                frames=[frame],
                onPage=lambda canvas, doc: _content_page(
                    canvas,
                    doc,
                    context["borough"]["name"],
                    generated_on,
                    font,
                ),
            ),
        ]
    )
    story = _cover_story(context, request, generated_on, styles)
    story.extend([NextPageTemplate("content"), PageBreak()])
    story.extend(_report_story(context, request, generated_on, styles, font))
    document.build(story)
    return output.getvalue()


def _font_for_locale(locale: str) -> str:
    if locale != "zh-CN":
        return "Helvetica"
    font_name = "NotoSansCJKsc"
    if font_name not in pdfmetrics.getRegisteredFontNames():
        pdfmetrics.registerFont(TTFont(font_name, CHINESE_FONT_PATH))
    return font_name


def _styles(font: str) -> dict[str, ParagraphStyle]:
    sample = getSampleStyleSheet()
    return {
        "cover_brand": ParagraphStyle(
            "cover_brand", parent=sample["Heading1"], fontName=font,
            fontSize=18, leading=22, textColor=BLUE_DARK, alignment=TA_CENTER,
        ),
        "cover_title": ParagraphStyle(
            "cover_title", parent=sample["Title"], fontName=font,
            fontSize=25, leading=34, textColor=INK, alignment=TA_CENTER,
        ),
        "cover_meta": ParagraphStyle(
            "cover_meta", parent=sample["BodyText"], fontName=font,
            fontSize=10, leading=17, textColor=MUTED, alignment=TA_CENTER,
        ),
        "h1": ParagraphStyle(
            "h1", parent=sample["Heading1"], fontName=font,
            fontSize=18, leading=23, textColor=INK, spaceBefore=3 * mm,
            spaceAfter=4 * mm, keepWithNext=True,
        ),
        "h2": ParagraphStyle(
            "h2", parent=sample["Heading2"], fontName=font,
            fontSize=13, leading=18, textColor=BLUE_DARK,
            spaceBefore=5 * mm, spaceAfter=2.5 * mm, keepWithNext=True,
        ),
        "body": ParagraphStyle(
            "body", parent=sample["BodyText"], fontName=font,
            fontSize=9.5, leading=15, textColor=INK, spaceAfter=2.5 * mm,
            splitLongWords=True,
        ),
        "small": ParagraphStyle(
            "small", parent=sample["BodyText"], fontName=font,
            fontSize=8, leading=12, textColor=MUTED,
        ),
        "metric": ParagraphStyle(
            "metric", parent=sample["Heading2"], fontName=font,
            fontSize=19, leading=23, textColor=BLUE_DARK, alignment=TA_CENTER,
        ),
        "metric_label": ParagraphStyle(
            "metric_label", parent=sample["BodyText"], fontName=font,
            fontSize=8, leading=11, textColor=MUTED, alignment=TA_CENTER,
        ),
        "card_title": ParagraphStyle(
            "card_title", parent=sample["Heading3"], fontName=font,
            fontSize=10, leading=14, textColor=INK, spaceAfter=1 * mm,
        ),
        "card_body": ParagraphStyle(
            "card_body", parent=sample["BodyText"], fontName=font,
            fontSize=8.5, leading=13, textColor=MUTED,
        ),
    }


def _cover_story(
    context: dict[str, Any],
    request: PDFReportRequest,
    generated_on: date,
    styles: dict[str, ParagraphStyle],
) -> list[Flowable]:
    locale = request.locale
    title = escape(report_title(locale, request.ai_insights_applied))
    mode = _label(locale, "AI deep analysis", "AI 深度分析") if request.ai_insights_applied else _label(locale, "Basic analysis", "基础分析")
    metadata = [
        f"{_label(locale, 'Borough', '行政区')}: {escape(context['borough']['name'])}",
        f"{_label(locale, 'Generated', '生成日期')}: {generated_on.isoformat()}",
        f"{_label(locale, 'Analysis mode', '分析模式')}: {mode}",
    ]
    if request.ai_insights_applied and request.ai_provider:
        provider = "Qwen" if request.ai_provider == "qwen" else request.ai_provider.title()
        metadata.append(f"AI Provider: {provider}")
        if request.ai_model:
            metadata.append(f"{_label(locale, 'Model', '模型')}: {escape(request.ai_model)}")
    return [
        Spacer(1, 43 * mm),
        Paragraph("UrbanInsight AI", styles["cover_brand"]),
        Spacer(1, 18 * mm),
        Paragraph(title, styles["cover_title"]),
        Spacer(1, 8 * mm),
        Paragraph("<br/>".join(metadata), styles["cover_meta"]),
        Spacer(1, 27 * mm),
        Paragraph(
            _label(
                locale,
                "Urban decision intelligence for evidence-led regional evaluation",
                "面向循证区域评价的城市决策智能",
            ),
            styles["cover_meta"],
        ),
    ]


def _report_story(
    context: dict[str, Any],
    request: PDFReportRequest,
    generated_on: date,
    styles: dict[str, ParagraphStyle],
    font: str,
) -> list[Flowable]:
    locale = request.locale
    scores = context["scores"]
    engine = context["analysis_engine"]
    insights = request.insights
    dimensions = [
        (_label(locale, "Economic", "经济"), float(scores["economic"])),
        (_label(locale, "Social", "社会"), float(scores["social"])),
        (_label(locale, "Ecological", "生态"), float(scores["ecological"])),
    ]
    contributions = [
        (_dimension_label(locale, name), float(value))
        for name, value in engine["dimension_contributions"].items()
    ]
    return [
        Paragraph(_label(locale, "Executive Summary", "执行摘要"), styles["h1"]),
        _metric_table(scores, locale, styles),
        Spacer(1, 4 * mm),
        Paragraph(escape(insights.executive_summary), styles["body"]),
        Paragraph(escape(insights.ranking_explanation), styles["body"]),
        _highlight_table(insights, locale, styles),
        Paragraph(_label(locale, "Overall Evaluation", "综合评价"), styles["h1"]),
        Paragraph(
            _label(
                locale,
                "The score and London rank are persisted PCA-weighted TOPSIS results from the Analysis Engine. This report does not recalculate them.",
                "综合得分与伦敦排名来自分析引擎已存储的 PCA 加权 TOPSIS 结果，本报告不会重新计算。",
            ),
            styles["body"],
        ),
        ContributionChart(contributions, font),
        PageBreak(),
        Paragraph(_label(locale, "Dimension Performance", "维度表现"), styles["h1"]),
        RadarChart(dimensions, font),
        _dimension_table(dimensions, locale, styles),
        Paragraph(_label(locale, "Key Indicators", "关键指标"), styles["h1"]),
        _indicator_table(context["indicators"], locale, styles),
        Paragraph(_label(locale, "Analysis Interpretation", "分析解读"), styles["h1"]),
        Paragraph(escape(insights.indicator_interpretation), styles["body"]),
        _insight_grid(insights, locale, styles),
        Paragraph(_label(locale, "Action Recommendations", "行动建议"), styles["h1"]),
        _recommendation_table(insights, locale, styles),
        Paragraph(_label(locale, "Method and Disclaimer", "方法与免责声明"), styles["h1"]),
        Paragraph(_method_text(locale, request, generated_on), styles["body"]),
    ]


class RadarChart(Flowable):
    def __init__(self, values: list[tuple[str, float]], font: str) -> None:
        super().__init__()
        self.values = values
        self.font = font
        self.width = 160 * mm
        self.height = 76 * mm

    def draw(self) -> None:
        center_x, center_y, radius = self.width / 2, self.height / 2 - 2 * mm, 27 * mm
        angles = [math.radians(90 + index * 120) for index in range(3)]
        for scale in (0.25, 0.5, 0.75, 1):
            points = [(center_x + radius * scale * math.cos(a), center_y + radius * scale * math.sin(a)) for a in angles]
            self.canv.setStrokeColor(BORDER)
            _draw_polygon(self.canv, points, False)
        for angle in angles:
            self.canv.line(center_x, center_y, center_x + radius * math.cos(angle), center_y + radius * math.sin(angle))
        points = [
            (center_x + radius * max(0, min(score, 100)) / 100 * math.cos(angle),
             center_y + radius * max(0, min(score, 100)) / 100 * math.sin(angle))
            for (_, score), angle in zip(self.values, angles)
        ]
        self.canv.setFillColor(colors.Color(BLUE.red, BLUE.green, BLUE.blue, alpha=0.2))
        self.canv.setStrokeColor(BLUE)
        self.canv.setLineWidth(2)
        _draw_polygon(self.canv, points, True)
        self.canv.setFont(self.font, 8.5)
        self.canv.setFillColor(INK)
        for (label, score), angle in zip(self.values, angles):
            x = center_x + (radius + 10 * mm) * math.cos(angle)
            y = center_y + (radius + 8 * mm) * math.sin(angle)
            self.canv.drawCentredString(x, y, f"{label} {score:.1f}")


class ContributionChart(Flowable):
    def __init__(self, values: list[tuple[str, float]], font: str) -> None:
        super().__init__()
        self.values = values
        self.font = font
        self.width = 160 * mm
        self.height = 45 * mm

    def draw(self) -> None:
        label_width = 31 * mm
        bar_width = self.width - label_width - 15 * mm
        maximum = max([value for _, value in self.values] + [1])
        self.canv.setFont(self.font, 8.5)
        for index, (label, value) in enumerate(self.values):
            y = self.height - (index + 1) * 12 * mm
            self.canv.setFillColor(INK)
            self.canv.drawString(0, y + 2.5 * mm, label)
            self.canv.setFillColor(BLUE_LIGHT)
            self.canv.roundRect(label_width, y, bar_width, 7 * mm, 3.5 * mm, fill=1, stroke=0)
            self.canv.setFillColor(MINT)
            self.canv.roundRect(label_width, y, bar_width * value / maximum, 7 * mm, 3.5 * mm, fill=1, stroke=0)
            self.canv.setFillColor(MUTED)
            self.canv.drawRightString(self.width, y + 2.5 * mm, f"{value:.1f}%")


def _draw_polygon(canvas: Any, points: list[tuple[float, float]], fill: bool) -> None:
    path = canvas.beginPath()
    path.moveTo(*points[0])
    for point in points[1:]:
        path.lineTo(*point)
    path.close()
    canvas.drawPath(path, fill=int(fill), stroke=1)


def _metric_table(scores: dict[str, Any], locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    data = [
        [Paragraph(f"{float(scores['overall']):.1f}", styles["metric"]),
         Paragraph(f"#{int(scores['regional_rank'])}", styles["metric"]),
         Paragraph("PCA + TOPSIS", styles["metric"])],
        [Paragraph(_label(locale, "Overall score", "综合得分"), styles["metric_label"]),
         Paragraph(_label(locale, "London rank", "伦敦排名"), styles["metric_label"]),
         Paragraph(_label(locale, "Method", "评价方法"), styles["metric_label"])],
    ]
    table = Table(data, colWidths=[54 * mm] * 3, rowHeights=[12 * mm, 8 * mm])
    table.setStyle(_table_style(header=False))
    return table


def _highlight_table(insights: AnalysisInsights, locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    cells = [[
        [Paragraph(_label(locale, "Key strength", "主要优势"), styles["small"]),
         Paragraph(escape(insights.strengths[0].title), styles["card_title"]),
         Paragraph(escape(insights.strengths[0].detail), styles["card_body"])],
        [Paragraph(_label(locale, "Key risk", "主要短板或风险"), styles["small"]),
         Paragraph(escape(insights.weaknesses[0].title), styles["card_title"]),
         Paragraph(escape(insights.weaknesses[0].detail), styles["card_body"])],
    ]]
    table = Table(cells, colWidths=[80 * mm, 80 * mm])
    table.setStyle(_table_style(header=False))
    return table


def _dimension_table(dimensions: list[tuple[str, float]], locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    descriptions = {
        "Economic": "Income, business density and housing affordability.",
        "Social": "Safety, services, culture, healthcare and bus access.",
        "Ecological": "Vegetation, wetness, landscape quality and recycling.",
        "经济": "收入、商业密度与住房负担能力。",
        "社会": "公共安全、服务、文化、医疗与公交可达性。",
        "生态": "植被、湿度、景观质量与回收利用。",
    }
    rows = [[Paragraph(_label(locale, "Dimension", "维度"), styles["card_title"]),
             Paragraph(_label(locale, "Score", "得分"), styles["card_title"]),
             Paragraph(_label(locale, "Indicator scope", "指标范围"), styles["card_title"])]]
    rows.extend([Paragraph(label, styles["body"]), Paragraph(f"{score:.1f}", styles["body"]),
                 Paragraph(descriptions[label], styles["body"])] for label, score in dimensions)
    table = Table(rows, colWidths=[35 * mm, 24 * mm, 101 * mm], repeatRows=1)
    table.setStyle(_table_style())
    return table


def _indicator_table(indicators: dict[str, Any], locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[Paragraph(_label(locale, "Indicator", "指标"), styles["card_title"]),
             Paragraph(_label(locale, "Value", "数值"), styles["card_title"])]]
    rows.extend([Paragraph(escape(indicator_name(key, locale)), styles["body"]),
                 Paragraph(format_indicator_value(key, value), styles["body"])] for key, value in indicators.items())
    table = Table(rows, colWidths=[112 * mm, 48 * mm], repeatRows=1)
    table.setStyle(_table_style())
    return table


def _insight_grid(insights: AnalysisInsights, locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    items: list[tuple[str, Any]] = []
    items.extend((_label(locale, "Driver", "驱动因素"), item) for item in insights.main_drivers)
    items.extend((_label(locale, "Strength", "优势"), item) for item in insights.strengths)
    items.extend((_label(locale, "Weakness", "短板"), item) for item in insights.weaknesses)
    rows = []
    for index in range(0, len(items), 2):
        row = [[Paragraph(kind, styles["small"]), Paragraph(escape(item.title), styles["card_title"]),
                Paragraph(escape(item.detail), styles["card_body"])] for kind, item in items[index:index + 2]]
        if len(row) == 1:
            row.append("")
        rows.append(row)
    table = Table(rows, colWidths=[80 * mm, 80 * mm])
    table.setStyle(_table_style(header=False))
    return table


def _recommendation_table(insights: AnalysisInsights, locale: str, styles: dict[str, ParagraphStyle]) -> Table:
    rows = [[Paragraph(_label(locale, "Priority", "优先级"), styles["card_title"]),
             Paragraph(_label(locale, "Recommendation", "建议"), styles["card_title"]),
             Paragraph(_label(locale, "Decision use", "决策应用"), styles["card_title"])]]
    for item in insights.recommendations:
        priority = _label(locale, "High", "高") if item.priority == "High" else _label(locale, "Medium", "中")
        rows.append([Paragraph(priority, styles["body"]), Paragraph(escape(item.title), styles["body"]),
                     Paragraph(escape(item.detail), styles["body"])])
    table = Table(rows, colWidths=[25 * mm, 48 * mm, 87 * mm], repeatRows=1)
    table.setStyle(_table_style())
    return table


def _table_style(header: bool = True) -> TableStyle:
    commands = [
        ("BACKGROUND", (0, 0), (-1, -1), PAPER),
        ("BOX", (0, 0), (-1, -1), 0.5, BORDER),
        ("INNERGRID", (0, 0), (-1, -1), 0.5, BORDER),
        ("VALIGN", (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("RIGHTPADDING", (0, 0), (-1, -1), 3 * mm),
        ("TOPPADDING", (0, 0), (-1, -1), 2.5 * mm),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2.5 * mm),
    ]
    if header:
        commands.append(("BACKGROUND", (0, 0), (-1, 0), BLUE_LIGHT))
    return TableStyle(commands)


def _cover_page(canvas: Any, _: Any) -> None:
    canvas.saveState()
    canvas.setFillColor(PAPER)
    canvas.rect(0, 0, PAGE_WIDTH, PAGE_HEIGHT, fill=1, stroke=0)
    canvas.setFillColor(BLUE)
    canvas.rect(0, PAGE_HEIGHT - 7 * mm, PAGE_WIDTH, 7 * mm, fill=1, stroke=0)
    canvas.circle(PAGE_WIDTH / 2, PAGE_HEIGHT - 40 * mm, 10 * mm, fill=1, stroke=0)
    canvas.setFillColor(colors.white)
    canvas.setFont("Helvetica-Bold", 15)
    canvas.drawCentredString(PAGE_WIDTH / 2, PAGE_HEIGHT - 42 * mm, "UI")
    canvas.restoreState()


def _content_page(canvas: Any, doc: Any, borough: str, generated_on: date, font: str) -> None:
    canvas.saveState()
    canvas.setStrokeColor(BORDER)
    canvas.line(18 * mm, PAGE_HEIGHT - 12 * mm, PAGE_WIDTH - 18 * mm, PAGE_HEIGHT - 12 * mm)
    canvas.setFont(font, 7.5)
    canvas.setFillColor(MUTED)
    canvas.drawString(18 * mm, PAGE_HEIGHT - 9 * mm, "UrbanInsight AI")
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, PAGE_HEIGHT - 9 * mm, borough)
    canvas.line(18 * mm, 12 * mm, PAGE_WIDTH - 18 * mm, 12 * mm)
    canvas.drawString(18 * mm, 8 * mm, generated_on.isoformat())
    canvas.drawRightString(PAGE_WIDTH - 18 * mm, 8 * mm, str(doc.page))
    canvas.restoreState()


def _method_text(locale: str, request: PDFReportRequest, generated_on: date) -> str:
    if locale == "zh-CN":
        ai_note = (
            f"本次报告包含已完成的 AI 辅助解读，Provider 为 {escape(request.ai_provider or '')}，"
            f"模型为 {escape(request.ai_model or '未记录')}。PDF 生成过程没有再次调用模型。"
            if request.ai_insights_applied
            else "本报告使用完整基础预设解读，PDF 生成过程没有调用外部模型。"
        )
        if request.ai_insights_requested and not request.ai_insights_applied:
            ai_note += " 本次 AI 深度解读未成功应用，当前报告基于完整基础分析结果生成。"
        return (
            "PCA 从标准化指标中提取客观权重，TOPSIS 根据已存储权重评价行政区与理想解的接近程度。"
            "指标与数据来源应结合项目数据说明审阅；本报告仅使用数据库已有指标和分析结果。"
            f"报告生成日期为 {generated_on.isoformat()}。{ai_note}"
            " 本报告仅用于辅助研究与决策，不替代专业规划、投资或公共政策判断。"
        )
    ai_note = (
        f"This report includes completed AI-assisted interpretation from {escape(request.ai_provider or '')} "
        f"using {escape(request.ai_model or 'an unrecorded model')}. PDF generation did not call the model again."
        if request.ai_insights_applied
        else "This report uses the complete preset interpretation. PDF generation did not call an external model."
    )
    if request.ai_insights_requested and not request.ai_insights_applied:
        ai_note += " The requested AI interpretation was not applied, so this report uses the complete basic analysis."
    return (
        "PCA derives objective weights from standardized indicators. TOPSIS evaluates each borough's closeness "
        "to the ideal solution using persisted weights. Indicator provenance should be reviewed with the data "
        f"specification. Generated {generated_on.isoformat()}. {ai_note} This report supports research and "
        "decision-making and does not replace professional planning, investment or public-policy judgement."
    )


def _dimension_label(locale: str, value: str) -> str:
    translations = {"Economic": "经济", "Social": "社会", "Ecological": "生态"}
    return translations.get(value, value) if locale == "zh-CN" else value


def _label(locale: str, english: str, chinese: str) -> str:
    return chinese if locale == "zh-CN" else english
