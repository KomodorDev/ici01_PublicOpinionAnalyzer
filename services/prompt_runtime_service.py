"""
prompt_runtime_service.py
=========================

This module provides the `PromptRuntimeService`, which is responsible for
building the actual system/user prompts that get sent to the LLM during comment
analysis.

Key design points:
- The service is stateless except for **one cached base prompt pair** that is
  created on the first `create_prompt(...)` call.
- The base prompts contain classification descriptions, expected output format,
  and content-level metadata (title, summary).
- Comment-specific placeholders (TARGETCOMMENT, THREADCOMMENTS, TAGGEDCOMMENTS)
  are applied on top of the cached base prompts on every call.

This avoids recalculating expensive classification/outputformat blocks for
every comment and ensures consistent prompts across a single analysis run.
"""

from typing import List, Dict, Tuple, Any
import re

from enums import PlatformEnum, PlaceholderEnum
from services import ClassificationService
from models.domain import ContentAnalysis, Comment


##################################################################
class PromptRuntimeService:
    """
    Builds LLM prompts for comment classification.

    This class creates two kinds of prompt content:

    1. Base prompts (system + user):
       - Includes classification instructions and JSON output format.
       - Includes video/content metadata (title, summary).
       - These are computed **once** and cached for the lifetime of this
         PromptRuntimeService instance.

    2. Comment-specific prompts:
       - Includes the actual comment text.
       - Includes optional thread or tagged comment context.
       - These are applied on top of the cached base prompts for each call.

    The constructor requires only a `ClassificationService`. Everything else is
    provided per call via a `ContentAnalysis` (content/video metadata +
    template) and a `Comment`.

    This design keeps prompt construction fast, predictable, and consistent
    while avoiding repeated classification/group formatting work.
    """

    # pattern matches [PLACEHOLDER]
    placeholder_pattern = re.compile(r"\[([A-Z0-9_]+)\]")

    # ----------------------------------------------------------------
    def __init__(self, classification_service: ClassificationService):
        """
        PromptRuntimeService is bound to a single classification_service
        and caches exactly ONE base prompt pair (system/user) over its lifetime.

        The first call to create_prompt(...) initializes the cache based on
        the given ContentAnalysis. Subsequent calls reuse that base and only
        inject comment-specific placeholders.
        """
        self.classification_service = classification_service

        # One cache for base prompts; we only ever store "system" + "user" once.
        self.cache: dict[str, Any] = {}


    # ================================================================
    # Prompt Creation (Core Functionality)
    # ================================================================
    # ----------------------------------------------------------------
    def create_prompt(
        self,
        content_analysis: ContentAnalysis,
        comment: Comment,
    ) -> Tuple[str, str]:
        """
        Create a complete prompt ready for the LLM using cached data.

        The first call initializes the base system/user prompts for this
        PromptRuntimeService instance (classification info, output format,
        content metadata). Later calls reuse that base and only fill in
        TARGETCOMMENT / THREADCOMMENTS / TAGGEDCOMMENTS.

        Args:
            content_analysis: ContentAnalysis for this video/post
            comment: Comment object to generate prompt for

        Returns:
            Tuple of (system_prompt, user_prompt)
        """
        # 1) Initialize cache on first use --------------------------------
        if "base_system" not in self.cache or "base_user" not in self.cache:
            self._initialize_base_prompts(content_analysis)

        base_system: str = self.cache["base_system"]
        base_user: str = self.cache["base_user"]

        # 2) Build comment-specific variables -----------------------------
        # NOTE: use PlaceholderEnum so we don't hardcode strings
        comment_vars: Dict[str, Any] = {
            PlaceholderEnum.TARGETCOMMENT.value: comment.text,
            PlaceholderEnum.THREADCOMMENTS.value: getattr(comment, "thread_comments", "") or "",
            PlaceholderEnum.TAGGEDCOMMENTS.value: getattr(comment, "tagged_comments", "") or "",
        }

        # 3) Apply comment placeholders on top of the base prompts --------
        system_prompt = self._substitute_variables(base_system, comment_vars)
        user_prompt = self._substitute_variables(base_user, comment_vars)

        return system_prompt, user_prompt

    # ================================================================
    # Internal helpers
    # ================================================================
    def _initialize_base_prompts(self, content_analysis: ContentAnalysis) -> None:
        """
        Build and cache the base system/user prompts for this service instance.

        Base prompts:
        - depend on ContentAnalysis (platform, template, classification_group, content_item)
        - include classification description and [OUTPUTFORMAT]
        - include video metadata (title, summary)
        - DO NOT include comment-specific placeholders (TARGET/THREAD/TAGGED)
        """
        ca = content_analysis

        prompt_template = ca.prompt_template
        content_item = ca.content
        classification_group = ca.classification_group

        # 1) Ask ClassificationService for classification text + OUTPUTFORMAT
        classifications_str = self.classification_service.get_classification_group_string(
            classification_group
        )
        outputformat_hint = self.classification_service.build_outputformat_hint_json(
            classification_group
        )

        # 2) Base variables that are the same for all comments ------------
        base_vars: Dict[str, Any] = {
            PlaceholderEnum.CLASSIFICATIONS.value: classifications_str,
            PlaceholderEnum.OUTPUTFORMAT.value: outputformat_hint,
            PlaceholderEnum.VIDEOTITLE.value: getattr(content_item, "title", ""),
            PlaceholderEnum.VIDEOCONTEXT.value: getattr(content_item, "summary", ""),
        }

        # 3) Apply base vars to system and user templates -----------------
        # We only substitute these four placeholders here.
        system_template = prompt_template.system_prompt
        user_template = prompt_template.user_prompt

        base_system = self._substitute_variables(system_template, base_vars)
        base_user = self._substitute_variables(user_template, base_vars)

        # 4) Cache once for this PromptRuntimeService lifetime ------------
        self.cache["base_system"] = base_system
        self.cache["base_user"] = base_user

    # ================================================================
    # Variable Substitution
    # ================================================================
    # ----------------------------------------------------------------
    def _substitute_variables(self, template: str, variables: Dict[str, Any]) -> str:
        """
        Replace all [PLACEHOLDER] occurrences with the given values.

        Args:
            template: Template string with [PLACEHOLDER] tokens
            variables: Dict mapping placeholder names (without brackets) to values

        Returns:
            Rendered string
        """

        rendered = template

        for key, value in variables.items():
            placeholder = f"[{key}]"
            value_str = "" if value is None else str(value)
            rendered = rendered.replace(placeholder, value_str)

        return rendered

    # ----------------------------------------------------------------
    def detect_placeholders(self, template_text: str) -> List[str]:
        """
        Detect all placeholders in a template.

        Args:
            template_text: Template string

        Returns:
            List of placeholder names (without brackets), e.g. ["VIDEOTITLE", "OUTPUTFORMAT"]
        """
        matches = self.placeholder_pattern.findall(template_text or "")
        # return unique names
        return list(set(matches))

    # ----------------------------------------------------------------

##################################################################
def main():
    """
    Minimal, self-contained test for PromptRuntimeService.

    This does NOT depend on your real repositories. It:
    - creates dummy PromptTemplate / ContentItem / ClassificationGroup / Comment
    - uses a fake ClassificationService with predictable outputs
    - calls create_prompt() twice to demonstrate:
        * base prompts are cached
        * TARGETCOMMENT is substituted per comment
    """

    # --------------------------------------------------------------
    # Dummy helper classes
    # (NOTE: adjust/remove these if you want to use your real models.)
    # --------------------------------------------------------------
    class DummyPromptTemplate:  # pylint: disable=missing-class-docstring
        def __init__(self, system_prompt: str, user_prompt_template: str):
            self.system_prompt = system_prompt
            self.user_prompt_template = user_prompt_template

    class DummyContentItem:     # pylint: disable=missing-class-docstring
        def __init__(self, title: str, summary: str):
            self.title = title
            self.summary = summary

    class DummyClassification:  # pylint: disable=missing-class-docstring
        def __init__(self, name: str, question: str):
            self.name = name
            self.question = question
            # Other fields omitted for this test.

    class DummyClassificationGroup: # pylint: disable=missing-class-docstring
        def __init__(self, name: str, classifications: List[DummyClassification]):
            self.name = name
            self.classifications = classifications

    class DummyContentAnalysis:
        """
        Minimal stand-in for ContentAnalysis.
        NOTE: In your real code, ContentAnalysis likely is a dataclass with
        many more fields. If you want to test with the real one, replace this
        with an actual ContentAnalysis instance and remove this dummy class.
        """
        def __init__(self, platform, content, prompt_template, classification_group):
            self.platform = platform
            self.content = content
            self.prompt_template = prompt_template
            self.classification_group = classification_group

    class DummyComment:
        """
        Minimal stand-in for Comment.
        NOTE: If your real Comment model has different field names,
        adjust this or use the real Comment instead.
        """
        def __init__(self, text: str, thread_comments: str = "", tagged_comments: str = ""):
            self.text = text
            self.thread_comments = thread_comments
            self.tagged_comments = tagged_comments

    # --------------------------------------------------------------
    # Fake ClassificationService for testing PromptRuntimeService
    # --------------------------------------------------------------
    class FakeClassificationService:    # pylint: disable=missing-class-docstring
        def get_classification_group_string(self, group: DummyClassificationGroup) -> str: # pylint: disable=missing-function-docstring
            # Simple human-readable block for testing.
            lines = [f"Classification group: {group.name}", ""]
            for c in group.classifications:
                lines.append(f"- {c.name}: {c.question}")
            return "\n".join(lines)

        def build_outputformat_hint_json(self, group: DummyClassificationGroup) -> str: # pylint: disable=missing-function-docstring
            # Very simple JSON-like hint for testing.
            # In your real ClassificationService this is a real JSON schema/hint.
            return (
                "{\n"
                f'  "{group.name}": {{ "value": "<test-value>", "explanation": "<test-explanation>" }}\n'
                "}"
            )

    # --------------------------------------------------------------
    # Build dummy data for the test
    # --------------------------------------------------------------
    fake_classification_service = FakeClassificationService()
    prompt_service = PromptRuntimeService(classification_service=fake_classification_service)  # type: ignore[arg-type]

    # Dummy classification group
    demo_classifications = [
        DummyClassification(
            name="IsProTaiwan",
            question="Is this comment supportive of Taiwan?"
        ),
        DummyClassification(
            name="Tone",
            question="What is the overall tone of this comment?"
        ),
    ]
    demo_group = DummyClassificationGroup(
        name="DemoGroup",
        classifications=demo_classifications,
    )

    # Dummy content item (video/post)
    demo_content = DummyContentItem(
        title="Demo Video Title",
        summary="This is a short summary of the demo video.",
    )

    # Dummy prompt template that uses the placeholders we support
    system_tpl = (
        "You are a labeling assistant.\n\n"
        "Classifications:\n[CLASSIFICATIONS]\n\n"
        "Output format:\n[OUTPUTFORMAT]\n"
    )
    user_tpl = (
        "Video title: [VIDEOTITLE]\n"
        "Video context: [VIDEOCONTEXT]\n\n"
        "Target comment:\n[TARGETCOMMENT]\n\n"
        "Thread comments:\n[THREADCOMMENTS]\n\n"
        "Tagged comments:\n[TAGGEDCOMMENTS]\n"
    )
    demo_prompt_template = DummyPromptTemplate(system_prompt=system_tpl, user_prompt_template=user_tpl)

    # Dummy ContentAnalysis for the test
    demo_ca = DummyContentAnalysis(
        platform=PlatformEnum.YOUTUBE,  # NOTE: adjust if your enum name differs
        content=demo_content,
        prompt_template=demo_prompt_template,
        classification_group=demo_group,
    )

    # Two different comments to show base reuse and per-comment substitution
    comment1 = DummyComment(
        text="I really love how Taiwan is handling this situation!",
        thread_comments="Previous comment in thread...",
        tagged_comments="@user123 mentioned something similar."
    )
    comment2 = DummyComment(
        text="This video is boring and poorly researched.",
        thread_comments="Earlier: 'Great analysis!'",
        tagged_comments=""
    )

    # --------------------------------------------------------------
    # Run test calls
    # --------------------------------------------------------------
    print("=== First call (initializes base prompts) ===")
    sys1, usr1 = prompt_service.create_prompt(demo_ca, comment1)
    print("\n--- System Prompt ---\n")
    print(sys1)
    print("\n--- User Prompt ---\n")
    print(usr1)

    print("\n\n=== Second call (reuses base, new TARGETCOMMENT etc.) ===")
    sys2, usr2 = prompt_service.create_prompt(demo_ca, comment2)
    print("\n--- System Prompt ---\n")
    print(sys2)
    print("\n--- User Prompt ---\n")
    print(usr2)

    # NOTE:
    # - sys1 and sys2 should be identical (base system prompt cached).
    # - usr1 and usr2 should differ in the [TARGETCOMMENT] / [THREADCOMMENTS] / [TAGGEDCOMMENTS] parts.
    # - All placeholders [CLASSIFICATIONS], [OUTPUTFORMAT], [VIDEOTITLE], [VIDEOCONTEXT]
    #   should be replaced already in both prompts.


if __name__ == "__main__":
    main()

# python -m services.prompt_runtime_service
