# services/output_format_service.py
"""
export_service.py
=================

Service for exporting analysis results (ContentAnalysis) to XLSX.
"""

from __future__ import annotations

import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from openpyxl import Workbook
from openpyxl.worksheet.worksheet import Worksheet

from models.domain import ContentAnalysis
from models.domain.label_model import Label  # <-- needed for type hints


##################################################################
class ExportService:
    """Handles generation of XLSX export files based on a ContentAnalysis."""

    # ----------------------------------------------------------------
    def __init__(self, base_export_dir: Optional[Path] = None):
        """
        Initialize ExportService.

        Args:
            base_export_dir: Root folder where exports are stored.
                             Defaults to "<project_root>/exports".
        """
        if base_export_dir is None:
            # You can adjust this to your project structure if needed
            base_export_dir = Path.cwd() / "exports"

        self.base_export_dir = base_export_dir

    # ----------------------------------------------------------------
    def export_to_xlsx(self, content_analysis: ContentAnalysis) -> Path:
        """
        Export the final ContentAnalysis state to an .xlsx spreadsheet.

        Args:
            content_analysis: Fully populated ContentAnalysis object
                              (final analysis state).

        Returns:
            Path to the created .xlsx file.
        """

        # 1) Compute smart folder + filename
        platform_str = getattr(content_analysis, "platform", None)
        if platform_str is None and getattr(content_analysis, "content", None):
            # fallback: take platform from the content if present
            platform_str = getattr(content_analysis.content, "platform", "unknown")

        # If platform is an Enum, use its value
        if hasattr(platform_str, "value"):
            platform_str = platform_str.value

        platform_str = str(platform_str or "unknown").lower()

        content = getattr(content_analysis, "content", None)
        content_id = getattr(content, "content_id", None) or getattr(
            content, "id", "unknown_id"
        )
        title = getattr(content, "title", "") or "untitled"

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

        safe_title = self._slugify(title)[:80]  # avoid super-long filenames

        export_dir = (
            self.base_export_dir
            / platform_str
            / str(content_id)
        )
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{safe_title}_{timestamp}.xlsx"
        export_path = export_dir / filename

        # 2) Prepare workbook + worksheet
        wb = Workbook()
        ws: Worksheet = wb.active
        ws.title = "Comments"

        # 2a) Get comments from ContentAnalysis
        comments = getattr(content_analysis, "comments", []) or []

        # 2b) Discover all model keys + classification names from labels
        all_model_keys: set[str] = set()
        all_class_names: set[str] = set()

        for comment in comments:
            labels_by_model: Dict[str, Dict[str, Label]] = comment.labels or {}
            for model_key, clf_dict in labels_by_model.items():
                all_model_keys.add(model_key)
                for class_name in clf_dict.keys():
                    all_class_names.add(class_name)

        # 2c) Use classification_group to define canonical order if available
        classification_group = getattr(content_analysis, "classification_group", None)
        if classification_group and getattr(classification_group, "classifications", None):
            group_names = [clf.name for clf in classification_group.classifications]
            # include any “extra” class names that appear in data but not in the group
            extras = sorted(all_class_names - set(group_names))
            ordered_class_names: List[str] = group_names + extras
        else:
            ordered_class_names = sorted(all_class_names)

        ordered_model_keys: List[str] = sorted(all_model_keys)

        # 3) Build headers
        # --- Core content-level info (repeated on each row for convenience)
        headers: List[str] = [
            "platform",
            "content_id",
            "content_title",
        ]

        # --- Comment-level info
        comment_headers = [
            "comment_id",
            "author",
            "like_count",
            "reply_count",
            "published_at",
            "text",
        ]
        headers.extend(comment_headers)

        # --- Classification headers: two columns per (class, model)
        model_class_headers: List[str] = []
        for model_key in ordered_model_keys:
            for class_name in ordered_class_names:
                model_class_headers.append(f"{class_name} [{model_key}] value")
                model_class_headers.append(f"{class_name} [{model_key}] explanation")

        headers.extend(model_class_headers)

        # Write header row
        ws.append(headers)

        # 4) Write one row per comment
        for comment in comments:
            row: List[Any] = []

            # content-level cells
            row.append(platform_str)
            row.append(content_id)
            row.append(title)

            # comment-level cells
            comment_id = comment.comment_id
            author = comment.author
            like_count = comment.like_count
            reply_count = comment.reply_count
            published_at = comment.published_at
            text = comment.text

            row.extend(
                [
                    comment_id,
                    author,
                    like_count,
                    reply_count,
                    published_at,
                    text,
                ]
            )

            # --- labels: Dict[model_key, Dict[class_name, Label]] ---
            labels_by_model: Dict[str, Dict[str, Label]] = comment.labels or {}

            for model_key in ordered_model_keys:
                clf_dict = labels_by_model.get(model_key, {}) or {}
                for class_name in ordered_class_names:
                    label_obj = clf_dict.get(class_name)

                    if label_obj is None:
                        # No label from this model for this class:
                        # empty value + empty explanation
                        row.append("")
                        row.append("")
                        continue

                    # VALUE
                    value = getattr(label_obj, "value", None)
                    if hasattr(value, "value"):  # unwrap Enum-like
                        value = value.value
                    value_str = "" if value is None else str(value)

                    # EXPLANATION (optional)
                    explanation = getattr(label_obj, "explanation", None)
                    explanation_str = "" if explanation is None else str(explanation)

                    row.append(value_str)
                    row.append(explanation_str)

            ws.append(row)

        # 5) (Optional but nice) Auto-size columns a bit
        for column_cells in ws.columns:
            max_length = 0
            column_letter = column_cells[0].column_letter
            for cell in column_cells:
                try:
                    cell_value = str(cell.value) if cell.value is not None else ""
                    max_length = max(max_length, len(cell_value))
                except Exception:
                    pass
            # simple heuristic: max_length + 2, capped so text column doesn't explode
            ws.column_dimensions[column_letter].width = min(max_length + 2, 80)

        # 6) Save workbook
        wb.save(export_path)

        return export_path

    # ----------------------------------------------------------------
    @staticmethod
    def _slugify(text: str) -> str:
        """
        Turn an arbitrary string into a filesystem-safe slug.
        """
        text = text.strip().lower()
        text = re.sub(r"\s+", "_", text)
        text = re.sub(r"[^a-z0-9_\-]+", "", text)
        return text or "untitled"
