"""Filter builder component for the Civitai Downloader WebUI.

This module provides a UI component for building complex filter conditions
in the web interface with interactive controls.
"""

from typing import Dict, Any, List, Tuple, Callable, Optional

import gradio as gr

from civitai_dl.api.client import CivitaiAPI
from civitai_dl.core.filter import FilterManager
from civitai_dl.utils.logger import get_logger

logger = get_logger(__name__)


class FilterBuilder:
    """Interactive filter builder component for the web UI.

    Provides UI elements and logic for creating, saving, and loading complex
    filter conditions for searching models.
    """

    def __init__(self) -> None:
        """Initialize the filter builder with a filter manager."""
        self.filter_manager = FilterManager()
        self.templates = self.filter_manager.list_templates()
        self.current_condition: Dict[str, Any] = {}
        self.temp_conditions: List[Dict[str, Any]] = []

    def create_ui(self) -> Tuple[gr.Accordion, gr.JSON, gr.Button, gr.Button, gr.Button]:
        """Create the filter builder UI components.

        Returns:
            Tuple containing:
            - filter_accordion: Main accordion container
            - current_filter: JSON component for the current filter
            - apply_filter_btn: Button to apply the filter
            - save_template_btn: Button to save the current filter as a template
            - load_template_btn: Button to load a template
        """
        with gr.Accordion("高级筛选", open=False) as filter_accordion:
            with gr.Row():
                with gr.Column(scale=1):
                    # Field selection components
                    field_dropdown = gr.Dropdown(
                        choices=[
                            "name", "type", "creator.username", "tags",
                            "modelVersions.baseModel", "stats.rating",
                            "stats.downloadCount", "stats.favoriteCount",
                            "publishedAt", "updatedAt"
                        ],
                        label="字段",
                        value="name"
                    )  # noqa: F841

                    operator_dropdown = gr.Dropdown(
                        choices=[
                            "eq (equals)", "ne (not equals)",
                            "gt (greater than)", "ge (greater or equal)",
                            "lt (less than)", "le (less or equal)",
                            "contains (contains)", "startswith (starts with)",
                            "endswith (ends with)", "regex (regex match)"
                        ],
                        label="Operator",
                        value="contains (contains)"
                    )

                    value_input = gr.Textbox(label="Value")

                    logic_radio = gr.Radio(
                        choices=["AND", "OR"],
                        label="Logic Operator",
                        value="AND"
                    )

                    add_condition_btn = gr.Button("Add Condition")

                    # Template management
                    template_name = gr.Textbox(label="Template Name")

                    template_list = gr.Dropdown(
                        choices=list(self.templates.keys()),
                        label="Load Template"
                    )

                    with gr.Row():
                        save_template_btn = gr.Button("Save Template")
                        load_template_btn = gr.Button("Load Template")

                with gr.Column(scale=1):
                    # Current filter display
                    current_filter = gr.JSON(
                        label="Current Filter",
                        value={}
                    )

                    conditions_list = gr.Dataframe(
                        headers=["Field", "Operator", "Value"],
                        label="Current Conditions",
                        interactive=False,
                        value=[]
                    )

                    preview_output = gr.Textbox(
                        label="Preview",
                        interactive=False
                    )

                    with gr.Row():
                        clear_btn = gr.Button("Clear Filter")
                        preview_btn = gr.Button("Preview Results")

                    apply_filter_btn = gr.Button("Apply Filter", variant="primary")

        return filter_accordion, current_filter, apply_filter_btn, save_template_btn, load_template_btn

    def setup_callbacks(
        self,
        components: Tuple[gr.Accordion, gr.JSON, gr.Button, gr.Button, gr.Button],
        api: CivitaiAPI,
        on_preview: Optional[Callable[[Dict[str, Any]], str]] = None,
        on_apply: Optional[Callable[[Dict[str, Any]], Any]] = None
    ) -> None:
        """Set up the callbacks for the filter builder components.

        Args:
            components: UI components returned by create_ui()
            api: API client for previewing filter results
            on_preview: Callback function for filter preview
            on_apply: Callback function for applying the filter
        """
        filter_accordion, current_filter, apply_filter_btn, save_template_btn, load_template_btn = components

        # 修复 F841: 标记未使用变量或将其删除
        # Find components within the accordion
        add_condition_btn = None
        clear_btn = None
        preview_btn = None
        preview_output_element = None  # Renamed to avoid conflict
        
        # Extract components from accordion
        try:
            for component in filter_accordion.children:
                if isinstance(component, gr.Row):
                    for col in component.children:
                        if isinstance(col, gr.Column):
                            for elem in col.children:
                                if isinstance(elem, gr.Button) and elem.value == "Add Condition":
                                    add_condition_btn = elem
                                elif isinstance(elem, gr.Button) and elem.value == "Clear Filter":
                                    clear_btn = elem
                                elif isinstance(elem, gr.Button) and elem.value == "Preview Results":
                                    preview_btn = elem
                                elif isinstance(elem, gr.Textbox) and elem.label == "Preview":
                                    preview_output_element = elem
                                
                                # 其他组件的定位代码不需要赋值给变量，注释掉以避免未使用变量警告
                                # 或者可以将不再需要的定位代码完全删除
        except Exception as e:
            logger.error(f"Failed to extract components from accordion: {e}")

        # Define callback functions
        def add_condition(field: str, operator: str, value: str,
                          conditions: List[List[str]]) -> Tuple[List[List[str]], Dict[str, Any]]:
            """Add a condition to the filter.

            Args:
                field: Field name
                operator: Operator string (includes display text)
                value: Value to filter by
                conditions: Current conditions table

            Returns:
                Updated conditions table and filter JSON
            """
            # Extract operator code from the display string
            op_code = operator.split(" ")[0]

            # Handle value type conversion
            if value.isdigit():
                value = int(value)
            elif value.replace(".", "", 1).isdigit() and value.count(".") <= 1:
                value = float(value)

            # Add to temporary conditions
            self.temp_conditions.append({
                "field": field,
                "op": op_code,
                "value": value
            })

            # Update UI table
            new_conditions = conditions.copy() if conditions else []
            new_conditions.append([field, op_code, str(value)])

            # Update the current filter JSON
            if len(self.temp_conditions) > 1:
                # Use the first condition's logic operator (default to AND)
                logic = "and"  # Default
                self.current_condition = {logic: self.temp_conditions}
            else:
                # Just one condition
                self.current_condition = self.temp_conditions[0]

            return new_conditions, self.current_condition

        def clear_filter() -> Tuple[List[List[str]], Dict[str, Any]]:
            """Clear the current filter and conditions.

            Returns:
                Empty conditions table and filter JSON
            """
            self.temp_conditions = []
            self.current_condition = {}
            return [], {}

        def save_template(name: str, filter_json: Dict[str, Any]) -> gr.Dropdown:
            """Save the current filter as a template.

            Args:
                name: Template name
                filter_json: Filter condition to save

            Returns:
                Updated template dropdown
            """
            if not name or not filter_json:
                return gr.Dropdown(choices=list(self.templates.keys()))

            # Save the template
            self.filter_manager.add_template(name, filter_json)

            # Reload templates
            self.templates = self.filter_manager.list_templates()

            # Return updated dropdown
            return gr.Dropdown(choices=list(self.templates.keys()))

        def load_template(name: str) -> Tuple[Dict[str, Any], List[List[str]]]:
            """Load a template as the current filter.

            Args:
                name: Template name to load

            Returns:
                Loaded filter JSON and updated conditions table
            """
            if not name or name not in self.templates:
                return {}, []

            template = self.filter_manager.get_template(name)
            self.current_condition = template

            # Convert to UI table format
            table_data = []

            # Extract conditions from filter
            conditions = []
            if "field" in template:
                # Single condition
                conditions = [template]
            elif "and" in template:
                conditions = template["and"]
            elif "or" in template:
                conditions = template["or"]

            # Update temp conditions
            self.temp_conditions = conditions

            # Build table data
            for condition in conditions:
                table_data.append([
                    condition.get("field", ""),
                    condition.get("op", ""),
                    str(condition.get("value", ""))
                ])

            return template, table_data

        # Connect callbacks in a single try-except block
        try:
            # Add condition button callback
            if add_condition_btn and field_dropdown and operator_dropdown and value_input and conditions_list:
                add_condition_btn.click(
                    fn=add_condition,
                    inputs=[field_dropdown, operator_dropdown, value_input, conditions_list],
                    outputs=[conditions_list, current_filter]
                )

            # Clear button callback
            if clear_btn:
                clear_btn.click(
                    fn=clear_filter,
                    inputs=[],
                    outputs=[conditions_list, current_filter]
                )

            # Save template button callback
            if save_template_btn and template_name:
                save_template_btn.click(
                    fn=save_template,
                    inputs=[template_name, current_filter],
                    outputs=[template_list]
                )

            # Load template button callback
            if load_template_btn and template_list:
                load_template_btn.click(
                    fn=load_template,
                    inputs=[template_list],
                    outputs=[current_filter, conditions_list]
                )

            # Connect external callbacks
            if on_preview and preview_btn and preview_output:
                preview_btn.click(
                    fn=on_preview,
                    inputs=[current_filter],
                    outputs=[preview_output]
                )

            if on_apply and apply_filter_btn and current_filter:
                apply_filter_btn.click(
                    fn=on_apply,
                    inputs=[current_filter],
                    outputs=[]
                )
        except Exception as e:
            logger.error(f"Failed to set up filter callbacks: {e}")
