from dataclasses import dataclass, field
from typing import List, Optional
from models.view_models.prompt_template.prompt_template_detail_view_model import PromptTemplateDetailViewModel

@dataclass
class PromptTemplateViewModel:
    """
    Full state for the Prompt Template view.
    """
    # Platform selection
    platform_choices: List[str] = field(default_factory=list)
    selected_platform: str = ""
    
    # Template selection
    template_name_choices: List[str] = field(default_factory=list)
    
    # The currently selected template details.
    selected_template: Optional[PromptTemplateDetailViewModel] = None

    # Page-level messages
    info_message: Optional[str] = None
    error_message: Optional[str] = None
