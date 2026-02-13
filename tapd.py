"""
TAPD API 客户端
通过HTTP请求向TAPD提交工单（缺陷/需求/任务）
"""
import requests
import base64
import re
from typing import Optional, Dict, Any, List, Union

class TapdClient:
    """TAPD API 客户端"""
    
    BASE_URL = "https://api.tapd.cn"
    
    # 常见图片扩展名
    IMAGE_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
    
    def __init__(self, api_user: str, api_password: str, workspace_id: str):

        self.api_user = api_user
        self.api_password = api_password
        self.workspace_id = workspace_id
        self.session = requests.Session()
        
        # 设置基本认证
        auth_string = f"{api_user}:{api_password}"
        auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
        self.session.headers.update({
            "Authorization": f"Basic {auth_bytes}",
            # TAPD API 使用表单格式，不要设置 Content-Type 为 application/json
        })
    
    def _request(self, method: str, endpoint: str, params: Optional[Dict] = None, 
                 data: Optional[Dict] = None) -> Dict:
        """
        发送HTTP请求
        
        Args:
            method: HTTP方法 (GET/POST)
            endpoint: API端点
            params: URL参数
            data: POST数据
            
        Returns:
            API响应数据
        """
        url = f"{self.BASE_URL}{endpoint}"
        
        try:
            if method.upper() == "GET":
                response = self.session.get(url, params=params)
            elif method.upper() == "POST":
                response = self.session.post(url, params=params, data=data)
            else:
                raise ValueError(f"不支持的HTTP方法: {method}")
            
            response.raise_for_status()
            result = response.json()
            
            if result.get("status") != 1:
                raise Exception(f"TAPD API错误: {result.get('info', '未知错误')}")
            
            return result.get("data", {})
            
        except requests.exceptions.RequestException as e:
            raise Exception(f"请求TAPD API失败: {str(e)}")
    
    # ============ 图片/描述处理辅助方法 ============
    
    @staticmethod
    def url_to_img_tag(url: str, width: str = None, alt: str = "图片") -> str:
        """
        将图片URL转换为HTML img标签
        
        Args:
            url: 图片URL
            width: 可选，图片宽度（如 "500px" 或 "100%"）
            alt: 图片替代文本
            
        Returns:
            HTML img标签字符串
            
        Example:
            url_to_img_tag("https://example.com/img.png")
            # 返回: '<img src="https://example.com/img.png" alt="图片" />'
        """
        if not url or not url.strip():
            return ""
        
        url = url.strip()
        style = f' style="max-width: {width};"' if width else ""
        return f'<img src="{url}" alt="{alt}"{style} />'
    
    @staticmethod
    def urls_to_img_tags(urls: Union[str, List[str]], separator: str = "<br/>") -> str:
        """
        将多个图片URL转换为HTML img标签
        
        Args:
            urls: 图片URL，可以是:
                - 单个URL字符串
                - 逗号/换行分隔的多个URL字符串
                - URL列表
            separator: 多个图片之间的分隔符，默认换行
            
        Returns:
            HTML img标签字符串
            
        Example:
            urls_to_img_tags("url1,url2")  # 逗号分隔
            urls_to_img_tags(["url1", "url2"])  # 列表
        """
        if not urls:
            return ""
        
        # 如果是字符串，尝试按逗号或换行分隔
        if isinstance(urls, str):
            # 支持逗号、换行、分号分隔
            urls = re.split(r'[,\n;]+', urls)
        
        # 过滤空值并转换
        img_tags = []
        for url in urls:
            url = url.strip()
            if url:
                img_tags.append(TapdClient.url_to_img_tag(url))
        
        return separator.join(img_tags)
    
    @staticmethod
    def format_description_with_images(text: str, image_urls: Union[str, List[str]] = None, 
                                        image_position: str = "bottom") -> str:
        """
        格式化描述内容，自动将图片URL转换为HTML图片标签
        
        Args:
            text: 描述文本内容
            image_urls: 图片URL（字符串或列表）
            image_position: 图片位置 ("top"=顶部, "bottom"=底部)
            
        Returns:
            包含HTML图片标签的描述内容
            
        Example:
            format_description_with_images(
                "问题描述：xxx", 
                "https://example.com/img.png"
            )
            # 返回: '<p>问题描述：xxx</p><br/><img src="https://example.com/img.png" alt="图片" />'
        """
        result_parts = []
        
        # 处理文本内容
        if text and text.strip():
            # 如果文本不是HTML格式，用p标签包裹
            text = text.strip()
            if not text.startswith('<'):
                text = f"<p>{text}</p>"
            result_parts.append(text)
        
        # 处理图片
        if image_urls:
            img_html = TapdClient.urls_to_img_tags(image_urls)
            if img_html:
                if image_position == "top":
                    result_parts.insert(0, img_html)
                else:
                    result_parts.append(img_html)
        
        return "<br/>".join(result_parts)
    
    @staticmethod  
    def auto_convert_image_urls(description: str) -> str:
        """
        自动检测描述中的图片URL并转换为HTML img标签
        
        自动识别常见图片URL格式（以.png/.jpg/.jpeg/.gif等结尾）
        
        Args:
            description: 包含图片URL的描述内容
            
        Returns:
            转换后的描述内容
            
        Example:
            auto_convert_image_urls("截图：https://example.com/img.png")
            # 返回: '截图：<img src="https://example.com/img.png" alt="图片" />'
        """
        if not description:
            return description
        
        # 匹配图片URL的正则表达式
        # 支持http/https开头，以常见图片扩展名结尾的URL
        img_url_pattern = r'(https?://[^\s<>"\']+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))(?:\?[^\s<>"\']*)?'
        
        def replace_url(match):
            url = match.group(0)
            # 如果URL已经在img标签中，则不替换
            return f'<img src="{url}" alt="图片" />'
        
        # 先检查是否已经是img标签格式
        if '<img' in description and 'src=' in description:
            return description
        
        return re.sub(img_url_pattern, replace_url, description, flags=re.IGNORECASE)
    
    # ============ 缺陷(Bug)相关 ============
    
    def create_bug(self, title: str, description: str = "", 
                   severity: str = "general", priority: str = "low",
                   current_owner: str = "", reporter: str = "",
                   **kwargs) -> Dict:
        """
        创建缺陷(Bug)
        
        Args:
            title: 缺陷标题
            description: 缺陷描述
            severity: 严重程度 (fatal/serious/general/prompt/advice)
            priority: 优先级 (urgent/high/middle/low/insignificant)
            current_owner: 当前处理人（用户名或昵称）
            reporter: 报告人
            **kwargs: 其他可选参数，如:
                - version_report: 发现版本
                - version_test: 验证版本
                - version_fix: 解决版本
                - version_close: 关闭版本
                - module: 模块
                - iteration_id: 迭代ID
                - custom_field_xxx: 自定义字段
                
        Returns:
            创建的缺陷信息
        """
        data = {
            "workspace_id": self.workspace_id,
            "title": title,
            "description": description,
            "severity": severity,
            "priority": priority,
        }
        
        if current_owner:
            data["current_owner"] = current_owner
        if reporter:
            data["reporter"] = reporter
            
        # 添加其他可选参数
        data.update(kwargs)
        
        result = self._request("POST", "/bugs", data=data)
        return result.get("Bug", {})
    
    def get_bug(self, bug_id: str) -> Dict:
        """获取缺陷详情"""
        params = {
            "workspace_id": self.workspace_id,
            "id": bug_id
        }
        result = self._request("GET", "/bugs", params=params)
        
        # 处理 result 可能是列表的情况
        if isinstance(result, list):
            if len(result) > 0:
                first_item = result[0]
                return first_item.get("Bug", first_item) if isinstance(first_item, dict) else {}
            return {}
        
        # result 是字典的情况
        bugs = result.get("Bug", [])
        if isinstance(bugs, list) and len(bugs) > 0:
            # API 返回列表，每个元素是 {"Bug": {...}} 格式
            first_bug = bugs[0]
            return first_bug.get("Bug", first_bug) if isinstance(first_bug, dict) else {}
        return bugs if isinstance(bugs, dict) else {}
    
    def update_bug(self, bug_id: str, **kwargs) -> Dict:
        """
        更新缺陷
        
        Args:
            bug_id: 缺陷ID
            **kwargs: 要更新的字段
        """
        data = {
            "workspace_id": self.workspace_id,
            "id": bug_id,
            **kwargs
        }
        result = self._request("POST", "/bugs", data=data)
        return result.get("Bug", {})
    
    # ============ 需求(Story)相关 ============
    
    def create_story(self, name: str, description: str = "",
                     priority: str = "middle", owner: str = "",
                     creator: str = "", **kwargs) -> Dict:
        """
        创建需求(Story)
        
        Args:
            name: 需求名称
            description: 需求描述
            priority: 优先级 (1-4, 1最高)
            owner: 处理人
            creator: 创建人
            **kwargs: 其他可选参数，如:
                - iteration_id: 迭代ID
                - module: 模块
                - release_id: 发布计划ID
                - source: 需求来源
                - category_id: 需求分类ID
                - parent_id: 父需求ID
                - custom_field_xxx: 自定义字段
                
        Returns:
            创建的需求信息
        """
        data = {
            "workspace_id": self.workspace_id,
            "name": name,
            "description": description,
            "priority": priority,
        }
        
        if owner:
            data["owner"] = owner
        if creator:
            data["creator"] = creator
            
        data.update(kwargs)
        
        result = self._request("POST", "/stories", data=data)
        return result.get("Story", {})
    
    def get_story(self, story_id: str) -> Dict:
        """获取需求详情"""
        params = {
            "workspace_id": self.workspace_id,
            "id": story_id
        }
        result = self._request("GET", "/stories", params=params)
        
        # 处理 result 可能是列表的情况 [{"Story": {...}}, ...]
        if isinstance(result, list):
            if len(result) > 0:
                first_item = result[0]
                return first_item.get("Story", first_item) if isinstance(first_item, dict) else {}
            return {}
        
        # result 是字典的情况
        if isinstance(result, dict):
            # 可能直接是 Story 数据
            if "id" in result:
                return result
            # 或者是 {"Story": {...}} 格式
            story = result.get("Story", {})
            if isinstance(story, dict):
                return story
            elif isinstance(story, list) and len(story) > 0:
                first_story = story[0]
                return first_story.get("Story", first_story) if isinstance(first_story, dict) else first_story
        
        return {}
    
    def update_story(self, story_id: str, **kwargs) -> Dict:
        """更新需求"""
        data = {
            "workspace_id": self.workspace_id,
            "id": story_id,
            **kwargs
        }
        result = self._request("POST", "/stories", data=data)
        return result.get("Story", {})
    
    # ============ 任务(Task)相关 ============
    
    def create_task(self, name: str, description: str = "",
                    priority: str = "middle", owner: str = "",
                    creator: str = "", story_id: str = "", **kwargs) -> Dict:
        """
        创建任务(Task)
        
        Args:
            name: 任务名称
            description: 任务描述
            priority: 优先级
            owner: 处理人
            creator: 创建人
            story_id: 关联需求ID
            **kwargs: 其他可选参数
                
        Returns:
            创建的任务信息
        """
        data = {
            "workspace_id": self.workspace_id,
            "name": name,
            "description": description,
            "priority": priority,
        }
        
        if owner:
            data["owner"] = owner
        if creator:
            data["creator"] = creator
        if story_id:
            data["story_id"] = story_id
            
        data.update(kwargs)
        
        result = self._request("POST", "/tasks", data=data)
        return result.get("Task", {})
    
    def get_task(self, task_id: str) -> Dict:
        """获取任务详情"""
        params = {
            "workspace_id": self.workspace_id,
            "id": task_id
        }
        result = self._request("GET", "/tasks", params=params)
        
        # 处理 result 可能是列表的情况
        if isinstance(result, list):
            if len(result) > 0:
                first_item = result[0]
                return first_item.get("Task", first_item) if isinstance(first_item, dict) else {}
            return {}
        
        # result 是字典的情况
        tasks = result.get("Task", [])
        if isinstance(tasks, list) and len(tasks) > 0:
            # API 返回列表，每个元素是 {"Task": {...}} 格式
            first_task = tasks[0]
            return first_task.get("Task", first_task) if isinstance(first_task, dict) else {}
        return tasks if isinstance(tasks, dict) else {}
    
    # ============ 通用方法 ============
    
    def create_issue(self, issue_type: str, data: Dict) -> Dict:
        """
        通用创建工作项方法
        
        Args:
            issue_type: 工作项类型 (bug/story/task)
            data: 工作项数据
            
        Returns:
            创建的工作项信息
        """
        issue_type = issue_type.lower()
        
        if issue_type == "bug":
            return self.create_bug(
                title=data.get("Title", data.get("title", "")),
                description=data.get("Description", data.get("description", "")),
                severity=data.get("Severity", data.get("severity", "general")),
                priority=data.get("Priority", data.get("priority", "middle")),
                current_owner=data.get("Assignee", data.get("current_owner", "")),
                reporter=data.get("Reporter", data.get("reporter", ""))
            )
        elif issue_type == "story":
            return self.create_story(
                name=data.get("Title", data.get("name", "")).strip(),
                description=data.get("Description", data.get("description", "")),
                priority=data.get("Priority", data.get("priority", "middle")).strip(),
                owner=data.get("Assignee", data.get("owner", "")).strip(),
                creator=data.get("Creator", data.get("creator", "")).strip()
            )
        elif issue_type == "task":
            return self.create_task(
                name=data.get("Title", data.get("name", "")).strip(),
                description=data.get("Description", data.get("description", "")),
                priority=data.get("Priority", data.get("priority", "middle")).strip(),
                owner=data.get("Assignee", data.get("owner", "")).strip(),
                creator=data.get("Creator", data.get("creator", "")).strip(),
                story_id=data.get("StoryId", data.get("story_id", "")).strip()
            )
        else:
            raise ValueError(f"不支持的工作项类型: {issue_type}")
    
    def get_project_members(self) -> List[Dict]:
        """获取项目成员列表"""
        params = {"workspace_id": self.workspace_id}
        result = self._request("GET", "/workspaces/users", params=params)
        return result.get("UserWorkspace", [])
    
    def get_iterations(self) -> List[Dict]:
        """获取迭代列表"""
        params = {"workspace_id": self.workspace_id}
        result = self._request("GET", "/iterations", params=params)
        return result.get("Iteration", [])
    
    # ============ 附件上传相关 ============
    
    def upload_attachment(self, entry_type: str, entry_id: str, file_path: str, 
                          filename: str = None) -> Dict:
        """
        上传附件到TAPD工单（支持图片等文件）
        
        Args:
            entry_type: 工单类型 (story/bug/task)
            entry_id: 工单ID
            file_path: 本地文件路径
            filename: 自定义文件名（可选，默认使用原文件名）
            
        Returns:
            上传结果，包含附件信息
            
        Example:
            # 创建需求后上传图片
            story = client.create_story(name="需求标题", description="描述")
            story_id = story.get("id")
            result = client.upload_attachment("story", story_id, "C:/path/to/image.png")
        """
        import os
        
        url = f"{self.BASE_URL}/attachments"
        
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件不存在: {file_path}")
        
        # 获取文件名
        if filename is None:
            filename = os.path.basename(file_path)
        
        # 获取文件的MIME类型
        import mimetypes
        mime_type, _ = mimetypes.guess_type(file_path)
        if mime_type is None:
            mime_type = 'application/octet-stream'
        
        try:
            with open(file_path, 'rb') as f:
                files = {
                    'file': (filename, f, mime_type)
                }
                data = {
                    'workspace_id': self.workspace_id,
                    'entry_type': entry_type,
                    'entry_id': entry_id
                }
                
                response = self.session.post(url, data=data, files=files)
                response.raise_for_status()
                result = response.json()
                
                if result.get("status") != 1:
                    raise Exception(f"上传附件失败: {result.get('info', '未知错误')}")
                
                return result.get("data", {})
                
        except requests.exceptions.RequestException as e:
            raise Exception(f"上传附件请求失败: {str(e)}")
    
    def upload_attachments(self, entry_type: str, entry_id: str, 
                           file_paths: List[str]) -> List[Dict]:
        """
        批量上传多个附件
        
        Args:
            entry_type: 工单类型 (story/bug/task)
            entry_id: 工单ID
            file_paths: 文件路径列表
            
        Returns:
            上传结果列表
        """
        results = []
        for file_path in file_paths:
            try:
                result = self.upload_attachment(entry_type, entry_id, file_path)
                results.append({"file": file_path, "success": True, "data": result})
            except Exception as e:
                results.append({"file": file_path, "success": False, "error": str(e)})
        return results
    
    def create_story_with_attachments(self, name: str, description: str = "",
                                      file_paths: List[str] = None, **kwargs) -> Dict:
        """
        创建需求并上传附件（图片等）
        
        Args:
            name: 需求名称
            description: 需求描述
            file_paths: 附件文件路径列表
            **kwargs: 其他需求参数
            
        Returns:
            包含需求信息和附件上传结果的字典
            
        Example:
            result = client.create_story_with_attachments(
                name="需求标题",
                description="需求描述",
                file_paths=["C:/images/screenshot1.png", "C:/images/screenshot2.png"],
                priority="2",
                owner="张三"
            )
        """
        # 1. 创建需求
        story = self.create_story(name=name, description=description, **kwargs)
        story_id = story.get("id")
        
        result = {
            "story": story,
            "attachments": []
        }
        
        # 2. 上传附件
        if file_paths and story_id:
            result["attachments"] = self.upload_attachments("story", story_id, file_paths)
        
        return result
    
    def create_bug_with_attachments(self, title: str, description: str = "",
                                    file_paths: List[str] = None, **kwargs) -> Dict:
        """
        创建缺陷并上传附件（图片等）
        
        Args:
            title: 缺陷标题
            description: 缺陷描述
            file_paths: 附件文件路径列表
            **kwargs: 其他缺陷参数
            
        Returns:
            包含缺陷信息和附件上传结果的字典
        """
        # 1. 创建缺陷
        bug = self.create_bug(title=title, description=description, **kwargs)
        bug_id = bug.get("id")
        
        result = {
            "bug": bug,
            "attachments": []
        }
        
        # 2. 上传附件
        if file_paths and bug_id:
            result["attachments"] = self.upload_attachments("bug", bug_id, file_paths)
        
        return result
    
    def get_story_workitem_types(self) -> List[Dict]:
        """
        获取需求类别列表
        
        Returns:
            需求类别列表，每个元素包含:
                - id: 需求类别ID (workitem_type_id)
                - name: 需求类别名称
                - english_name: 英文名称/标签
                - workspace_id: 项目ID
                - 等其他字段
        """
        params = {"workspace_id": self.workspace_id, "type": "story"}
        result = self._request("GET", "/workitem_types", params=params)
        
        # 处理返回结果
        if isinstance(result, list):
            # 返回格式: [{"WorkitemType": {...}}, ...]
            return [item.get("WorkitemType", item) if isinstance(item, dict) else item for item in result]
        elif isinstance(result, dict):
            types = result.get("WorkitemType", [])
            if isinstance(types, list):
                return types
            return [types] if types else []
        return []
    
    def print_story_workitem_types(self) -> None:
        """
        打印需求类别列表（便于查看 workitem_type_id）
        """
        types = self.get_story_workitem_types()
        print(f"\n{'='*80}")
        print(f"项目 {self.workspace_id} 的需求类别列表:")
        print(f"{'='*80}")
        print(f"{'类别名称':<20} {'英文标签':<15} {'workitem_type_id':<25}")
        print(f"{'-'*80}")
        for t in types:
            name = t.get("name", "未知")
            english_name = t.get("english_name", "")
            type_id = t.get("id", "未知")
            print(f"{name:<20} {english_name:<15} {type_id:<25}")
        print(f"{'='*80}\n")
    
    def get_stories_list(self, limit: int = 50, **kwargs) -> List[Dict]:
        """
        获取需求列表
        
        Args:
            limit: 返回数量限制，默认50
            **kwargs: 其他查询参数，如:
                - status: 状态筛选
                - owner: 处理人筛选
                - priority: 优先级筛选
                
        Returns:
            需求列表
        """
        params = {
            "workspace_id": self.workspace_id,
            "limit": limit,
            **kwargs
        }
        result = self._request("GET", "/stories", params=params)
        
        # 处理返回结果 - TAPD API 返回格式可能是列表或字典
        if isinstance(result, list):
            # 返回格式: [{"Story": {...}}, {"Story": {...}}]
            return [item.get("Story", item) if isinstance(item, dict) else item for item in result]
        elif isinstance(result, dict):
            # 返回格式可能是 {"Story": [...]} 或 {"Story": {...}}
            stories = result.get("Story", [])
            if isinstance(stories, list):
                return stories
            elif isinstance(stories, dict):
                return [stories]
        return []


# ============ 使用示例 ============

if __name__ == "__main__":
    # 配置信息（请替换为实际值）
    API_USER = "gNxpkwrr"           # TAPD API用户名
    API_PASSWORD = "86EE396F-6733-051C-3BA9-1243A2E8AA36"   # TAPD API密码
    WORKSPACE_ID = "41827997"            # 项目空间ID
    
    # 创建客户端
    client = TapdClient(
        api_user=API_USER,
        api_password=API_PASSWORD,
        workspace_id=WORKSPACE_ID
    )
    
    # 示例1: 创建缺陷
    # try:
    #     bug = client.create_bug(
    #         title="测试缺陷 - 测试建单",
    #         description="<p>使用http建单测试，先用python过一遍没问题配置到多维表的按钮上</p>",
    #         severity="general",      # 一般
    #         priority="low",         # 低
    #         current_owner="郑成昆",    # 处理人
    #         reporter="郑成昆",         # 报告人
    #         # 可选: 关联迭代
    #         # iteration_id="1112222333"
    #     )
    #     print(f"缺陷创建成功!")
    #     print(f"  ID: {bug.get('id')}")
    #     print(f"  标题: {bug.get('title')}")
    #     print(f"  URL: https://www.tapd.cn/{WORKSPACE_ID}/bugtrace/bugs/view/{bug.get('id')}")
    # except Exception as e:
    #     print(f"创建缺陷失败: {e}")
    
    # # 示例2: 创建需求
    # try:
    #     story = client.create_story(
    #         name="用户登录功能优化",
    #         description="<p>支持手机号快捷登录</p>",
    #         priority="2",            # 高优先级
    #         owner="王五",            # 处理人
    #         creator="赵六"           # 创建人
    #     )
    #     print(f"\n需求创建成功!")
    #     print(f"  ID: {story.get('id')}")
    #     print(f"  名称: {story.get('name')}")
    #     print(f"  URL: https://www.tapd.cn/{WORKSPACE_ID}/prong/stories/view/{story.get('id')}")
    # except Exception as e:
    #     print(f"创建需求失败: {e}")
    
    # 示例3: 创建任务
    # try:
    #     task = client.create_task(
    #         name="编写登录接口单元测试",
    #         description="覆盖正常和异常场景",
    #         priority="middle",
    #         owner="钱七",
    #         # story_id="1112222444"  # 可关联需求
    #     )
    #     print(f"\n任务创建成功!")
    #     print(f"  ID: {task.get('id')}")
    #     print(f"  名称: {task.get('name')}")
    #     print(f"  URL: https://www.tapd.cn/{WORKSPACE_ID}/prong/tasks/view/{task.get('id')}")
    # except Exception as e:
    #     print(f"创建任务失败: {e}")
    
    # # 示例4: 批量创建
    # issues_to_create = [
    #     {"type": "bug", "Title": "问题1", "Description": "描述1", "Assignee": "张三"},
    #     {"type": "bug", "Title": "问题2", "Description": "描述2", "Assignee": "李四"},
    #     {"type": "story", "Title": "需求1", "Description": "需求描述", "Assignee": "王五"},
    # ]
    
    # print("\n批量创建结果:")
    # for item in issues_to_create:
    #     try:
    #         issue_type = item.pop("type")
    #         result = client.create_issue(issue_type, item)
    #         print(f"  ✓ {issue_type}: {result.get('id')} - {result.get('title', result.get('name'))}")
    #     except Exception as e:
    #         print(f"  ✗ 失败: {e}")
    
    # 示例5：获取一个需求单所有字段
    # try:
    #     story_id = "1141827997001293351"  # 使用完整的需求ID
    #     story = client.get_story(story_id)
    #     print(f"\n需求详情 (ID: {story_id}):")
    #     if not story:
    #         print("  未获取到数据")
    #     for key, value in story.items():
    #         print(f"  {key}: {value}")
    # except Exception as e:
    #     print(f"获取需求失败: {e}")

    # 示例6：获取需求列表
    # try:
    #     stories = client.get_stories_list(limit=10)
    #     print(f"\n需求列表 (前10条):")
    #     if not stories:
    #         print("  没有获取到需求，可能是项目中暂无需求或权限问题")
    #     for story in stories:
    #         print(f"  ID: {story.get('id')}, 名称: {story.get('name')}, 状态: {story.get('status')}")
    # except Exception as e:
    #     print(f"获取需求列表失败: {e}")

    # 示例7：获取迭代列表
    # try:
    #     params = {"workspace_id": "41827997"}
    #     url = "https://api.tapd.cn/iterations"
    #     response = client.session.get(url, params=params)
    #     data = response.json()
    #     iterations = data.get("data", [])
    #     print(f"\n迭代列表:")
    #     for item in iterations:
    #         it = item.get("Iteration", item)
    #         print(f"  ID: {it.get('id')}, 名称: {it.get('name')}, 状态: {it.get('status')}")
    # except Exception as e:
    #     print(f"获取迭代列表失败: {e}")