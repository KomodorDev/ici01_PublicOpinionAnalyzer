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
from models.domain.content_item_model import ContentItem
from models.domain.comment_model import Comment
from enums.platform_enum import PlatformEnum
from enums.task_status_enum import TaskStatusEnum


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

        # Mark export as running on the domain object so controllers/views
        content_analysis.export_status = TaskStatusEnum.RUNNING
        
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

        export_dir = self.base_export_dir / platform_str / str(content_id)
        export_dir.mkdir(parents=True, exist_ok=True)

        filename = f"{safe_title}_{timestamp}.xlsx"
        export_path = export_dir / filename

        # 2) Prepare workbook + two sheets: Overview + Comments
        wb = Workbook()

        # Overview sheet (first / default)
        ws_overview: Worksheet = wb.active
        ws_overview.title = "Overview"

        # Comments sheet (second)
        ws_comments: Worksheet = wb.create_sheet(title="Comments")

        # 2a) Populate Overview sheet with key/value metadata
        content = getattr(content_analysis, "content", None)
        overview_rows: List[List[Any]] = []

        def _maybe_get(obj, *attrs):
            for a in attrs:
                if obj is None:
                    return None
                obj = getattr(obj, a, None)
            return obj

        overview_rows.append(["exported_at", datetime.now().isoformat()])
        overview_rows.append(["platform", platform_str])
        overview_rows.append(["content_id", content_id])
        overview_rows.append(["title", title])
        overview_rows.append(
            ["url", _maybe_get(content, "url") or _maybe_get(content, "web_url") or ""]
        )
        overview_rows.append(["author", _maybe_get(content, "author") or ""])
        pub = _maybe_get(content, "published_at")
        overview_rows.append(["published_at", str(pub) if pub is not None else ""])
        overview_rows.append(
            ["num_comments", len(getattr(content_analysis, "comments", []) or [])]
        )

        # include content-level summary if present (e.g., AI/manual)
        content_summary = _maybe_get(content, "summary")
        if content_summary:
            overview_rows.append(["content_summary", str(content_summary)])
        content_summary_source = _maybe_get(content, "summary_source")
        if content_summary_source:
            overview_rows.append(
                ["content_summary_source", str(content_summary_source)]
            )

        # classification group info
        classification_group = getattr(content_analysis, "classification_group", None)
        if classification_group and getattr(classification_group, "name", None):
            overview_rows.append(
                ["classification_group", getattr(classification_group, "name")]
            )
        if classification_group and getattr(
            classification_group, "classifications", None
        ):
            group_names = [c.name for c in classification_group.classifications]
            overview_rows.append(["classification_names", ", ".join(group_names)])

        # models used
        model_keys = []
        for m in getattr(content_analysis, "models", []) or []:
            try:
                model_keys.append(getattr(m, "name", str(m)))
            except (AttributeError, TypeError):
                model_keys.append(str(m))
        overview_rows.append(["models", ", ".join(model_keys)])

        # optional: analysis summary/notes
        summary = getattr(content_analysis, "summary", None) or getattr(
            content_analysis, "analysis_summary", None
        )
        if summary:
            overview_rows.append(["analysis_summary", str(summary)])

        for r in overview_rows:
            ws_overview.append(r)

        # 2b) Get comments and discover model keys + class names
        comments = getattr(content_analysis, "comments", []) or []

        all_model_keys: set[str] = set()
        all_class_names: set[str] = set()
        for comment in comments:
            labels_by_model: Dict[str, Dict[str, Label]] = (
                getattr(comment, "labels", {}) or {}
            )
            for model_key, clf_dict in labels_by_model.items():
                all_model_keys.add(model_key)
                for class_name in clf_dict.keys():
                    all_class_names.add(class_name)

        # canonical ordering for classes
        if classification_group and getattr(
            classification_group, "classifications", None
        ):
            group_names = [clf.name for clf in classification_group.classifications]
            extras = sorted(all_class_names - set(group_names))
            ordered_class_names: List[str] = group_names + extras
        else:
            ordered_class_names = sorted(all_class_names)

        ordered_model_keys: List[str] = sorted(all_model_keys)

        # 3) Build headers for Comments sheet
        headers: List[str] = [
            "platform",
            "content_id",
            "content_title",
            "comment_id",
            "author",
            "like_count",
            "reply_count",
            "published_at",
            "text",
        ]

        # Classification columns grouped by classification name first, then model
        model_class_headers: List[str] = []
        for class_name in ordered_class_names:
            for model_key in ordered_model_keys:
                model_class_headers.append(f"{class_name} [{model_key}] value")
                model_class_headers.append(f"{class_name} [{model_key}] explanation")

        headers.extend(model_class_headers)

        # Build a top-row that indicates which model produced each classification column.
        # Core comment columns remain empty; classification columns contain the model key.
        core_len = 9  # number of core columns: platform..text
        model_top_row: List[str] = [""] * core_len
        for class_name in ordered_class_names:
            for model_key in ordered_model_keys:
                # two columns per (class, model): value + explanation
                model_top_row.append(model_key)
                model_top_row.append(model_key)

        # Write model row first, then the human-readable headers row
        ws_comments.append(model_top_row)
        ws_comments.append(headers)

        # 4) Write rows for each comment
        for comment in comments:
            row: List[Any] = []
            row.extend([platform_str, content_id, title])

            comment_id = getattr(comment, "comment_id", "")
            author = getattr(comment, "author", "")
            like_count = getattr(comment, "like_count", None)
            reply_count = getattr(comment, "reply_count", None)
            published_at = getattr(comment, "published_at", None)
            text = getattr(comment, "text", "")

            row.extend(
                [comment_id, author, like_count, reply_count, published_at, text]
            )

            labels_by_model: Dict[str, Dict[str, Label]] = (
                getattr(comment, "labels", {}) or {}
            )

            for class_name in ordered_class_names:
                for model_key in ordered_model_keys:
                    clf_dict = labels_by_model.get(model_key, {}) or {}
                    label_obj = clf_dict.get(class_name)

                    if label_obj is None:
                        row.append("")
                        row.append("")
                        continue

                    value = getattr(label_obj, "value", None)
                    if hasattr(value, "value"):
                        value = value.value
                    value_str = "" if value is None else str(value)

                    explanation = getattr(label_obj, "explanation", None)
                    explanation_str = "" if explanation is None else str(explanation)

                    row.append(value_str)
                    row.append(explanation_str)

            ws_comments.append(row)

        # 5) Auto-size columns a bit on both sheets
        for ws in (ws_overview, ws_comments):
            for column_cells in ws.columns:
                try:
                    max_length = 0
                    column_letter = column_cells[0].column_letter
                    for cell in column_cells:
                        cell_value = str(cell.value) if cell.value is not None else ""
                        max_length = max(max_length, len(cell_value))
                    ws.column_dimensions[column_letter].width = min(max_length + 2, 80)
                except (IndexError, TypeError, AttributeError):
                    # best-effort sizing; ignore failures such as empty columns
                    pass

        # 6) Save workbook
        try:
            wb.save(export_path)
            # mark success on the domain object
            content_analysis.export_status = TaskStatusEnum.DONE

            return export_path
        except Exception:
            # mark failure and re-raise so callers know
            content_analysis.export_status = TaskStatusEnum.ERROR


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

##################################################################

def main():
    # Quick local self-test: create a ContentAnalysis with two comments and run export
    content_item = ContentItem(
        content_id="vid123",
        platform=PlatformEnum.YOUTUBE,
        url="https://youtu.be/vid123",
        title="Sample video: Taiwan praise",
        author="channel_xyz",
        description="Short description",
        summary="AI: Taiwan praised for hospitality and safety.",
        summary_source="ai",
        published_at=datetime.now().isoformat(),
        view_count=12345,
        like_count=1200,
        comment_count=2,
    )

    c1 = Comment(
        comment_id="c1",
        content_id=content_item.content_id,
        author="alice",
        text="I love Taiwan — such a friendly place!",
        published_at=datetime.now().isoformat(),
        like_count=5,
        reply_count=0,
    )
    c1.labels = {
        "gpt-4": {
            "pro_taiwan": Label(
                value="pro_taiwan", explanation="Explicit praise for Taiwan"
            )
        }
    }

    c2 = Comment(
        comment_id="c2",
        content_id=content_item.content_id,
        author="bob",
        text="I prefer other places, but Taiwan seems nice.",
        published_at=datetime.now().isoformat(),
        like_count=2,
        reply_count=1,
    )
    c2.labels = {
        "gpt-4": {
            "pro_taiwan": Label(
                value="neutral", explanation="Not strongly positive nor negative"
            )
        },
        "llama-2": {
            "pro_taiwan": Label(
                value="pro_taiwan", explanation="Supports Taiwan in a mild way"
            )
        },
    }

    ca = ContentAnalysis(content=content_item)
    ca.comments = [c1, c2]
    ca.models = ["gpt-4", "llama-2"]

    svc = ExportService()
    out = svc.export_to_xlsx(ca)
    print(f"Exported to: {out}")


if __name__ == "__main__":
    main()

# python -m services.export_service
