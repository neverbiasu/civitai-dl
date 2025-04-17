import gradio as gr
import json
import logging
from typing import Dict, List, Any, Tuple, Optional

from ...core.filter import FilterManager, FilterParser, FilterCondition

# 配置日志
logger = logging.getLogger(__name__)

# 创建过滤管理器实例
filter_manager = FilterManager()

class FilterBuilder:
    """筛选条件构建器组件"""
    
    def __init__(self):
        """初始化筛选构建器"""
        self.templates = filter_manager.list_templates()
        self.operators = [
            "等于 (=)", "不等于 (!=)", "大于 (>)", "大于等于 (>=)",
            "小于 (<)", "小于等于 (<=)", "包含", "以...开头", "以...结尾",
            "匹配正则表达式"
        ]
        self.op_map = {
            "等于 (=)": "eq",
            "不等于 (!=)": "ne",
            "大于 (>)": "gt",
            "大于等于 (>=)": "ge",
            "小于 (<)": "lt",
            "小于等于 (<=)": "le",
            "包含": "contains",
            "以...开头": "startswith",
            "以...结尾": "endswith",
            "匹配正则表达式": "regex",
        }
        self.common_fields = [
            "name", "type", "creator.username", "tags", 
            "modelVersions.baseModel", "stats.rating", 
            "stats.downloadCount", "publishedAt"
        ]
        
        # 存储当前条件列表和最终筛选条件
        self.current_conditions = []
        self.final_filter = {}
        
    def create_ui(self) -> Tuple:
        """创建筛选条件构建器UI
        
        Returns:
            (筛选构建区, 结果输出, 应用按钮, 保存按钮, 加载按钮)
        """
        with gr.Accordion("高级筛选条件构建器", open=False) as filter_accordion:
            with gr.Tabs() as filter_tabs:
                with gr.TabItem("简单条件"):
                    with gr.Row():
                        with gr.Column(scale=1):
                            field = gr.Dropdown(
                                choices=self.common_fields,
                                label="字段",
                                info="选择要筛选的字段"
                            )
                            custom_field = gr.Textbox(
                                label="自定义字段",
                                placeholder="例如: stats.favoriteCount"
                            )
                        
                        with gr.Column(scale=1):
                            operator = gr.Dropdown(
                                choices=self.operators,
                                label="操作符",
                                info="选择筛选条件的操作符"
                            )
                        
                        with gr.Column(scale=1):
                            value = gr.Textbox(
                                label="值",
                                placeholder="例如: LORA"
                            )
                    
                    with gr.Row():
                        add_btn = gr.Button("添加条件", variant="primary")
                
                with gr.TabItem("复合条件"):
                    condition_list = gr.Textbox(
                        label="当前条件列表",
                        placeholder="还没有条件",
                        info="当前添加的所有条件",
                        lines=5,
                        interactive=False
                    )
                    
                    with gr.Row():
                        logic_op = gr.Radio(
                            choices=["AND (所有条件都满足)", "OR (任一条件满足)"],
                            label="条件之间的逻辑关系",
                            value="AND (所有条件都满足)"
                        )
                        
                    with gr.Row():
                        clear_btn = gr.Button("清空条件")
                        apply_logic_btn = gr.Button("应用逻辑关系", variant="primary")
                
                with gr.TabItem("JSON编辑"):
                    json_input = gr.Textbox(
                        label="JSON格式的筛选条件",
                        placeholder='例如: {"field": "type", "op": "eq", "value": "LORA"}',
                        info="直接编辑JSON格式的筛选条件",
                        lines=10
                    )
                    
                    with gr.Row():
                        validate_json_btn = gr.Button("验证JSON", variant="secondary")
                        load_json_btn = gr.Button("加载JSON", variant="primary")
                
                with gr.TabItem("模板"):
                    template_dropdown = gr.Dropdown(
                        choices=list(self.templates.keys()),
                        label="选择模板",
                        info="选择一个保存的筛选模板"
                    )
                    
                    with gr.Row():
                        load_template_btn = gr.Button("加载模板", variant="primary")
                        delete_template_btn = gr.Button("删除模板", variant="stop")
                    
                    with gr.Row():
                        template_name = gr.Textbox(
                            label="新模板名称",
                            placeholder="例如: 高质量LORA"
                        )
                        save_template_btn = gr.Button("保存当前条件为模板", variant="secondary")
            
            # 当前筛选条件显示区域
            current_filter = gr.Textbox(
                label="当前筛选条件",
                placeholder="还没有设置筛选条件",
                info="这是当前将被应用的筛选条件",
                lines=5,
                interactive=False
            )
            
            # 预览结果区域
            preview_result = gr.Textbox(
                label="预览效果",
                placeholder="点击'预览效果'按钮查看筛选结果",
                interactive=False
            )
            
            with gr.Row():
                preview_btn = gr.Button("预览效果")
                apply_btn = gr.Button("应用筛选条件", variant="primary")
                reset_btn = gr.Button("重置", variant="stop")
        
        # 返回需要外部访问的组件
        return filter_accordion, current_filter, apply_btn, save_template_btn, load_template_btn
    
    def setup_callbacks(self, components: Tuple, api, on_preview=None, on_apply=None) -> None:
        """设置组件的回调函数
        
        Args:
            components: 从create_ui返回的组件元组
            api: API客户端实例
            on_preview: 预览回调函数
            on_apply: 应用筛选条件回调函数
        """
        filter_accordion, current_filter, apply_btn, save_template_btn, load_template_btn = components
        
        # 获取其他需要绑定的组件
        tabs = filter_accordion.children[0]
        simple_tab = tabs.children[0]
        compound_tab = tabs.children[1]
        json_tab = tabs.children[2]
        template_tab = tabs.children[3]
        
        # 简单条件标签页内的组件
        field = simple_tab.children[0].children[0].children[0]
        custom_field = simple_tab.children[0].children[0].children[1]
        operator = simple_tab.children[0].children[1].children[0]
        value = simple_tab.children[0].children[2].children[0]
        add_btn = simple_tab.children[1].children[0]
        
        # 复合条件标签页内的组件
        condition_list = compound_tab.children[0]
        logic_op = compound_tab.children[1].children[0]
        clear_btn = compound_tab.children[2].children[0]
        apply_logic_btn = compound_tab.children[2].children[1]
        
        # JSON编辑标签页内的组件
        json_input = json_tab.children[0]
        validate_json_btn = json_tab.children[1].children[0]
        load_json_btn = json_tab.children[1].children[1]
        
        # 模板标签页内的组件
        template_dropdown = template_tab.children[0]
        load_template_btn = template_tab.children[1].children[0]
        delete_template_btn = template_tab.children[1].children[1]
        template_name = template_tab.children[2].children[0]
        save_template_btn = template_tab.children[2].children[1]
        
        # 底部操作区内的组件
        preview_result = filter_accordion.children[2]
        preview_btn = filter_accordion.children[3].children[0]
        reset_btn = filter_accordion.children[3].children[2]
        
        # 添加简单条件回调
        def on_add_condition():
            field_value = custom_field.value if custom_field.value else field.value
            op_value = self.op_map.get(operator.value, "eq")
            
            # 转换值类型（尝试转为数字）
            try:
                if value.value.isdigit():
                    val = int(value.value)
                elif value.value.replace(".", "", 1).isdigit() and value.value.count(".") <= 1:
                    val = float(value.value)
                else:
                    val = value.value
            except (ValueError, AttributeError):
                val = value.value
            
            # 创建条件
            condition = {
                "field": field_value,
                "op": op_value,
                "value": val
            }
            
            # 添加到条件列表
            self.current_conditions.append(condition)
            
            # 更新显示
            condition_desc = self._format_conditions(self.current_conditions)
            
            # 清空输入框
            return condition_desc, "", "", ""
        
        add_btn.click(
            fn=on_add_condition,
            inputs=[],
            outputs=[condition_list, custom_field, field, value]
        )
        
        # 清空条件回调
        def on_clear_conditions():
            self.current_conditions = []
            self.final_filter = {}
            return "", self._format_filter(self.final_filter)
        
        clear_btn.click(
            fn=on_clear_conditions,
            inputs=[],
            outputs=[condition_list, current_filter]
        )
        
        # 应用逻辑关系回调
        def on_apply_logic():
            if not self.current_conditions:
                return "还没有条件", "{}"
            
            # 确定逻辑操作符
            logic = "and" if logic_op.value.startswith("AND") else "or"
            
            # 创建筛选条件
            if len(self.current_conditions) == 1:
                self.final_filter = self.current_conditions[0]
            else:
                self.final_filter = {logic: self.current_conditions}
            
            # 格式化显示
            return self._format_conditions(self.current_conditions), self._format_filter(self.final_filter)
        
        apply_logic_btn.click(
            fn=on_apply_logic,
            inputs=[],
            outputs=[condition_list, current_filter]
        )
        
        # 验证JSON回调
        def on_validate_json():
            try:
                json_data = json.loads(json_input.value)
                FilterCondition(json_data)  # 验证格式
                return "JSON格式有效✅"
            except Exception as e:
                return f"JSON格式无效❌: {str(e)}"
        
        validate_json_btn.click(
            fn=on_validate_json,
            inputs=[],
            outputs=[preview_result]
        )
        
        # 加载JSON回调
        def on_load_json():
            try:
                json_data = json.loads(json_input.value)
                FilterCondition(json_data)  # 验证格式
                self.final_filter = json_data
                return self._format_filter(self.final_filter)
            except Exception as e:
                return f"加载JSON失败: {str(e)}"
        
        load_json_btn.click(
            fn=on_load_json,
            inputs=[],
            outputs=[current_filter]
        )
        
        # 加载模板回调
        def on_load_template():
            template_name = template_dropdown.value
            if not template_name:
                return "请先选择一个模板", current_filter.value
            
            template = filter_manager.get_template(template_name)
            if not template:
                return f"模板 '{template_name}' 不存在", current_filter.value
            
            self.final_filter = template
            return f"已加载模板: {template_name}✅", self._format_filter(self.final_filter)
        
        load_template_btn.click(
            fn=on_load_template,
            inputs=[],
            outputs=[preview_result, current_filter]
        )
        
        # 删除模板回调
        def on_delete_template():
            template_name = template_dropdown.value
            if not template_name:
                return "请先选择一个模板", list(filter_manager.list_templates().keys())
            
            success = filter_manager.remove_template(template_name)
            self.templates = filter_manager.list_templates()
            
            if success:
                return f"模板 '{template_name}' 已删除✅", list(self.templates.keys())
            else:
                return f"删除模板 '{template_name}' 失败❌", list(self.templates.keys())
        
        delete_template_btn.click(
            fn=on_delete_template,
            inputs=[],
            outputs=[preview_result, template_dropdown]
        )
        
        # 保存模板回调
        def on_save_template():
            if not template_name.value:
                return "请输入模板名称"
            
            if not self.final_filter:
                return "请先创建筛选条件"
            
            success = filter_manager.add_template(template_name.value, self.final_filter)
            self.templates = filter_manager.list_templates()
            
            if success:
                return f"模板 '{template_name.value}' 保存成功✅", "", list(self.templates.keys())
            else:
                return f"保存模板失败❌", template_name.value, list(self.templates.keys())
        
        save_template_btn.click(
            fn=on_save_template,
            inputs=[],
            outputs=[preview_result, template_name, template_dropdown]
        )
        
        # 预览效果回调
        def on_preview_filter():
            if not self.final_filter:
                return "请先创建筛选条件"
            
            # 如果提供了自定义预览回调，则使用它
            if on_preview:
                return on_preview(self.final_filter)
            
            # 否则执行默认预览
            try:
                # 将筛选条件转换为API参数
                api_params = FilterParser.to_api_params(self.final_filter)
                api_params["limit"] = 1  # 只取一条进行预览
                
                # 调用API
                response = api.get_models(api_params)
                count = response.get("metadata", {}).get("totalItems", 0)
                
                # 返回结果预览
                return f"符合条件的模型数量: {count}"
            except Exception as e:
                return f"预览失败: {str(e)}"
        
        preview_btn.click(
            fn=on_preview_filter,
            inputs=[],
            outputs=[preview_result]
        )
        
        # 重置回调
        def on_reset():
            self.current_conditions = []
            self.final_filter = {}
            return "", "", "", "", "", "{}"
        
        reset_btn.click(
            fn=on_reset,
            inputs=[],
            outputs=[field, custom_field, value, condition_list, preview_result, current_filter]
        )
        
        # 应用筛选条件回调
        if on_apply:
            apply_btn.click(
                fn=lambda: on_apply(self.final_filter),
                inputs=[],
                outputs=[]
            )
    
    def _format_conditions(self, conditions: List[Dict[str, Any]]) -> str:
        """格式化条件列表为可读字符串
        
        Args:
            conditions: 条件列表
            
        Returns:
            格式化后的字符串
        """
        if not conditions:
            return "还没有条件"
        
        # 反向映射操作符
        rev_op_map = {v: k for k, v in self.op_map.items()}
        
        result = []
        for i, cond in enumerate(conditions):
            field = cond.get("field", "")
            op = rev_op_map.get(cond.get("op", "eq"), "=")
            value = cond.get("value", "")
            
            result.append(f"{i+1}. {field} {op} {value}")
        
        return "\n".join(result)
    
    def _format_filter(self, filter_condition: Dict[str, Any]) -> str:
        """格式化筛选条件为JSON字符串
        
        Args:
            filter_condition: 筛选条件字典
            
        Returns:
            格式化的JSON字符串
        """
        if not filter_condition:
            return "{}"
        
        try:
            return json.dumps(filter_condition, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"格式化筛选条件失败: {str(e)}")
            return "{}"
    
    def get_filter(self) -> Dict[str, Any]:
        """获取当前设置的筛选条件
        
        Returns:
            筛选条件字典
        """
        return self.final_filter
