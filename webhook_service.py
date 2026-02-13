"""
飞书 Webhook 服务模块
处理飞书多维表自动化HTTP请求，创建TAPD工单
"""
import json
import hashlib
import time
from typing import Dict, Any, Optional, Tuple
from dataclasses import dataclass
from enum import Enum

from config import get_config, AppConfig
from tapd import TapdClient
from field_mapper import FieldMapper, TicketBuilder
from image_handler import ImageHandler, FeishuImageHelper


class TicketType(Enum):
    """工单类型"""
    STORY = "story"
    BUG = "bug"
    TASK = "task"


@dataclass
class CreateTicketResult:
    """创建工单结果"""
    success: bool
    ticket_id: Optional[str] = None
    ticket_url: Optional[str] = None
    ticket_type: Optional[str] = None
    error_message: Optional[str] = None
    raw_response: Optional[Dict] = None


class FeishuWebhookHandler:
    """飞书Webhook处理器"""
    
    def __init__(self, config: AppConfig = None):
        self.config = config or get_config()
        self.tapd_client = TapdClient(
            api_user=self.config.tapd.api_user,
            api_password=self.config.tapd.api_password,
            workspace_id=self.config.tapd.workspace_id
        )
        self.ticket_builder = TicketBuilder(self.config)
        # 使用FeishuImageHelper获取带认证的ImageHandler
        feishu_helper = FeishuImageHelper(
            app_id=self.config.feishu.app_id,
            app_secret=self.config.feishu.app_secret
        )
        self.image_handler = feishu_helper.get_image_handler()
    
    def verify_request(self, timestamp: str, nonce: str, signature: str, 
                       body: bytes) -> bool:
        """
        验证飞书请求签名
        
        Args:
            timestamp: 请求时间戳
            nonce: 随机数
            signature: 签名
            body: 请求体
            
        Returns:
            验证是否通过
        """
        if not self.config.feishu.verification_token:
            return True  # 未配置验证token，跳过验证
        
        # 飞书签名验证算法
        # signature = sha256(timestamp + nonce + encrypt_key + body)
        encrypt_key = self.config.feishu.verification_token
        string_to_sign = timestamp + nonce + encrypt_key + body.decode('utf-8')
        calculated_signature = hashlib.sha256(string_to_sign.encode('utf-8')).hexdigest()
        
        return calculated_signature == signature
    
    def handle_challenge(self, body: Dict) -> Optional[Dict]:
        """
        处理飞书的URL验证请求
        
        飞书在配置Webhook时会发送challenge请求
        """
        if 'challenge' in body:
            return {'challenge': body['challenge']}
        return None
    
    def parse_feishu_request(self, body: Dict) -> Tuple[str, Dict[str, Any]]:
        """
        解析飞书多维表自动化请求
        
        飞书自动化HTTP请求格式通常是：
        {
            "record": {
                "字段1": "值1",
                "字段2": "值2",
                ...
            },
            "ticket_type": "story" or "bug"
        }
        
        或直接是记录字段：
        {
            "标题": "xxx",
            "描述": "xxx",
            "类型": "需求" or "缺陷",
            ...
        }
        
        Returns:
            (ticket_type, record_data)
        """
        # 检查是否有嵌套的record字段
        if 'record' in body:
            record_data = body['record']
            ticket_type = body.get('ticket_type', body.get('type', 'story'))
        else:
            record_data = body
            ticket_type = body.get('ticket_type', body.get('type', body.get('类型', 'story')))
        
        # 标准化ticket_type
        ticket_type_lower = str(ticket_type).lower()
        if ticket_type_lower in ['story', '需求', '需求单', 'requirement']:
            ticket_type = 'story'
        elif ticket_type_lower in ['bug', '缺陷', '缺陷单', 'defect']:
            ticket_type = 'bug'
        elif ticket_type_lower in ['task', '任务', '任务单']:
            ticket_type = 'task'
        else:
            # 默认根据字段推断
            if '标题' in record_data or 'title' in record_data:
                ticket_type = 'bug'
            else:
                ticket_type = 'story'
        
        # 移除类型字段，避免传给TAPD API
        for type_field in ['ticket_type', 'type', '类型']:
            record_data.pop(type_field, None)
        
        return ticket_type, record_data
    
    def create_ticket(self, ticket_type: str, record_data: Dict[str, Any]) -> CreateTicketResult:
        """
        创建TAPD工单
        
        Args:
            ticket_type: 工单类型 (story/bug/task)
            record_data: 记录数据
            
        Returns:
            创建结果
        """
        try:
            if ticket_type == 'story':
                return self._create_story(record_data)
            elif ticket_type == 'bug':
                return self._create_bug(record_data)
            elif ticket_type == 'task':
                return self._create_task(record_data)
            else:
                return CreateTicketResult(
                    success=False,
                    error_message=f"不支持的工单类型: {ticket_type}"
                )
        except Exception as e:
            return CreateTicketResult(
                success=False,
                error_message=str(e)
            )
    
    def _create_story(self, record_data: Dict[str, Any]) -> CreateTicketResult:
        """创建需求单"""
        try:
            # 构建需求数据
            build_result = self.ticket_builder.build_story(record_data)
            tapd_fields = build_result['tapd_fields']
            
            # 调用TAPD API创建需求
            result = self.tapd_client.create_story(**tapd_fields)
            
            story_id = result.get('id')
            if story_id:
                story_url = self.config.tapd.get_story_url(story_id)
                return CreateTicketResult(
                    success=True,
                    ticket_id=story_id,
                    ticket_url=story_url,
                    ticket_type='story',
                    raw_response=result
                )
            else:
                return CreateTicketResult(
                    success=False,
                    error_message="API返回成功但未获取到工单ID",
                    raw_response=result
                )
                
        except ValueError as e:
            return CreateTicketResult(
                success=False,
                error_message=f"数据验证失败: {str(e)}"
            )
        except Exception as e:
            return CreateTicketResult(
                success=False,
                error_message=f"创建需求失败: {str(e)}"
            )
    
    def _create_bug(self, record_data: Dict[str, Any]) -> CreateTicketResult:
        """创建缺陷单"""
        try:
            # 构建缺陷数据
            build_result = self.ticket_builder.build_bug(record_data)
            tapd_fields = build_result['tapd_fields']
            
            # 调用TAPD API创建缺陷
            result = self.tapd_client.create_bug(**tapd_fields)
            
            bug_id = result.get('id')
            if bug_id:
                bug_url = self.config.tapd.get_bug_url(bug_id)
                return CreateTicketResult(
                    success=True,
                    ticket_id=bug_id,
                    ticket_url=bug_url,
                    ticket_type='bug',
                    raw_response=result
                )
            else:
                return CreateTicketResult(
                    success=False,
                    error_message="API返回成功但未获取到工单ID",
                    raw_response=result
                )
                
        except ValueError as e:
            return CreateTicketResult(
                success=False,
                error_message=f"数据验证失败: {str(e)}"
            )
        except Exception as e:
            return CreateTicketResult(
                success=False,
                error_message=f"创建缺陷失败: {str(e)}"
            )
    
    def _create_task(self, record_data: Dict[str, Any]) -> CreateTicketResult:
        """创建任务单（暂未实现完整映射）"""
        try:
            # 简单处理任务创建
            name = record_data.get('标题') or record_data.get('名称') or record_data.get('name', '')
            description = record_data.get('描述') or record_data.get('description', '')
            owner = record_data.get('处理人') or record_data.get('owner', '')
            
            result = self.tapd_client.create_task(
                name=name,
                description=description,
                owner=owner
            )
            
            task_id = result.get('id')
            if task_id:
                task_url = f"{self.config.tapd.web_base_url}/{self.config.tapd.workspace_id}/prong/tasks/view/{task_id}"
                return CreateTicketResult(
                    success=True,
                    ticket_id=task_id,
                    ticket_url=task_url,
                    ticket_type='task',
                    raw_response=result
                )
            else:
                return CreateTicketResult(
                    success=False,
                    error_message="API返回成功但未获取到工单ID",
                    raw_response=result
                )
                
        except Exception as e:
            return CreateTicketResult(
                success=False,
                error_message=f"创建任务失败: {str(e)}"
            )
    
    def handle_request(self, body: Dict) -> Dict[str, Any]:
        """
        处理完整的Webhook请求
        
        Args:
            body: 请求体（JSON解析后）
            
        Returns:
            响应数据，符合飞书自动化期望的格式
        """
        # 检查是否是challenge请求
        challenge_response = self.handle_challenge(body)
        if challenge_response:
            return challenge_response
        
        # 解析请求
        ticket_type, record_data = self.parse_feishu_request(body)
        
        # 创建工单
        result = self.create_ticket(ticket_type, record_data)
        
        # 构建响应
        if result.success:
            return {
                "status": "success",
                "code": 0,
                "message": "工单创建成功",
                "data": {
                    "ticket_id": result.ticket_id,
                    "ticket_url": result.ticket_url,
                    "ticket_type": result.ticket_type,
                    # 飞书自动化可能需要的字段
                    "Story": {
                        "id": result.ticket_id
                    } if result.ticket_type == 'story' else None,
                    "Bug": {
                        "id": result.ticket_id
                    } if result.ticket_type == 'bug' else None,
                }
            }
        else:
            return {
                "status": "error",
                "code": -1,
                "message": result.error_message,
                "data": None
            }


class TicketService:
    """工单服务 - 可供直接调用"""
    
    def __init__(self, config: AppConfig = None):
        self.handler = FeishuWebhookHandler(config)
    
    def create_story_from_dict(self, data: Dict[str, Any]) -> CreateTicketResult:
        """从字典数据创建需求单"""
        return self.handler.create_ticket('story', data)
    
    def create_bug_from_dict(self, data: Dict[str, Any]) -> CreateTicketResult:
        """从字典数据创建缺陷单"""
        return self.handler.create_ticket('bug', data)
    
    def create_from_feishu_data(self, feishu_data: Dict[str, Any]) -> CreateTicketResult:
        """从飞书数据创建工单（自动判断类型）"""
        ticket_type, record_data = self.handler.parse_feishu_request(feishu_data)
        return self.handler.create_ticket(ticket_type, record_data)
