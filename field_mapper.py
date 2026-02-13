"""
字段映射模块
将飞书多维表字段映射到TAPD API字段
"""
from typing import Dict, Any, List, Optional, Tuple
from config import get_config, AppConfig


class FieldMapper:
    """字段映射器"""
    
    def __init__(self, config: AppConfig = None):
        self.config = config or get_config()
        self.field_mapping = self.config.field_mapping
        self.workitem_types = self.config.workitem_types
    
    def map_story_fields(self, feishu_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        将飞书字段映射到TAPD需求字段
        
        Args:
            feishu_data: 飞书多维表的记录数据
            
        Returns:
            (tapd_data, image_urls): TAPD API 数据字典 和 图片URL列表
        """
        tapd_data = {}
        image_urls = []
        
        for feishu_field, value in feishu_data.items():
            if value is None or value == "":
                continue
            
            # 查找映射
            tapd_field = self.field_mapping.story_field_mapping.get(feishu_field)
            
            if tapd_field is None:
                # 尝试直接使用原字段名（可能是TAPD原生字段）
                if feishu_field in ['name', 'description', 'owner', 'priority', 
                                   'priority_label', 'iteration_id', 'workitem_type_id',
                                   'module', 'version', 'label', 'begin', 'due']:
                    tapd_field = feishu_field
                else:
                    continue
            
            # 处理特殊字段
            if tapd_field == "_images":
                # 收集图片URL
                urls = self._extract_image_urls(value)
                image_urls.extend(urls)
                continue
            
            # 处理优先级转换
            if tapd_field in ['priority', 'priority_label']:
                value = self._map_priority(str(value))
            
            # 处理需求类别（workitem_type_id）
            if feishu_field == "标签类型" or feishu_field == "需求类别":
                type_id = self.workitem_types.get_type_id(str(value))
                if type_id:
                    tapd_data['workitem_type_id'] = type_id
                # 同时作为标签
                if 'label' not in tapd_data:
                    tapd_data['label'] = str(value)
                continue
            
            tapd_data[tapd_field] = self._clean_value(value)
        
        return tapd_data, image_urls
    
    def map_bug_fields(self, feishu_data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[str]]:
        """
        将飞书字段映射到TAPD缺陷字段
        
        Args:
            feishu_data: 飞书多维表的记录数据
            
        Returns:
            (tapd_data, image_urls): TAPD API 数据字典 和 图片URL列表
        """
        tapd_data = {}
        image_urls = []
        
        for feishu_field, value in feishu_data.items():
            if value is None or value == "":
                continue
            
            # 查找映射
            tapd_field = self.field_mapping.bug_field_mapping.get(feishu_field)
            
            if tapd_field is None:
                # 尝试直接使用原字段名
                if feishu_field in ['title', 'description', 'current_owner', 'priority',
                                   'priority_label', 'severity', 'iteration_id',
                                   'module', 'version_report', 'label', 'begin', 'due']:
                    tapd_field = feishu_field
                else:
                    continue
            
            # 处理特殊字段
            if tapd_field == "_images":
                urls = self._extract_image_urls(value)
                image_urls.extend(urls)
                continue
            
            # 处理优先级转换
            if tapd_field in ['priority', 'priority_label']:
                value = self._map_priority(str(value))
            
            # 处理严重程度转换
            if tapd_field == 'severity':
                value = self._map_severity(str(value))
            
            tapd_data[tapd_field] = self._clean_value(value)
        
        return tapd_data, image_urls
    
    def _map_priority(self, value: str) -> str:
        """映射优先级"""
        value = value.strip()
        if value in self.field_mapping.priority_mapping:
            return self.field_mapping.priority_mapping[value]
        return value
    
    def _map_severity(self, value: str) -> str:
        """映射严重程度"""
        value = value.strip()
        if value in self.field_mapping.severity_mapping:
            return self.field_mapping.severity_mapping[value]
        return value
    
    def _extract_image_urls(self, value: Any) -> List[str]:
        """
        从字段值中提取图片URL
        
        支持格式:
        - 单个URL字符串
        - 逗号/换行分隔的多个URL
        - URL数组
        - 飞书附件格式 [{"url": "xxx", "name": "yyy"}, ...]
        """
        urls = []
        
        if isinstance(value, str):
            # 字符串，可能是逗号/换行分隔
            import re
            parts = re.split(r'[,\n;]+', value)
            for part in parts:
                url = part.strip()
                if url and self._is_image_url(url):
                    urls.append(url)
        
        elif isinstance(value, list):
            for item in value:
                if isinstance(item, str):
                    if self._is_image_url(item):
                        urls.append(item)
                elif isinstance(item, dict):
                    # 飞书附件格式
                    url = item.get('url') or item.get('file_url') or item.get('src')
                    if url and self._is_image_url(url):
                        urls.append(url)
        
        elif isinstance(value, dict):
            url = value.get('url') or value.get('file_url') or value.get('src')
            if url and self._is_image_url(url):
                urls.append(url)
        
        return urls
    
    def _is_image_url(self, url: str) -> bool:
        """检查是否是图片URL"""
        if not url.startswith(('http://', 'https://')):
            return False
        # 检查常见图片扩展名
        image_extensions = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
        lower_url = url.lower().split('?')[0]  # 去掉查询参数
        return lower_url.endswith(image_extensions) or 'image' in lower_url
    
    def _clean_value(self, value: Any) -> str:
        """清理字段值"""
        if isinstance(value, str):
            return value.strip()
        elif isinstance(value, (int, float)):
            return str(value)
        elif isinstance(value, list):
            # 如果是列表，取第一个值或用 | 连接
            if len(value) == 1:
                return str(value[0]).strip()
            return '|'.join(str(v).strip() for v in value if v)
        else:
            return str(value)


class TicketBuilder:
    """工单构建器"""
    
    def __init__(self, config: AppConfig = None):
        self.config = config or get_config()
        self.mapper = FieldMapper(self.config)
    
    def build_story(self, feishu_data: Dict[str, Any], 
                    include_images_in_description: bool = True) -> Dict[str, Any]:
        """
        构建需求单数据
        
        Args:
            feishu_data: 飞书多维表记录数据
            include_images_in_description: 是否将图片嵌入描述中
            
        Returns:
            构建好的TAPD需求数据，包含:
                - tapd_fields: TAPD API 字段
                - image_urls: 图片URL列表（供附件上传使用）
        """
        tapd_data, image_urls = self.mapper.map_story_fields(feishu_data)
        
        # 必填项检查
        if 'name' not in tapd_data or not tapd_data['name']:
            raise ValueError("需求单必须包含标题(name)字段")
        
        # 添加项目ID
        tapd_data['workspace_id'] = self.config.tapd.workspace_id
        
        # 处理图片嵌入描述
        if include_images_in_description and image_urls:
            description = tapd_data.get('description', '')
            img_html = self._images_to_html(image_urls)
            if description:
                tapd_data['description'] = f"{description}<br/><br/>{img_html}"
            else:
                tapd_data['description'] = img_html
        
        return {
            'tapd_fields': tapd_data,
            'image_urls': image_urls
        }
    
    def build_bug(self, feishu_data: Dict[str, Any],
                  include_images_in_description: bool = True) -> Dict[str, Any]:
        """
        构建缺陷单数据
        
        Args:
            feishu_data: 飞书多维表记录数据
            include_images_in_description: 是否将图片嵌入描述中
            
        Returns:
            构建好的TAPD缺陷数据
        """
        tapd_data, image_urls = self.mapper.map_bug_fields(feishu_data)
        
        # 必填项检查
        if 'title' not in tapd_data or not tapd_data['title']:
            raise ValueError("缺陷单必须包含标题(title)字段")
        
        # 添加项目ID
        tapd_data['workspace_id'] = self.config.tapd.workspace_id
        
        # 处理图片嵌入描述
        if include_images_in_description and image_urls:
            description = tapd_data.get('description', '')
            img_html = self._images_to_html(image_urls)
            if description:
                tapd_data['description'] = f"{description}<br/><br/>{img_html}"
            else:
                tapd_data['description'] = img_html
        
        return {
            'tapd_fields': tapd_data,
            'image_urls': image_urls
        }
    
    def _images_to_html(self, image_urls: List[str], max_width: str = "800px") -> str:
        """将图片URL转换为HTML标签"""
        if not image_urls:
            return ""
        
        img_tags = []
        for i, url in enumerate(image_urls, 1):
            img_tags.append(
                f'<p>图片{i}:</p>'
                f'<img src="{url}" alt="图片{i}" style="max-width: {max_width};" />'
            )
        
        return '<br/>'.join(img_tags)
