"""
配置管理模块
管理TAPD API配置、飞书配置和字段映射配置
"""
import os
import json
from typing import Dict, Any, Optional
from dataclasses import dataclass, field
from pathlib import Path


@dataclass
class TapdConfig:
    """TAPD API 配置"""
    api_user: str = "gNxpkwrr"
    api_password: str = "86EE396F-6733-051C-3BA9-1243A2E8AA36"
    workspace_id: str = "41827997"
    
    # TAPD 链接前缀
    base_url: str = "https://api.tapd.cn"
    web_base_url: str = "https://www.tapd.cn"
    
    def get_story_url(self, story_id: str) -> str:
        """获取需求单链接"""
        return f"{self.web_base_url}/{self.workspace_id}/prong/stories/view/{story_id}"
    
    def get_bug_url(self, bug_id: str) -> str:
        """获取缺陷单链接"""
        return f"{self.web_base_url}/{self.workspace_id}/bugtrace/bugs/view/{bug_id}"


@dataclass
class FeishuConfig:
    """飞书配置"""
    app_id: str = "cli_a9edfc60bef89bd2"
    app_secret: str = "4HJ12IX5jGGLFsa8E7ciHeHF3jNeWVwf"
    # Webhook 接收配置
    webhook_port: int = 8080
    webhook_path: str = "/webhook/feishu"
    # 用于验证飞书请求的加密密钥（可选）
    verification_token: str = ""


@dataclass
class WorkitemTypeMapping:
    """需求类别映射配置"""
    # 标签名称 -> workitem_type_id
    label_to_type_id: Dict[str, str] = field(default_factory=lambda: {
        "FX": "1141827997001001460",
        "PREFAB": "1141827997001001459",
        "DD": "1141827997001001453",
        "QA": "1141827997001001452",
        "UI": "1141827997001001451",
        "DIRECTOR": "1141827997001001450",
        "WRITER": "1141827997001001449",
        "Audio": "1141827997001001442",
        "AUDIO": "1141827997001001442",
        "CG": "1141827997001001441",
        "ARTS": "1141827997001001440",
        "ASSET": "1141827997001001439",
        "EXCEL": "1141827997001001438",
        "Program": "1141827997001001437",
        "PROGRAM": "1141827997001001437",
        "FEATURE": "1141827997001001436",
        "Epic": "1141827997001001435",
    })
    
    def get_type_id(self, label: str) -> Optional[str]:
        """根据标签获取 workitem_type_id"""
        if not label:
            return None
        # 尝试精确匹配
        if label in self.label_to_type_id:
            return self.label_to_type_id[label]
        # 尝试大写匹配
        if label.upper() in self.label_to_type_id:
            return self.label_to_type_id[label.upper()]
        return None


@dataclass 
class FieldMappingConfig:
    """字段映射配置 - 飞书多维表字段名 -> TAPD API 字段名"""
    
    # 需求单字段映射
    story_field_mapping: Dict[str, str] = field(default_factory=lambda: {
        # 飞书字段名: TAPD字段名
        "标题": "name",
        "名称": "name",
        "需求名称": "name",
        "描述": "description",
        "详细描述": "description",
        "处理人": "owner",
        "负责人": "owner",
        "创建人": "creator",
        "优先级": "priority_label",
        "标签类型": "label",
        "标签": "label",
        "需求类别": "workitem_type_id",
        "迭代": "iteration_id",
        "版本": "version",
        "模块": "module",
        "预计开始": "begin",
        "预计结束": "due",
        "图片": "_images",  # 特殊字段，用于图片URL
        "截图": "_images",
        "附件图片": "_images",
    })
    
    # 缺陷单字段映射
    bug_field_mapping: Dict[str, str] = field(default_factory=lambda: {
        # 飞书字段名: TAPD字段名
        "标题": "title",
        "缺陷标题": "title",
        "描述": "description",
        "详细描述": "description",
        "处理人": "current_owner",
        "负责人": "current_owner",
        "当前处理人": "current_owner",
        "创建人": "reporter",
        "报告人": "reporter",
        "优先级": "priority_label",
        "严重程度": "severity",
        "标签": "label",
        "迭代": "iteration_id",
        "版本": "version_report",
        "发现版本": "version_report",
        "模块": "module",
        "预计开始": "begin",
        "预计结束": "due",
        "图片": "_images",
        "截图": "_images",
        "附件图片": "_images",
    })
    
    # 优先级映射
    priority_mapping: Dict[str, str] = field(default_factory=lambda: {
        "紧急": "urgent",
        "高": "high", 
        "中": "middle",
        "低": "low",
        "无关紧要": "insignificant",
        "1": "urgent",
        "2": "high",
        "3": "middle", 
        "4": "low",
    })
    
    # 严重程度映射
    severity_mapping: Dict[str, str] = field(default_factory=lambda: {
        "致命": "fatal",
        "严重": "serious",
        "一般": "general",
        "提示": "prompt",
        "建议": "advice",
    })


class AppConfig:
    """应用配置管理器"""
    
    def __init__(self, config_file: str = None):
        self.config_file = config_file or "app_config.json"
        self.tapd = TapdConfig()
        self.feishu = FeishuConfig()
        self.workitem_types = WorkitemTypeMapping()
        self.field_mapping = FieldMappingConfig()
        
        # 尝试加载配置文件
        self._load_from_file()
        # 环境变量覆盖
        self._load_from_env()
    
    def _load_from_file(self) -> None:
        """从配置文件加载"""
        config_path = Path(self.config_file)
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                
                # TAPD配置
                if 'tapd' in config:
                    tapd_cfg = config['tapd']
                    self.tapd.api_user = tapd_cfg.get('api_user', self.tapd.api_user)
                    self.tapd.api_password = tapd_cfg.get('api_password', self.tapd.api_password)
                    self.tapd.workspace_id = tapd_cfg.get('workspace_id', self.tapd.workspace_id)
                
                # 飞书配置
                if 'feishu' in config:
                    feishu_cfg = config['feishu']
                    self.feishu.app_id = feishu_cfg.get('app_id', self.feishu.app_id)
                    self.feishu.app_secret = feishu_cfg.get('app_secret', self.feishu.app_secret)
                    self.feishu.webhook_port = feishu_cfg.get('webhook_port', self.feishu.webhook_port)
                    self.feishu.webhook_path = feishu_cfg.get('webhook_path', self.feishu.webhook_path)
                    self.feishu.verification_token = feishu_cfg.get('verification_token', '')
                
                # 需求类别映射
                if 'workitem_types' in config:
                    self.workitem_types.label_to_type_id.update(config['workitem_types'])
                    
            except Exception as e:
                print(f"加载配置文件失败: {e}")
    
    def _load_from_env(self) -> None:
        """从环境变量加载（优先级高于配置文件）"""
        # TAPD配置
        self.tapd.api_user = os.getenv('TAPD_API_USER', self.tapd.api_user)
        self.tapd.api_password = os.getenv('TAPD_API_PASSWORD', self.tapd.api_password)
        self.tapd.workspace_id = os.getenv('TAPD_WORKSPACE_ID', self.tapd.workspace_id)
        
        # 飞书配置
        self.feishu.app_id = os.getenv('FEISHU_APP_ID', self.feishu.app_id)
        self.feishu.app_secret = os.getenv('FEISHU_APP_SECRET', self.feishu.app_secret)
        
        port = os.getenv('WEBHOOK_PORT')
        if port:
            self.feishu.webhook_port = int(port)
    
    def save_config(self, file_path: str = None) -> None:
        """保存配置到文件"""
        file_path = file_path or self.config_file
        config = {
            'tapd': {
                'api_user': self.tapd.api_user,
                'api_password': self.tapd.api_password,
                'workspace_id': self.tapd.workspace_id,
            },
            'feishu': {
                'app_id': self.feishu.app_id,
                'app_secret': self.feishu.app_secret,
                'webhook_port': self.feishu.webhook_port,
                'webhook_path': self.feishu.webhook_path,
            },
            'workitem_types': self.workitem_types.label_to_type_id,
        }
        
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
    
    def validate(self) -> tuple[bool, list[str]]:
        """验证配置是否完整"""
        errors = []
        
        if not self.tapd.api_user:
            errors.append("缺少 TAPD API 用户名 (TAPD_API_USER)")
        if not self.tapd.api_password:
            errors.append("缺少 TAPD API 密码 (TAPD_API_PASSWORD)")
        if not self.tapd.workspace_id:
            errors.append("缺少 TAPD 项目ID (TAPD_WORKSPACE_ID)")
        
        return len(errors) == 0, errors


# 全局配置实例
_config: Optional[AppConfig] = None


def get_config() -> AppConfig:
    """获取全局配置实例"""
    global _config
    if _config is None:
        _config = AppConfig()
    return _config


def init_config(config_file: str = None) -> AppConfig:
    """初始化配置"""
    global _config
    _config = AppConfig(config_file)
    return _config
