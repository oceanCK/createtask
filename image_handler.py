"""
图片处理模块
处理飞书图片URL和TAPD描述中的图片
"""
import re
import requests
import base64
import mimetypes
import os
import tempfile
import json
from typing import List, Dict, Optional, Tuple, Any
from urllib.parse import urlparse, unquote


class ImageHandler:
    """图片处理器"""
    
    # 支持的图片格式
    SUPPORTED_EXTENSIONS = ('.png', '.jpg', '.jpeg', '.gif', '.bmp', '.webp', '.svg')
    
    # 常见图片MIME类型
    MIME_TYPES = {
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.bmp': 'image/bmp',
        '.webp': 'image/webp',
        '.svg': 'image/svg+xml',
    }
    
    def __init__(self, feishu_access_token: str = None):
        """
        初始化图片处理器
        
        Args:
            feishu_access_token: 飞书访问令牌（用于下载飞书私有图片）
        """
        self.feishu_access_token = feishu_access_token
        self.session = requests.Session()
    
    # ============ URL 识别与提取 ============
    
    def is_image_url(self, url: str) -> bool:
        """
        判断URL是否是图片链接
        
        支持:
        - 以图片扩展名结尾的URL
        - 飞书图片URL
        - 含有image关键词的URL
        """
        if not url or not isinstance(url, str):
            return False
        
        url = url.strip()
        if not url.startswith(('http://', 'https://')):
            return False
        
        # 解析URL
        parsed = urlparse(url)
        path = unquote(parsed.path).lower()
        
        # 检查扩展名
        for ext in self.SUPPORTED_EXTENSIONS:
            if path.endswith(ext):
                return True
        
        # 检查飞书图片URL
        if self._is_feishu_image_url(url):
            return True
        
        # 检查是否包含image相关关键词
        if 'image' in path or 'img' in path or 'photo' in path:
            return True
        
        return False
    
    def _is_feishu_image_url(self, url: str) -> bool:
        """判断是否是飞书图片URL"""
        feishu_domains = [
            'feishu.cn',
            'feishu-boe.cn',
            'feishucdn.com',      # 飞书CDN域名
            'pstatp.com',          # 飞书静态资源域名
            'larksuite.com',
            'larkoffice.com',
            'open.feishu.cn',
        ]
        parsed = urlparse(url)
        return any(domain in parsed.netloc for domain in feishu_domains)
    
    def extract_image_urls_from_text(self, text: str) -> List[str]:
        """
        从文本中提取所有图片URL
        
        Args:
            text: 可能包含图片URL的文本
            
        Returns:
            提取到的图片URL列表
        """
        if not text:
            return []
        
        # URL正则表达式
        url_pattern = r'https?://[^\s<>"\']+?\.(?:png|jpg|jpeg|gif|bmp|webp|svg)(?:\?[^\s<>"\']*)?'
        urls = re.findall(url_pattern, text, re.IGNORECASE)
        
        # 去重并保持顺序
        seen = set()
        unique_urls = []
        for url in urls:
            if url not in seen:
                seen.add(url)
                unique_urls.append(url)
        
        return unique_urls
    
    def extract_urls_from_feishu_attachment(self, attachment_field: Any) -> List[str]:
        """
        从飞书附件字段提取图片URL
        
        飞书附件格式示例:
        [
            {"name": "image1.png", "url": "https://..."},
            {"name": "image2.jpg", "file_token": "xxx"}
        ]
        """
        urls = []
        
        if isinstance(attachment_field, str):
            # 可能是单个URL
            if self.is_image_url(attachment_field):
                urls.append(attachment_field)
        
        elif isinstance(attachment_field, list):
            for item in attachment_field:
                if isinstance(item, str):
                    if self.is_image_url(item):
                        urls.append(item)
                elif isinstance(item, dict):
                    # 尝试获取URL
                    url = (item.get('url') or 
                           item.get('file_url') or 
                           item.get('src') or
                           item.get('tmp_url'))
                    if url and self.is_image_url(url):
                        urls.append(url)
        
        elif isinstance(attachment_field, dict):
            url = (attachment_field.get('url') or 
                   attachment_field.get('file_url') or 
                   attachment_field.get('src') or
                   attachment_field.get('tmp_url'))
            if url and self.is_image_url(url):
                urls.append(url)
        
        return urls
    
    # ============ HTML 转换 ============
    
    def url_to_img_tag(self, url: str, alt: str = "图片", 
                       max_width: str = None) -> str:
        """
        将图片URL转换为HTML img标签
        
        Args:
            url: 图片URL
            alt: 替代文本
            max_width: 最大宽度（如 "800px"）
            
        Returns:
            HTML img标签字符串
        """
        if not url or not url.strip():
            return ""
        
        url = url.strip()
        style = f' style="max-width: {max_width};"' if max_width else ""
        return f'<img src="{url}" alt="{alt}"{style} />'
    
    def urls_to_img_tags(self, urls: List[str], separator: str = "<br/>",
                         numbered: bool = True, max_width: str = "800px") -> str:
        """
        将多个图片URL转换为HTML img标签
        
        Args:
            urls: 图片URL列表
            separator: 图片之间的分隔符
            numbered: 是否添加序号标签
            max_width: 最大宽度
            
        Returns:
            HTML字符串
        """
        if not urls:
            return ""
        
        img_tags = []
        for i, url in enumerate(urls, 1):
            url = url.strip()
            if not url:
                continue
            
            if numbered:
                label = f'<p><strong>图片{i}:</strong></p>'
                img_tag = self.url_to_img_tag(url, f"图片{i}", max_width)
                img_tags.append(f"{label}{img_tag}")
            else:
                img_tags.append(self.url_to_img_tag(url, f"图片", max_width))
        
        return separator.join(img_tags)
    
    def format_description_with_images(self, text: str, 
                                        image_urls: List[str] = None,
                                        position: str = "bottom") -> str:
        """
        格式化描述内容，添加图片
        
        Args:
            text: 描述文本
            image_urls: 图片URL列表
            position: 图片位置 ("top" 或 "bottom")
            
        Returns:
            包含图片的HTML描述
        """
        parts = []
        
        # 处理文本
        if text and text.strip():
            text = text.strip()
            # 如果文本不是HTML，包装成段落
            if not text.startswith('<'):
                text = f"<p>{text}</p>"
            parts.append(text)
        
        # 处理图片
        if image_urls:
            img_html = self.urls_to_img_tags(image_urls)
            if img_html:
                if position == "top":
                    parts.insert(0, img_html)
                else:
                    parts.append(img_html)
        
        return "<br/><br/>".join(parts)
    
    def auto_convert_urls_in_text(self, text: str) -> str:
        """
        自动检测并转换文本中的图片URL为img标签
        
        注意：不会重复转换已经是img标签的图片
        
        Args:
            text: 包含图片URL的文本
            
        Returns:
            转换后的文本
        """
        if not text:
            return text
        
        # 如果已经包含img标签，可能已经处理过
        if '<img' in text and 'src=' in text:
            return text
        
        # 图片URL正则
        img_pattern = r'(https?://[^\s<>"\']+\.(?:png|jpg|jpeg|gif|bmp|webp|svg))(?:\?[^\s<>"\']*)?'
        
        def replace_url(match):
            url = match.group(0)
            return f'<img src="{url}" alt="图片" style="max-width: 800px;" />'
        
        return re.sub(img_pattern, replace_url, text, flags=re.IGNORECASE)
    
    # ============ 图片下载与处理 ============
    
    def download_image(self, url: str, save_dir: str = None) -> Optional[str]:
        """
        下载图片到本地
        
        Args:
            url: 图片URL
            save_dir: 保存目录（默认使用临时目录）
            
        Returns:
            本地文件路径，失败返回None
        """
        try:
            # 设置请求头 - 飞书CDN需要完整的浏览器头信息
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Accept-Encoding': 'gzip, deflate, br',
                'Connection': 'keep-alive',
            }
            
            # 如果是飞书图片，添加必要的头信息
            if self._is_feishu_image_url(url):
                # 添加 Referer 头 - 飞书CDN通常需要这个头来验证来源
                headers['Referer'] = 'https://www.feishu.cn/'
                headers['Origin'] = 'https://www.feishu.cn'
                # 如果有token也添加（某些飞书API需要）
                if self.feishu_access_token:
                    headers['Authorization'] = f'Bearer {self.feishu_access_token}'
            
            response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
            response.raise_for_status()
            
            # 获取文件扩展名
            content_type = response.headers.get('Content-Type', '')
            ext = self._get_extension_from_content_type(content_type)
            if not ext:
                # 从URL获取扩展名
                parsed = urlparse(url)
                path = parsed.path.lower()
                for extension in self.SUPPORTED_EXTENSIONS:
                    if path.endswith(extension):
                        ext = extension
                        break
                if not ext:
                    ext = '.png'  # 默认
            
            # 保存文件
            if save_dir is None:
                save_dir = tempfile.gettempdir()
            
            filename = f"feishu_img_{hash(url) % 100000000}{ext}"
            file_path = os.path.join(save_dir, filename)
            
            with open(file_path, 'wb') as f:
                f.write(response.content)
            
            return file_path
            
        except requests.exceptions.HTTPError as e:
            # 详细记录HTTP错误信息，方便调试
            error_info = {
                "url": url,
                "status_code": e.response.status_code if e.response else None,
                "headers": dict(e.response.headers) if e.response else None,
                "body": e.response.text[:500] if e.response else None,
            }
            print(f"下载图片HTTP错误 - {json.dumps(error_info, ensure_ascii=False, indent=2)}")
            return None
        except Exception as e:
            print(f"下载图片失败 {url}: {e}")
            return None
    
    def test_image_download(self, url: str) -> Dict:
        """
        测试图片下载，返回详细的调试信息
        
        Args:
            url: 图片URL
            
        Returns:
            调试信息字典
        """
        result = {
            "url": url,
            "is_feishu_url": self._is_feishu_image_url(url),
            "has_token": bool(self.feishu_access_token),
            "success": False,
            "error": None,
            "response_info": None
        }
        
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                'Accept': 'image/avif,image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8',
                'Accept-Language': 'zh-CN,zh;q=0.9,en;q=0.8',
                'Referer': 'https://www.feishu.cn/',
                'Origin': 'https://www.feishu.cn',
            }
            
            if self.feishu_access_token:
                headers['Authorization'] = f'Bearer {self.feishu_access_token}'
            
            result["request_headers"] = headers
            
            response = self.session.get(url, headers=headers, timeout=30, allow_redirects=True)
            
            result["response_info"] = {
                "status_code": response.status_code,
                "headers": dict(response.headers),
                "content_type": response.headers.get('Content-Type', ''),
                "content_length": len(response.content),
            }
            
            if response.status_code == 200:
                result["success"] = True
            else:
                result["error"] = f"HTTP {response.status_code}"
                result["response_body"] = response.text[:500]
                
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def _get_extension_from_content_type(self, content_type: str) -> Optional[str]:
        """从Content-Type获取扩展名"""
        type_to_ext = {
            'image/png': '.png',
            'image/jpeg': '.jpg',
            'image/jpg': '.jpg',
            'image/gif': '.gif',
            'image/bmp': '.bmp',
            'image/webp': '.webp',
            'image/svg+xml': '.svg',
        }
        # 去掉可能的charset等参数
        main_type = content_type.split(';')[0].strip().lower()
        return type_to_ext.get(main_type)
    
    def download_images(self, urls: List[str], save_dir: str = None) -> List[Dict]:
        """
        批量下载图片
        
        Args:
            urls: 图片URL列表
            save_dir: 保存目录
            
        Returns:
            下载结果列表
        """
        results = []
        for url in urls:
            file_path = self.download_image(url, save_dir)
            results.append({
                'url': url,
                'success': file_path is not None,
                'local_path': file_path
            })
        return results


class FeishuImageHelper:
    """飞书图片专用处理器"""
    
    def __init__(self, app_id: str = None, app_secret: str = None):
        self.app_id = app_id
        self.app_secret = app_secret
        self._access_token = None
        self._token_expires = 0
    
    def get_access_token(self) -> Optional[str]:
        """获取飞书访问令牌"""
        import time
        
        # 检查缓存的token是否还有效
        if self._access_token and time.time() < self._token_expires - 60:
            return self._access_token
        
        if not self.app_id or not self.app_secret:
            return None
        
        try:
            url = "https://open.feishu.cn/open-apis/auth/v3/tenant_access_token/internal"
            response = requests.post(url, json={
                "app_id": self.app_id,
                "app_secret": self.app_secret
            })
            data = response.json()
            
            if data.get('code') == 0:
                self._access_token = data.get('tenant_access_token')
                self._token_expires = time.time() + data.get('expire', 7200)
                return self._access_token
            else:
                print(f"获取飞书token失败: {data.get('msg')}")
                return None
                
        except Exception as e:
            print(f"获取飞书token异常: {e}")
            return None
    
    def get_image_handler(self) -> ImageHandler:
        """获取配置好token的图片处理器"""
        token = self.get_access_token()
        return ImageHandler(feishu_access_token=token)
