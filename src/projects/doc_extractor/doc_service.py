from __future__ import annotations

from pathlib import Path
from typing import Any, Dict, Optional

# Your core doc extractor pipeline
from src.projects.doc_extractor.doc_extractor import process as core_process


class DocumentExtractorService:
    """
    Thin wrapper around the existing `doc_extractor` package, with a stable
    return schema and optional memory/LLM hooks via the orchestrator.

    For now we:
      - Call doc_extractor.process(file_path) to get a base result.
      - Normalize keys and types.
      - Add a full_text field when possible.
      - Optionally record a memory via `brain.remember(...)`.
    """

    def __init__(
        self,
        model_client: Any,
        brain: Optional[Any] = None,
        logger: Optional[Any] = None,
    ) -> None:
        self.model_client = model_client
        self.brain = brain
        self.logger = logger

    def llm_classify_and_extract(self, file_path: str) -> Dict[str, Any]:
        """
        Run the document extractor pipeline and return a dict with keys:
          - document_type: str
          - classification_confidence: float (0.0–1.0)
          - extracted_fields: dict
          - text_snippet: str
          - full_text: str
        """
        path_str = str(file_path)
        base_result: Dict[str, Any] = {}
        full_text: str = ""
        text_snippet: str = ""

        try:
            # Use the existing doc_extractor package as the core pipeline.
            base_result = core_process(path_str) or {}

        except Exception as e:
            # If doc_extractor fails entirely, fall back to a safe default.
            if self.logger:
                self.logger.exception("doc_extractor.process failed for %s: %s", path_str, e)

            text_snippet = ""
            full_text = ""

            result = {
                "document_type": "unknown",
                "classification_confidence": 0.0,
                "extracted_fields": {},
                "text_snippet": text_snippet,
                "full_text": full_text,
            }

            # Optionally remember the failure
            if self.brain:
                try:
                    self.brain.remember(
                        mode="doc-extract",
                        goal=f"Process document {Path(path_str).name}",
                        target_path=path_str,
                        status="failed",
                        summary=f"doc_extractor.process failed: {e}",
                        metadata={},
                    )
                except Exception:
                    if self.logger:
                        self.logger.debug(
                            "Failed to store failure memory for doc-extract.",
                            exc_info=True,
                        )
            return result

        # ------------------------------
        # Normalize the base_result dict
        # ------------------------------
        doc_type = base_result.get("document_type", "unknown")

        try:
            confidence = float(base_result.get("classification_confidence", 0.0) or 0.0)
        except (TypeError, ValueError):
            confidence = 0.0

        extracted_fields = base_result.get("extracted_fields") or {}
        if not isinstance(extracted_fields, dict):
            extracted_fields = {}

        text_snippet = base_result.get("text_snippet") or ""

        # Try a few common keys for full text, then fall back to snippet
        full_text = (
            base_result.get("text")
            or base_result.get("full_text")
            or base_result.get("raw_text")
            or text_snippet
        )

        result: Dict[str, Any] = {
            "document_type": doc_type,
            "classification_confidence": confidence,
            "extracted_fields": extracted_fields,
            "text_snippet": text_snippet,
            "full_text": full_text,
        }

        # Optionally record a success memory
        if self.brain:
            try:
                self.brain.remember(
                    mode="doc-extract",
                    goal=f"Process document {Path(path_str).name}",
                    target_path=path_str,
                    status="success",
                    summary=f"doc_extractor classified as {doc_type}",
                    metadata={"confidence": confidence},
                )
            except Exception:
                if self.logger:
                    self.logger.debug(
                        "Failed to store success memory for doc-extract.",
                        exc_info=True,
                    )

        return result
