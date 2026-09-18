import io
import json
import re
import html
from typing import Dict, Any, List, Optional, Union

class ExportGenerator:
    """
    Institutional-Grade Multi-Format Export Engine for AI Venture Studio.
    Produces presentation-ready DOCX, 16:9 PPTX Pitch Decks, vector PDFs, and Excel financial models.
    """

    # ──────────────────────────────────────────────────────────────────────────
    # Helper: Text & Label Cleaners
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def _clean_label(key: str) -> str:
        """Transform snake_case_key into Title Case Header."""
        if not key:
            return ""
        return key.replace("_", " ").strip().title()

    @staticmethod
    def _safe_parse_json(value: Any) -> Any:
        """Recursively parse stringified JSON if needed."""
        if isinstance(value, str):
            trimmed = value.strip()
            if (trimmed.startswith("{") and trimmed.endswith("}")) or (trimmed.startswith("[") and trimmed.endswith("]")):
                try:
                    return json.loads(trimmed)
                except Exception:
                    return value
        return value

    @staticmethod
    def _format_val_str(v: Any) -> str:
        """Cleanly format scalar value for human reading."""
        if v is None:
            return "N/A"
        if isinstance(v, bool):
            return "Yes" if v else "No"
        if isinstance(v, (int, float)):
            if isinstance(v, float) and v.is_integer():
                return f"{int(v):,}"
            elif isinstance(v, float):
                return f"{v:,.2f}"
            return f"{v:,}"
        return str(v).strip()

    # ──────────────────────────────────────────────────────────────────────────
    # 1. MICROSOFT WORD (.DOCX) EXPORT
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_docx(project_name: Optional[Union[str, Dict[str, Any]]], reports: List[Dict[str, Any]]) -> bytes:
        """
        Generate an institutional-grade, beautifully formatted Microsoft Word (.docx)
        diligence memorandum complete with styled tables, callout blocks, and no raw code.
        """
        import docx
        from docx.shared import Inches, Pt, RGBColor
        from docx.enum.text import WD_ALIGN_PARAGRAPH
        from docx.enum.table import WD_TABLE_ALIGNMENT
        from docx.oxml import OxmlElement, parse_xml
        from docx.oxml.ns import nsdecls, qn

        if isinstance(project_name, dict):
            safe_project_name = str(project_name.get("name") or "Venture Advisory").strip()
        elif isinstance(project_name, str):
            safe_project_name = project_name.strip() or "Venture Advisory"
        else:
            safe_project_name = "Venture Advisory"

        doc = docx.Document()

        # Set standard margins (1 inch all sides)
        for section in doc.sections:
            section.top_margin = Inches(1.0)
            section.bottom_margin = Inches(1.0)
            section.left_margin = Inches(1.0)
            section.right_margin = Inches(1.0)

        # Base Palette
        COLOR_PRIMARY = RGBColor(15, 23, 42)      # Deep Navy #0F172A
        COLOR_ACCENT = RGBColor(79, 70, 229)      # Indigo #4F46E5
        COLOR_MUTED = RGBColor(100, 116, 139)     # Slate #64748B
        COLOR_TEXT = RGBColor(30, 41, 59)         # Dark Slate #1E293B

        def set_cell_background(cell, hex_color: str):
            shading = parse_xml(f'<w:shd {nsdecls("w")} w:fill="{hex_color}"/>')
            cell._tc.get_or_add_tcPr().append(shading)

        def set_cell_margins(cell, top=100, bottom=100, left=150, right=150):
            tcPr = cell._tc.get_or_add_tcPr()
            tcMar = OxmlElement('w:tcMar')
            for margin, val in [('top', top), ('bottom', bottom), ('left', left), ('right', right)]:
                node = OxmlElement(f'w:{margin}')
                node.set(qn('w:w'), str(val))
                node.set(qn('w:type'), 'dxa')
                tcMar.append(node)
            tcPr.append(tcMar)

        # ── COVER / TITLE BANNER ──
        title_p = doc.add_paragraph()
        title_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        title_run = title_p.add_run(safe_project_name.upper())
        title_run.font.name = 'Calibri'
        title_run.font.size = Pt(26)
        title_run.font.bold = True
        title_run.font.color.rgb = COLOR_PRIMARY

        sub_p = doc.add_paragraph()
        sub_p.alignment = WD_ALIGN_PARAGRAPH.LEFT
        sub_run = sub_p.add_run("Institutional Venture Strategy, Financial Modeling & Due Diligence Memorandum")
        sub_run.font.name = 'Calibri'
        sub_run.font.size = Pt(12)
        sub_run.font.color.rgb = COLOR_ACCENT
        sub_run.font.bold = True

        meta_p = doc.add_paragraph()
        meta_run = meta_p.add_run("Apex Venture Partners · Autonomous Multi-Agent Deliberation Chamber\n")
        meta_run.font.name = 'Calibri'
        meta_run.font.size = Pt(9.5)
        meta_run.font.color.rgb = COLOR_MUTED

        doc.add_paragraph().paragraph_format.space_after = Pt(6)

        # ── RECURSIVE DATA RENDERER FOR WORD ──
        def render_docx_table_from_list_of_dicts(data_list: List[Dict[str, Any]]):
            if not data_list or not isinstance(data_list[0], dict):
                return

            all_keys = []
            for item in data_list:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in all_keys:
                            all_keys.append(k)

            if not all_keys:
                return

            table = doc.add_table(rows=len(data_list) + 1, cols=len(all_keys))
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            # Header Row
            hdr_cells = table.rows[0].cells
            for idx, key in enumerate(all_keys):
                cell = hdr_cells[idx]
                cell.text = ExportGenerator._clean_label(key)
                set_cell_background(cell, "0F172A")
                set_cell_margins(cell, top=120, bottom=120, left=150, right=150)
                p = cell.paragraphs[0]
                p.alignment = WD_ALIGN_PARAGRAPH.LEFT
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)
                    r.font.bold = True
                    r.font.color.rgb = RGBColor(255, 255, 255)

            # Data Rows
            for row_idx, item in enumerate(data_list, start=1):
                row_cells = table.rows[row_idx].cells
                bg_color = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"
                for col_idx, key in enumerate(all_keys):
                    cell = row_cells[col_idx]
                    set_cell_background(cell, bg_color)
                    set_cell_margins(cell, top=100, bottom=100, left=150, right=150)
                    
                    val = item.get(key, "")
                    if isinstance(val, list):
                        cell.text = "\n".join([f"• {ExportGenerator._format_val_str(v_i)}" for v_i in val])
                    elif isinstance(val, dict):
                        cell.text = "\n".join([f"{ExportGenerator._clean_label(k_i)}: {ExportGenerator._format_val_str(v_i)}" for k_i, v_i in val.items()])
                    else:
                        cell.text = ExportGenerator._format_val_str(val)

                    p = cell.paragraphs[0]
                    for r in p.runs:
                        r.font.name = 'Calibri'
                        r.font.size = Pt(9)
                        r.font.color.rgb = COLOR_TEXT

            doc.add_paragraph().paragraph_format.space_after = Pt(8)

        def render_docx_key_value_table(d: Dict[str, Any]):
            if not d:
                return

            table = doc.add_table(rows=len(d), cols=2)
            table.alignment = WD_TABLE_ALIGNMENT.CENTER
            table.autofit = False

            col_widths = (Inches(2.5), Inches(4.0))
            for row_idx, (k, v) in enumerate(d.items()):
                row_cells = table.rows[row_idx].cells
                bg_color = "F8FAFC" if row_idx % 2 == 0 else "FFFFFF"

                c0 = row_cells[0]
                c0.width = col_widths[0]
                set_cell_background(c0, bg_color)
                set_cell_margins(c0, top=80, bottom=80, left=120, right=120)
                c0.text = ExportGenerator._clean_label(k)
                p0 = c0.paragraphs[0]
                for r in p0.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)
                    r.font.bold = True
                    r.font.color.rgb = COLOR_PRIMARY

                c1 = row_cells[1]
                c1.width = col_widths[1]
                set_cell_background(c1, bg_color)
                set_cell_margins(c1, top=80, bottom=80, left=120, right=120)

                if isinstance(v, list):
                    c1.text = "\n".join([f"• {ExportGenerator._format_val_str(v_i)}" for v_i in v])
                elif isinstance(v, dict):
                    c1.text = "\n".join([f"{ExportGenerator._clean_label(k_i)}: {ExportGenerator._format_val_str(v_i)}" for k_i, v_i in v.items()])
                else:
                    c1.text = ExportGenerator._format_val_str(v)

                p1 = c1.paragraphs[0]
                for r in p1.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(9.5)
                    r.font.color.rgb = COLOR_TEXT

            doc.add_paragraph().paragraph_format.space_after = Pt(8)

        def render_docx_section(key: str, val: Any, level: int = 2):
            val = ExportGenerator._safe_parse_json(val)
            section_title = ExportGenerator._clean_label(key)

            h = doc.add_heading(section_title, level=level)
            h.paragraph_format.space_before = Pt(10)
            h.paragraph_format.space_after = Pt(4)
            for r in h.runs:
                r.font.name = 'Calibri'
                r.font.color.rgb = COLOR_ACCENT if level == 2 else COLOR_PRIMARY

            if isinstance(val, (str, int, float, bool)):
                p = doc.add_paragraph()
                p.paragraph_format.space_after = Pt(6)
                p.paragraph_format.line_spacing = 1.15
                run = p.add_run(ExportGenerator._format_val_str(val))
                run.font.name = 'Calibri'
                run.font.size = Pt(10)
                run.font.color.rgb = COLOR_TEXT

            elif isinstance(val, list) and val and isinstance(ExportGenerator._safe_parse_json(val[0]), dict):
                parsed_list = [ExportGenerator._safe_parse_json(item) for item in val]
                render_docx_table_from_list_of_dicts(parsed_list)

            elif isinstance(val, list):
                for item in val:
                    item_str = ExportGenerator._format_val_str(item)
                    p = doc.add_paragraph(style='List Bullet')
                    p.paragraph_format.space_after = Pt(3)
                    p.paragraph_format.line_spacing = 1.15

                    if ":" in item_str and not item_str.startswith("http"):
                        parts = item_str.split(":", 1)
                        r_lead = p.add_run(parts[0] + ":")
                        r_lead.font.name = 'Calibri'
                        r_lead.font.bold = True
                        r_lead.font.size = Pt(10)
                        r_lead.font.color.rgb = COLOR_PRIMARY

                        r_rest = p.add_run(parts[1])
                        r_rest.font.name = 'Calibri'
                        r_rest.font.size = Pt(10)
                        r_rest.font.color.rgb = COLOR_TEXT
                    else:
                        r = p.add_run(item_str)
                        r.font.name = 'Calibri'
                        r.font.size = Pt(10)
                        r.font.color.rgb = COLOR_TEXT

            elif isinstance(val, dict):
                is_simple_dict = all(not isinstance(v_i, (dict, list)) for v_i in val.values())
                if is_simple_dict and len(val) > 2:
                    render_docx_key_value_table(val)
                else:
                    for sub_k, sub_v in val.items():
                        render_docx_section(sub_k, sub_v, level=min(level + 1, 3))

        # ── MAIN REPORTS LOOP ──
        for idx, rep in enumerate(reports, start=1):
            title = rep.get("title") or rep.get("report_type") or f"Report {idx}"
            
            h1 = doc.add_heading(f"SECTION {idx}.0 — {str(title).upper()}", level=1)
            h1.paragraph_format.space_before = Pt(18)
            h1.paragraph_format.space_after = Pt(6)
            for r in h1.runs:
                r.font.name = 'Calibri'
                r.font.size = Pt(14)
                r.font.bold = True
                r.font.color.rgb = COLOR_PRIMARY

            content = ExportGenerator._safe_parse_json(rep.get("content", {}))

            if isinstance(content, dict):
                for k, v in content.items():
                    render_docx_section(k, v, level=2)
            elif isinstance(content, list):
                render_docx_section("Key Deliverables", content, level=2)
            else:
                p = doc.add_paragraph(str(content))
                p.paragraph_format.line_spacing = 1.15
                for r in p.runs:
                    r.font.name = 'Calibri'
                    r.font.size = Pt(10)
                    r.font.color.rgb = COLOR_TEXT

            doc.add_paragraph().paragraph_format.space_after = Pt(10)

        bio = io.BytesIO()
        doc.save(bio)
        return bio.getvalue()

    # ──────────────────────────────────────────────────────────────────────────
    # 2. MICROSOFT POWERPOINT (.PPTX) 16:9 PITCH SLIDE DECK
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_pptx(project_name: Optional[Union[str, Dict[str, Any]]], reports: List[Dict[str, Any]]) -> bytes:
        """
        Generate 16:9 widescreen presentation deck matching the Pitch Deck view.
        Uses institutional dark aesthetic (Obsidian/Slate/Indigo/Gold) and proper slide cards.
        """
        from pptx import Presentation
        from pptx.util import Inches, Pt
        from pptx.dml.color import RGBColor
        from pptx.enum.text import PP_ALIGN
        from pptx.enum.shapes import MSO_SHAPE

        if isinstance(project_name, dict):
            safe_project_name = str(project_name.get("name") or "Venture Advisory").strip()
        elif isinstance(project_name, str):
            safe_project_name = project_name.strip() or "Venture Advisory"
        else:
            safe_project_name = "Venture Advisory"

        prs = Presentation()
        prs.slide_width = Inches(13.333)
        prs.slide_height = Inches(7.5)

        # Palette
        BG_COLOR = RGBColor(10, 13, 20)          # Midnight Obsidian #0A0D14
        PANEL_COLOR = RGBColor(17, 24, 39)       # Dark Glass Panel #111827
        PANEL_BORDER = RGBColor(55, 65, 81)      # Border #374151
        COLOR_PRIMARY = RGBColor(99, 102, 241)   # Electric Indigo #6366F1
        COLOR_GOLD = RGBColor(212, 175, 55)      # Gold #D4AF37
        COLOR_EMERALD = RGBColor(16, 185, 129)   # Emerald #10B981
        COLOR_WHITE = RGBColor(255, 255, 255)    # Pure White #FFFFFF
        COLOR_SLATE_200 = RGBColor(226, 232, 240)# Light Slate #E2E8F0
        COLOR_SLATE_500 = RGBColor(100, 116, 139)# Dim Slate #64748B

        blank_layout = prs.slide_layouts[6]

        def create_dark_background(slide):
            bg = slide.shapes.add_shape(MSO_SHAPE.RECTANGLE, 0, 0, Inches(13.333), Inches(7.5))
            bg.fill.solid()
            bg.fill.fore_color.rgb = BG_COLOR
            bg.line.fill.background()
            return bg

        # Extract Pitch Deck report if available
        pitch_deck_data = {}
        for rep in reports:
            if rep.get("report_type") == "pitch_deck":
                pitch_deck_data = ExportGenerator._safe_parse_json(rep.get("content", {}))
                break

        if not pitch_deck_data:
            for rep in reports:
                if rep.get("report_type") == "executive_summary":
                    pitch_deck_data = ExportGenerator._safe_parse_json(rep.get("content", {}))
                    break

        elevator_pitch = pitch_deck_data.get("elevator_pitch_summary") or pitch_deck_data.get("concept") or "Institutional venture creation and financial modeling analysis."
        slides_outline = pitch_deck_data.get("slide_deck_outline") or []
        if isinstance(slides_outline, str):
            slides_outline = ExportGenerator._safe_parse_json(slides_outline)

        key_highlights = pitch_deck_data.get("key_investment_highlights") or []
        if isinstance(key_highlights, str):
            key_highlights = ExportGenerator._safe_parse_json(key_highlights)

        use_of_funds = pitch_deck_data.get("use_of_funds_breakdown") or {}
        if isinstance(use_of_funds, str):
            use_of_funds = ExportGenerator._safe_parse_json(use_of_funds)

        # ── SLIDE 1: TITLE & COVER SLIDE ──
        s1 = prs.slides.add_slide(blank_layout)
        create_dark_background(s1)

        badge_box = s1.shapes.add_textbox(Inches(1.0), Inches(0.8), Inches(11.333), Inches(0.5))
        tf_b = badge_box.text_frame
        p_b = tf_b.paragraphs[0]
        p_b.text = "APEX VENTURE PARTNERS · EXECUTIVE STRATEGY DECK"
        p_b.font.size = Pt(11)
        p_b.font.bold = True
        p_b.font.color.rgb = COLOR_GOLD

        title_box = s1.shapes.add_textbox(Inches(1.0), Inches(1.3), Inches(11.333), Inches(1.4))
        tf_t = title_box.text_frame
        tf_t.word_wrap = True
        p_t = tf_t.paragraphs[0]
        p_t.text = safe_project_name
        p_t.font.size = Pt(44)
        p_t.font.bold = True
        p_t.font.color.rgb = COLOR_WHITE

        sub_box = s1.shapes.add_textbox(Inches(1.0), Inches(2.7), Inches(11.333), Inches(0.6))
        tf_s = sub_box.text_frame
        p_s = tf_s.paragraphs[0]
        p_s.text = "Autonomous Multi-Agent Deliberation & Financial Feasibility Study"
        p_s.font.size = Pt(18)
        p_s.font.color.rgb = COLOR_PRIMARY

        card = s1.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(3.6), Inches(11.333), Inches(2.6))
        card.fill.solid()
        card.fill.fore_color.rgb = PANEL_COLOR
        card.line.color.rgb = PANEL_BORDER
        card.line.width = Pt(1)

        pitch_tf = card.text_frame
        pitch_tf.word_wrap = True
        pitch_tf.margin_left = Inches(0.4)
        pitch_tf.margin_top = Inches(0.3)
        pitch_tf.margin_right = Inches(0.4)

        p_h = pitch_tf.paragraphs[0]
        p_h.text = "EXECUTIVE ELEVATOR THESIS"
        p_h.font.size = Pt(11)
        p_h.font.bold = True
        p_h.font.color.rgb = COLOR_GOLD

        p_p = pitch_tf.add_paragraph()
        p_p.text = f"\n{elevator_pitch}"
        p_p.font.size = Pt(14)
        p_p.font.color.rgb = COLOR_SLATE_200

        ft_box = s1.shapes.add_textbox(Inches(1.0), Inches(6.6), Inches(11.333), Inches(0.4))
        p_f = ft_box.text_frame.paragraphs[0]
        p_f.text = "CONFIDENTIAL · PREPARED FOR INVESTORS & BOARDROOM REVIEW"
        p_f.font.size = Pt(9)
        p_f.font.color.rgb = COLOR_SLATE_500

        # ── SLIDES 2..N: SLIDE DECK OUTLINE ──
        if isinstance(slides_outline, list) and slides_outline:
            total_slides = len(slides_outline)
            for idx, slide_item in enumerate(slides_outline, start=1):
                slide_item = ExportGenerator._safe_parse_json(slide_item)
                slide_title = f"Slide {idx}"
                category_tag = "STRATEGY"
                headline = ""
                slide_content = ""
                slide_bullets = []
                key_metrics = []
                image_prompt = ""
                layout_tip = ""

                if isinstance(slide_item, dict):
                    slide_title = (
                        slide_item.get("slide_title") or
                        slide_item.get("title") or
                        slide_item.get("name") or
                        slide_item.get("heading") or
                        f"Slide {idx}"
                    )
                    category_tag = (
                        slide_item.get("category_tag") or
                        slide_item.get("category") or
                        slide_item.get("tag") or
                        (slide_title.split(":")[0].strip() if ":" in str(slide_title) else "STRATEGY")
                    )
                    headline = slide_item.get("headline") or slide_item.get("tagline") or slide_item.get("takeaway") or ""
                    
                    slide_content = (
                        slide_item.get("core_content") or
                        slide_item.get("body_content") or
                        slide_item.get("content") or
                        slide_item.get("body") or
                        slide_item.get("description") or
                        slide_item.get("text") or
                        slide_item.get("summary") or
                        slide_item.get("details") or
                        slide_item.get("overview") or
                        slide_item.get("narrative") or
                        slide_item.get("concept") or
                        slide_item.get("message") or
                        slide_item.get("takeaway") or
                        ""
                    )

                    if not slide_content:
                        for k, v in slide_item.items():
                            if k not in ["slide_number", "slide_title", "title", "name", "heading", "topic", "header", "category_tag", "category", "tag", "image_recommendation", "visual_concept", "visual_layout_suggestion", "image_prompt", "visual_prompt"]:
                                if isinstance(v, str) and v.strip():
                                    slide_content = v.strip()
                                    break

                    slide_bullets = (
                        slide_item.get("bullet_points") or
                        slide_item.get("key_points") or
                        slide_item.get("bullets") or
                        slide_item.get("points") or
                        slide_item.get("highlights") or
                        slide_item.get("takeaways") or
                        []
                    )

                    if not slide_bullets and slide_content and isinstance(slide_content, str):
                        if "\n" in slide_content:
                            slide_bullets = [l.strip().lstrip("-*•0123456789.) ") for l in slide_content.split("\n") if l.strip()]
                        elif ";" in slide_content:
                            slide_bullets = [s.strip() for s in slide_content.split(";") if s.strip()]
                        elif ". " in slide_content and len(slide_content) > 50:
                            slide_bullets = [s.strip().rstrip(".") for s in slide_content.split(". ") if len(s.strip()) > 5]
                        elif " - " in slide_content and len(slide_content) > 40:
                            slide_bullets = [s.strip() for s in slide_content.split(" - ") if s.strip()]

                    key_metrics = slide_item.get("key_metrics") or slide_item.get("metrics") or []
                    image_prompt = slide_item.get("image_recommendation") or slide_item.get("image_prompt") or slide_item.get("visual_prompt") or ""
                    layout_tip = slide_item.get("visual_layout_suggestion") or slide_item.get("layout") or ""

                elif isinstance(slide_item, str):
                    slide_title = f"Slide {idx}"
                    slide_content = slide_item
                    if ":" in slide_item:
                        parts = slide_item.split(":", 1)
                        slide_title = parts[0].strip()
                        slide_content = parts[1].strip()

                    if ";" in slide_content:
                        slide_bullets = [s.strip() for s in slide_content.split(";") if s.strip()]
                    elif ". " in slide_content and len(slide_content) > 50:
                        slide_bullets = [s.strip().rstrip(".") for s in slide_content.split(". ") if len(s.strip()) > 5]

                if not image_prompt:
                    t = f"{category_tag} {slide_title} {slide_content}".lower()
                    if "problem" in t or "pain" in t or "friction" in t:
                        image_prompt = "Photorealistic 3D isometric illustration of manual administrative friction vs glowing digital alert halos, dramatic studio lighting with amber accent glow, 8k render."
                    elif "solution" in t or "product" in t or "platform" in t:
                        image_prompt = "Futuristic glassmorphic holographic 3D user interface mockup of cloud analytics platform, glowing cyan and gold data streams, ultra-clean modern SaaS UI."
                    elif "market" in t or "tam" in t or "sam" in t:
                        image_prompt = "3D luminous concentric rings infographic showing TAM/SAM/SOM market sizing over an illuminated map, deep navy blue background, vibrant emerald data beacons."
                    elif "financial" in t or "revenue" in t or "model" in t or "margin" in t:
                        image_prompt = "Dynamic 3D glass bar chart showing exponential 3-Year ARR growth with floating emerald metric badge cubes for 80% Gross Margin and LTV/CAC ratio."
                    elif "ask" in t or "fund" in t or "invest" in t or "capital" in t:
                        image_prompt = "Sleek 3D venture vault unlocking glowing golden tokens representing capital deployment into R&D and market expansion, luxury investor aesthetic."
                    else:
                        image_prompt = f"Premium 3D isometric conceptual render of {safe_project_name} strategic pillars, sleek glassmorphism, gold and electric blue lighting."

                s_i = prs.slides.add_slide(blank_layout)
                create_dark_background(s_i)

                hdr_box = s_i.shapes.add_textbox(Inches(1.0), Inches(0.5), Inches(9.0), Inches(1.0))
                tf_h = hdr_box.text_frame
                tf_h.word_wrap = True
                
                p_num = tf_h.paragraphs[0]
                p_num.text = f"SLIDE {idx:02d} OF {total_slides:02d} · {str(category_tag).upper()}"
                p_num.font.size = Pt(10)
                p_num.font.bold = True
                p_num.font.color.rgb = COLOR_PRIMARY

                p_t = tf_h.add_paragraph()
                p_t.text = ExportGenerator._clean_label(str(slide_title))
                p_t.font.size = Pt(22)
                p_t.font.bold = True
                p_t.font.color.rgb = COLOR_WHITE

                tag_box = s_i.shapes.add_textbox(Inches(10.2), Inches(0.5), Inches(2.133), Inches(0.6))
                p_tag = tag_box.text_frame.paragraphs[0]
                p_tag.alignment = PP_ALIGN.RIGHT
                p_tag.text = safe_project_name
                p_tag.font.size = Pt(10)
                p_tag.font.bold = True
                p_tag.font.color.rgb = COLOR_SLATE_500

                canvas = s_i.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.6), Inches(11.333), Inches(4.9))
                canvas.fill.solid()
                canvas.fill.fore_color.rgb = PANEL_COLOR
                canvas.line.color.rgb = PANEL_BORDER
                canvas.line.width = Pt(1)

                c_tf = canvas.text_frame
                c_tf.word_wrap = True
                c_tf.margin_left = Inches(0.4)
                c_tf.margin_top = Inches(0.3)
                c_tf.margin_right = Inches(0.4)

                has_first_para = False

                if headline and headline != slide_content:
                    p_head = c_tf.paragraphs[0]
                    p_head.text = f'"{headline}"'
                    p_head.font.size = Pt(13)
                    p_head.font.bold = True
                    p_head.font.italic = True
                    p_head.font.color.rgb = COLOR_GOLD
                    p_head.space_after = Pt(10)
                    has_first_para = True

                if slide_content:
                    p_body = c_tf.add_paragraph() if has_first_para else c_tf.paragraphs[0]
                    p_body.text = str(slide_content)
                    p_body.font.size = Pt(13)
                    p_body.font.color.rgb = COLOR_SLATE_200
                    p_body.space_after = Pt(10)
                    has_first_para = True

                if isinstance(slide_bullets, list) and slide_bullets:
                    for b_idx, b in enumerate(slide_bullets):
                        p_b = c_tf.add_paragraph()
                        p_b.text = f"•   {ExportGenerator._format_val_str(b)}"
                        p_b.font.size = Pt(12)
                        p_b.font.color.rgb = COLOR_WHITE if b_idx == 0 else COLOR_SLATE_200
                        p_b.space_after = Pt(6)

                if isinstance(key_metrics, list) and key_metrics:
                    p_met = c_tf.add_paragraph()
                    p_met.text = f"📊 Key Metrics: {' | '.join(str(m) for m in key_metrics)}"
                    p_met.font.size = Pt(11)
                    p_met.font.bold = True
                    p_met.font.color.rgb = COLOR_EMERALD
                    p_met.space_after = Pt(6)

                if image_prompt:
                    p_img = c_tf.add_paragraph()
                    p_img.text = f"\n🎨 AI Image Prompt: {image_prompt}"
                    p_img.font.size = Pt(9)
                    p_img.font.italic = True
                    p_img.font.color.rgb = COLOR_PRIMARY

                # ── EMBED NATIVE CHART IF SLIDE IS FINANCIAL / METRIC ORIENTED ──
                t_lower = f"{category_tag} {slide_title}".lower()
                if "financial" in t_lower or "projection" in t_lower or "runway" in t_lower or "unit economic" in t_lower:
                    try:
                        from pptx.chart.data import CategoryChartData
                        from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION
                        
                        f_chart_data = CategoryChartData()
                        f_chart_data.categories = ['Year 1', 'Year 2', 'Year 3']
                        f_chart_data.add_series('ARR (₹ Cr)', (1.2, 4.8, 14.5))
                        f_chart_data.add_series('Gross Margin (%)', (72, 79, 83))

                        # Add compact column chart on the right side
                        chart_shape = s_i.shapes.add_chart(
                            XL_CHART_TYPE.COLUMN_CLUSTERED,
                            Inches(8.2), Inches(2.2), Inches(4.3), Inches(3.8),
                            f_chart_data
                        )
                        f_chart = chart_shape.chart
                        f_chart.has_legend = True
                        f_chart.legend.position = XL_LEGEND_POSITION.TOP
                        f_chart.legend.include_in_layout = False
                    except Exception:
                        pass

                # ── EMBED EXECUTIVE PRESENTER NOTES ──
                try:
                    notes_slide = s_i.notes_slide
                    tf_notes = notes_slide.notes_text_frame
                    tf_notes.text = f"EXECUTIVE SCRIPT — SLIDE {idx}: {slide_title}\n"
                    if headline:
                        tf_notes.text += f"\nKey Takeaway: {headline}\n"
                    if slide_content:
                        tf_notes.text += f"\nNarrative: {slide_content}\n"
                    if slide_bullets:
                        tf_notes.text += "\nTalking Points:\n" + "\n".join(f"- {b}" for b in slide_bullets)
                    if image_prompt:
                        tf_notes.text += f"\n\n[AI Image Prompt]: {image_prompt}"
                    if layout_tip:
                        tf_notes.text += f"\n[Slide Layout Recommendation]: {layout_tip}"
                except Exception:
                    pass

                ft_box = s_i.shapes.add_textbox(Inches(1.0), Inches(6.7), Inches(11.333), Inches(0.4))
                p_f = ft_box.text_frame.paragraphs[0]
                p_f.text = f"{safe_project_name} · Confidential Strategic Memorandum"
                p_f.font.size = Pt(9)
                p_f.font.color.rgb = COLOR_SLATE_500

        # ── SLIDE: INVESTMENT HIGHLIGHTS & USE OF FUNDS WITH NATIVE DONUT CHART ──
        if key_highlights or use_of_funds:
            s_inv = prs.slides.add_slide(blank_layout)
            create_dark_background(s_inv)

            hdr_box = s_inv.shapes.add_textbox(Inches(1.0), Inches(0.6), Inches(11.333), Inches(0.9))
            tf_h = hdr_box.text_frame
            p_n = tf_h.paragraphs[0]
            p_n.text = "STRATEGIC CAPITAL ALLOCATION"
            p_n.font.size = Pt(10)
            p_n.font.bold = True
            p_n.font.color.rgb = COLOR_GOLD

            p_t = tf_h.add_paragraph()
            p_t.text = "Investment Highlights & Use of Proceeds"
            p_t.font.size = Pt(24)
            p_t.font.bold = True
            p_t.font.color.rgb = COLOR_WHITE

            # Left Card: Investment Highlights
            c_left = s_inv.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(1.0), Inches(1.7), Inches(5.6), Inches(4.8))
            c_left.fill.solid()
            c_left.fill.fore_color.rgb = PANEL_COLOR
            c_left.line.color.rgb = PANEL_BORDER
            c_left.line.width = Pt(1)

            l_tf = c_left.text_frame
            l_tf.word_wrap = True
            l_tf.margin_left = Inches(0.4)
            l_tf.margin_top = Inches(0.4)
            l_tf.margin_right = Inches(0.4)

            p_lh = l_tf.paragraphs[0]
            p_lh.text = "KEY INVESTMENT HIGHLIGHTS"
            p_lh.font.size = Pt(12)
            p_lh.font.bold = True
            p_lh.font.color.rgb = COLOR_PRIMARY
            p_lh.space_after = Pt(10)

            if isinstance(key_highlights, list):
                for h_item in key_highlights[:5]:
                    p_hi = l_tf.add_paragraph()
                    p_hi.text = f"•  {ExportGenerator._format_val_str(h_item)}"
                    p_hi.font.size = Pt(11)
                    p_hi.font.color.rgb = COLOR_SLATE_200
                    p_hi.space_after = Pt(8)

            # Right Card: Native Donut Chart for Capital Allocation
            c_right = s_inv.shapes.add_shape(MSO_SHAPE.ROUNDED_RECTANGLE, Inches(6.9), Inches(1.7), Inches(5.4), Inches(4.8))
            c_right.fill.solid()
            c_right.fill.fore_color.rgb = PANEL_COLOR
            c_right.line.color.rgb = PANEL_BORDER
            c_right.line.width = Pt(1)

            r_tf = c_right.text_frame
            r_tf.word_wrap = True
            r_tf.margin_left = Inches(0.4)
            r_tf.margin_top = Inches(0.3)
            r_tf.margin_right = Inches(0.4)

            p_rh = r_tf.paragraphs[0]
            p_rh.text = "PROPOSED USE OF FUNDS (%)"
            p_rh.font.size = Pt(12)
            p_rh.font.bold = True
            p_rh.font.color.rgb = COLOR_GOLD
            p_rh.space_after = Pt(4)

            # Extract numeric breakdown for python-pptx native donut chart
            donut_cats = []
            donut_vals = []

            if isinstance(use_of_funds, dict):
                for fund_k, fund_v in use_of_funds.items():
                    val = 25.0
                    if isinstance(fund_v, dict):
                        pct = fund_v.get('percentage') or fund_v.get('share') or 25
                        try:
                            val = float(str(pct).replace('%', '').strip())
                        except Exception:
                            val = 25.0
                    else:
                        try:
                            val = float(str(fund_v).replace('%', '').strip())
                        except Exception:
                            val = 25.0
                    donut_cats.append(ExportGenerator._clean_label(fund_k))
                    donut_vals.append(val)
            elif isinstance(use_of_funds, list):
                for idx_u, u in enumerate(use_of_funds):
                    donut_cats.append(f"Allocation #{idx_u+1}")
                    donut_vals.append(25.0)

            if not donut_cats:
                donut_cats = ['Product & R&D', 'GTM Sales', 'Compliance & Security', 'Working Capital']
                donut_vals = [40.0, 30.0, 15.0, 15.0]

            try:
                from pptx.chart.data import CategoryChartData
                from pptx.enum.chart import XL_CHART_TYPE, XL_LEGEND_POSITION

                chart_data = CategoryChartData()
                chart_data.categories = donut_cats
                chart_data.add_series('Allocation (%)', tuple(donut_vals))

                chart_shape = s_inv.shapes.add_chart(
                    XL_CHART_TYPE.DOUGHNUT,
                    Inches(7.1), Inches(2.4), Inches(5.0), Inches(3.8),
                    chart_data
                )
                chart = chart_shape.chart
                chart.has_legend = True
                chart.legend.position = XL_LEGEND_POSITION.BOTTOM
                chart.legend.include_in_layout = False
                chart.plots[0].has_data_labels = True
            except Exception:
                # Text fallback if chart plotting encounters system limitation
                if isinstance(use_of_funds, dict):
                    for fund_k, fund_v in use_of_funds.items():
                        p_fi = r_tf.add_paragraph()
                        if isinstance(fund_v, dict):
                            pct = fund_v.get('percentage') or fund_v.get('share') or ''
                            desc = fund_v.get('description') or ''
                            pct_str = f"{pct}%" if pct and not str(pct).endswith('%') else str(pct)
                            p_fi.text = f"•  {ExportGenerator._clean_label(fund_k)} ({pct_str}): {desc}"
                        else:
                            v_str = f"{fund_v}%" if not str(fund_v).endswith('%') else str(fund_v)
                            p_fi.text = f"•  {ExportGenerator._clean_label(fund_k)}: {v_str}"
                        p_fi.font.size = Pt(11)
                        p_fi.font.color.rgb = COLOR_SLATE_200
                        p_fi.space_after = Pt(8)

            # Presenter notes for capital allocation slide
            try:
                s_inv.notes_slide.notes_text_frame.text = (
                    f"CAPITAL ALLOCATION & PROCEEDS DEPLOYMENT:\n"
                    f"Highlights: {len(key_highlights)} key investment pillars.\n"
                    f"Use of Funds: {', '.join(f'{c}: {v}%' for c, v in zip(donut_cats, donut_vals))}\n"
                    f"Target Runway: 18-24 months to Series A milestone."
                )
            except Exception:
                pass

        bio = io.BytesIO()
        prs.save(bio)
        return bio.getvalue()

    # ──────────────────────────────────────────────────────────────────────────
    # 3. VECTOR PDF EXPORT (REPORTLAB)
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_pdf(project_name: Optional[Union[str, Dict[str, Any]]], reports: List[Dict[str, Any]]) -> bytes:
        """
        Generate institutional vector PDF via ReportLab with running headers/footers,
        clean table generation, zero raw code text, and proper XML escaping.
        """
        from reportlab.lib.pagesizes import letter
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable
        from reportlab.lib import colors
        from reportlab.pdfgen import canvas

        if isinstance(project_name, dict):
            safe_project_name = str(project_name.get("name") or "Venture Advisory").strip()
        elif isinstance(project_name, str):
            safe_project_name = project_name.strip() or "Venture Advisory"
        else:
            safe_project_name = "Venture Advisory"

        class NumberedCanvas(canvas.Canvas):
            def __init__(self, *args, **kwargs):
                super().__init__(*args, **kwargs)
                self._saved_page_states: List[Dict[str, Any]] = []

            def showPage(self):
                self._saved_page_states.append(dict(self.__dict__))
                super().showPage()

            def save(self):
                num_pages = len(self._saved_page_states)
                for state in self._saved_page_states:
                    self.__dict__.update(state)
                    self.draw_header_footer(num_pages)
                    super().showPage()
                super().save()

            def draw_header_footer(self, page_count: int):
                self.saveState()
                self.setFont("Helvetica", 8)
                self.setFillColor(colors.HexColor("#64748B"))
                
                curr_page = getattr(self, '_pageNumber', 1)
                if curr_page > 1:
                    self.drawString(50, 750, f"{safe_project_name} — Institutional Strategy Report")
                    self.setStrokeColor(colors.HexColor("#E2E8F0"))
                    self.setLineWidth(0.5)
                    self.line(50, 742, 562, 742)

                page_text = f"Page {curr_page} of {page_count}"
                self.drawRightString(562, 35, page_text)
                self.drawString(50, 35, "CONFIDENTIAL · APEX VENTURE PARTNERS ADVISORY")
                self.setStrokeColor(colors.HexColor("#E2E8F0"))
                self.setLineWidth(0.5)
                self.line(50, 45, 562, 45)
                self.restoreState()

        bio = io.BytesIO()
        doc = SimpleDocTemplate(
            bio,
            pagesize=letter,
            rightMargin=50,
            leftMargin=50,
            topMargin=55,
            bottomMargin=55
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            name="VentureTitle",
            fontName="Helvetica-Bold",
            fontSize=22,
            leading=26,
            textColor=colors.HexColor("#0F172A"),
            spaceAfter=4
        )
        subtitle_style = ParagraphStyle(
            name="VentureSubtitle",
            fontName="Helvetica-Bold",
            fontSize=11,
            leading=15,
            textColor=colors.HexColor("#4F46E5"),
            spaceAfter=4
        )
        meta_style = ParagraphStyle(
            name="VentureMeta",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#64748B"),
            spaceAfter=12
        )
        h1_style = ParagraphStyle(
            name="VentureH1",
            fontName="Helvetica-Bold",
            fontSize=14,
            leading=18,
            textColor=colors.HexColor("#0F172A"),
            spaceBefore=14,
            spaceAfter=6,
            keepWithNext=True
        )
        h2_style = ParagraphStyle(
            name="VentureH2",
            fontName="Helvetica-Bold",
            fontSize=10.5,
            leading=14,
            textColor=colors.HexColor("#4F46E5"),
            spaceBefore=8,
            spaceAfter=4,
            keepWithNext=True
        )
        body_style = ParagraphStyle(
            name="VentureBody",
            fontName="Helvetica",
            fontSize=9,
            leading=13,
            textColor=colors.HexColor("#1E293B"),
            spaceAfter=5
        )
        bullet_style = ParagraphStyle(
            name="VentureBullet",
            fontName="Helvetica",
            fontSize=8.5,
            leading=12,
            textColor=colors.HexColor("#1E293B"),
            leftIndent=12,
            firstLineIndent=-8,
            spaceAfter=3
        )
        tbl_hdr_style = ParagraphStyle(
            name="VentureTblHdr",
            fontName="Helvetica-Bold",
            fontSize=8,
            leading=10,
            textColor=colors.white
        )
        tbl_cell_style = ParagraphStyle(
            name="VentureTblCell",
            fontName="Helvetica",
            fontSize=8,
            leading=11,
            textColor=colors.HexColor("#1E293B")
        )

        story = []

        # ── TITLE BANNER ──
        story.append(Paragraph(html.escape(safe_project_name.upper()), title_style))
        story.append(Paragraph("Institutional Venture Strategy, Financial Projections & Due Diligence", subtitle_style))
        story.append(Paragraph("Apex Venture Partners · Autonomous Multi-Agent Deliberation Chamber", meta_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor("#4F46E5"), spaceAfter=14))

        def render_pdf_table_from_list_of_dicts(data_list: List[Dict[str, Any]]):
            if not data_list or not isinstance(data_list[0], dict):
                return

            all_keys = []
            for item in data_list:
                if isinstance(item, dict):
                    for k in item.keys():
                        if k not in all_keys:
                            all_keys.append(k)

            if not all_keys:
                return

            col_width = 512.0 / len(all_keys)
            col_widths = [col_width] * len(all_keys)

            table_data = []
            header_row = [Paragraph(html.escape(ExportGenerator._clean_label(k)), tbl_hdr_style) for k in all_keys]
            table_data.append(header_row)

            for item in data_list:
                row = []
                for k in all_keys:
                    val = item.get(k, "")
                    if isinstance(val, list):
                        cell_txt = "<br/>".join([f"• {html.escape(ExportGenerator._format_val_str(v_i))}" for v_i in val])
                    elif isinstance(val, dict):
                        cell_txt = "<br/>".join([f"<b>{html.escape(ExportGenerator._clean_label(k_i))}</b>: {html.escape(ExportGenerator._format_val_str(v_i))}" for k_i, v_i in val.items()])
                    else:
                        cell_txt = html.escape(ExportGenerator._format_val_str(val))
                    row.append(Paragraph(cell_txt, tbl_cell_style))
                table_data.append(row)

            t = Table(table_data, colWidths=col_widths)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0F172A")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 4),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            story.append(t)
            story.append(Spacer(1, 8))

        def render_pdf_key_value_table(d: Dict[str, Any]):
            if not d:
                return

            table_data = []
            for k, v in d.items():
                k_p = Paragraph(f"<b>{html.escape(ExportGenerator._clean_label(k))}</b>", tbl_cell_style)
                if isinstance(v, list):
                    v_txt = "<br/>".join([f"• {html.escape(ExportGenerator._format_val_str(v_i))}" for v_i in v])
                elif isinstance(v, dict):
                    v_txt = "<br/>".join([f"<b>{html.escape(ExportGenerator._clean_label(k_i))}</b>: {html.escape(ExportGenerator._format_val_str(v_i))}" for k_i, v_i in v.items()])
                else:
                    v_txt = html.escape(ExportGenerator._format_val_str(v))
                v_p = Paragraph(v_txt, tbl_cell_style)
                table_data.append([k_p, v_p])

            t = Table(table_data, colWidths=[160, 352])
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, -1), colors.white),
                ('VALIGN', (0, 0), (-1, -1), 'TOP'),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.HexColor("#F8FAFC"), colors.white]),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#E2E8F0")),
            ]))
            story.append(t)
            story.append(Spacer(1, 6))

        def render_pdf_section(key: str, val: Any, is_top: bool = False):
            val = ExportGenerator._safe_parse_json(val)
            section_title = ExportGenerator._clean_label(key)

            if is_top:
                story.append(Paragraph(html.escape(section_title), h2_style))

            if isinstance(val, (str, int, float, bool)):
                txt = html.escape(ExportGenerator._format_val_str(val))
                story.append(Paragraph(txt, body_style))

            elif isinstance(val, list) and val and isinstance(ExportGenerator._safe_parse_json(val[0]), dict):
                parsed_list = [ExportGenerator._safe_parse_json(item) for item in val]
                render_pdf_table_from_list_of_dicts(parsed_list)

            elif isinstance(val, list):
                for item in val:
                    item_str = ExportGenerator._format_val_str(item)
                    if ":" in item_str and not item_str.startswith("http"):
                        parts = item_str.split(":", 1)
                        lead = html.escape(parts[0].strip())
                        rest = html.escape(parts[1].strip())
                        story.append(Paragraph(f"• <b>{lead}:</b> {rest}", bullet_style))
                    else:
                        story.append(Paragraph(f"• {html.escape(item_str)}", bullet_style))
                story.append(Spacer(1, 4))

            elif isinstance(val, dict):
                is_simple = all(not isinstance(v_i, (dict, list)) for v_i in val.values())
                if is_simple and len(val) >= 2:
                    render_pdf_key_value_table(val)
                else:
                    for sub_k, sub_v in val.items():
                        story.append(Paragraph(html.escape(ExportGenerator._clean_label(sub_k)), h2_style))
                        render_pdf_section(sub_k, sub_v, is_top=False)

        for idx, rep in enumerate(reports, start=1):
            title = rep.get("title") or rep.get("report_type") or f"Report {idx}"
            story.append(Paragraph(f"SECTION {idx}.0 — {html.escape(str(title).upper())}", h1_style))
            story.append(HRFlowable(width="100%", thickness=0.5, color=colors.HexColor("#CBD5E1"), spaceAfter=8))

            content = ExportGenerator._safe_parse_json(rep.get("content", {}))

            if isinstance(content, dict):
                for k, v in content.items():
                    render_pdf_section(k, v, is_top=True)
            elif isinstance(content, list):
                render_pdf_section("Key Deliverables", content, is_top=False)
            else:
                story.append(Paragraph(html.escape(str(content)), body_style))

            story.append(Spacer(1, 10))

        doc.build(story, canvasmaker=NumberedCanvas)
        return bio.getvalue()

    # ──────────────────────────────────────────────────────────────────────────
    # 4. MICROSOFT EXCEL (.XLSX) 36-MONTH FINANCIAL MODEL
    # ──────────────────────────────────────────────────────────────────────────
    @staticmethod
    def generate_excel_simulation(
        project_name: Optional[str], 
        simulation_data: Dict[str, Any],
        project_meta: Optional[Dict[str, Any]] = None,
        reports: Optional[List[Dict[str, Any]]] = None
    ) -> bytes:
        """Generate an institutional-grade, 4-sheet 36-month financial model spreadsheet in Microsoft Excel (.xlsx)."""
        from services.excel_financial_generator import ExcelFinancialGenerator
        return ExcelFinancialGenerator.generate(project_name, simulation_data, project_meta, reports)

export_generator = ExportGenerator()
