"""Utilities for turning a structured repository analysis into a PDF document."""

from __future__ import annotations

import io
from typing import Dict, Iterable, List

from fpdf import FPDF


class AnalysisPDF(FPDF):
    """Customised PDF layout for the generated explanations."""

    def header(self) -> None:  # pragma: no cover - drawing code
        self.set_font("Helvetica", "B", 16)
        self.set_text_color(40, 40, 40)
        self.cell(0, 10, "Gitalyzer Report", ln=True, align="C")
        self.ln(4)

    def footer(self) -> None:  # pragma: no cover - drawing code
        self.set_y(-15)
        self.set_font("Helvetica", size=8)
        self.set_text_color(120, 120, 120)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")


def _write_section(pdf: AnalysisPDF, title: str, body: str | None = None) -> None:
    pdf.set_font("Helvetica", "B", 13)
    pdf.set_text_color(40, 40, 40)
    pdf.multi_cell(0, 8, title)
    pdf.ln(1)
    if body:
        pdf.set_font("Helvetica", size=11)
        pdf.set_text_color(10, 10, 10)
        pdf.multi_cell(0, 6, body)
        pdf.ln(2)


def _write_list(pdf: AnalysisPDF, items: Iterable[str]) -> None:
    pdf.set_font("Helvetica", size=11)
    pdf.set_text_color(10, 10, 10)
    for item in items:
        pdf.multi_cell(0, 6, f"• {item}")
    pdf.ln(2)


def build_pdf(repo_name: str, analysis: Dict[str, any]) -> bytes:
    pdf = AnalysisPDF()
    pdf.set_auto_page_break(auto=True, margin=15)
    pdf.add_page()

    pdf.set_font("Helvetica", "B", 18)
    pdf.cell(0, 12, repo_name or "Repository Report", ln=True)
    pdf.ln(4)

    summary = analysis.get("project_summary")
    if summary:
        _write_section(pdf, "Project Summary", summary)

    _write_section(pdf, "How it helps people", analysis.get("how_it_helps_people"))

    if analysis.get("main_features"):
        _write_section(pdf, "Main features")
        _write_list(pdf, analysis["main_features"])

    if analysis.get("how_it_works"):
        _write_section(pdf, "How it works")
        _write_list(pdf, analysis["how_it_works"])

    if analysis.get("tech_stack"):
        _write_section(pdf, "Tech explained simply")
        _write_list(pdf, analysis["tech_stack"])

    if analysis.get("getting_started"):
        _write_section(pdf, "Getting started")
        _write_list(pdf, analysis["getting_started"])

    if analysis.get("next_steps"):
        _write_section(pdf, "Next steps")
        _write_list(pdf, analysis["next_steps"])

    glossary: List[Dict[str, str]] = analysis.get("glossary", [])
    if glossary:
        _write_section(pdf, "Glossary")
        for entry in glossary:
            term = entry.get("term")
            definition = entry.get("definition")
            if term and definition:
                pdf.set_font("Helvetica", "B", 11)
                pdf.multi_cell(0, 6, term)
                pdf.set_font("Helvetica", size=11)
                pdf.multi_cell(0, 6, definition)
                pdf.ln(1)

    pdf_bytes = pdf.output(dest="S").encode("latin-1")
    return pdf_bytes
