"""
获取TAPD需求单的所有字段
用于查看需求单的完整字段结构
"""
import requests
import base64
import json

# ========== 配置信息 ==========
API_USER = "GNxpkwrr"
API_PASSWORD = "86EE396F-6733-051C-3BA9-1243A2E8AA36"
WORKSPACE_ID = "41827997"

# ========== 认证设置 ==========
auth_string = f"{API_USER}:{API_PASSWORD}"
auth_bytes = base64.b64encode(auth_string.encode('utf-8')).decode('utf-8')
headers = {
    "Authorization": f"Basic {auth_bytes}",
}

def get_stories_list(limit=1):
    """获取需求列表"""
    url = "https://api.tapd.cn/stories"
    params = {
        "workspace_id": WORKSPACE_ID,
        "limit": limit
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data.get("status") == 1:
        return data.get("data", [])
    else:
        print(f"请求失败: {data.get('info')}")
        return []

def get_story_by_id(story_id):
    """根据ID获取单个需求详情"""
    url = "https://api.tapd.cn/stories"
    params = {
        "workspace_id": WORKSPACE_ID,
        "id": story_id
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data.get("status") == 1:
        stories = data.get("data", [])
        if stories and len(stories) > 0:
            return stories[0].get("Story", stories[0])
    return {}

def get_custom_fields():
    """获取需求的自定义字段配置"""
    url = "https://api.tapd.cn/workflows/custom_fields_settings"
    params = {
        "workspace_id": WORKSPACE_ID,
        "system": "story"  # bug/story/task
    }
    try:
        response = requests.get(url, headers=headers, params=params)
        if response.status_code != 200:
            print(f"请求失败, 状态码: {response.status_code}")
            return {}
        data = response.json()
        
        if data.get("status") == 1:
            return data.get("data", {})
        else:
            print(f"获取自定义字段失败: {data.get('info')}")
            return {}
    except Exception as e:
        print(f"获取自定义字段异常: {e}")
        return {}

def main():
    print("=" * 60)
    print("TAPD 需求单字段查询工具")
    print("=" * 60)
    
    # 1. 获取一个需求单示例，查看所有字段
    print("\n【方式1】获取需求单示例，查看所有字段:")
    print("-" * 40)
    
    stories = get_stories_list(limit=1)
    if stories:
        story_data = stories[0].get("Story", stories[0])
        print("\n需求单所有字段:")
        for key, value in story_data.items():
            # 高亮显示常用重要字段
            if key in ['name', 'priority', 'owner', 'creator', 'status', 'iteration_id', 'category_id', 'workitem_type_id']:
                print(f"  ★ {key}: {value}")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("【重点字段确认】")
        print("-" * 40)
        print(f"  需求名称: name = {story_data.get('name', '(未设置)')}")
        print(f"  优先级: priority = {story_data.get('priority', '(未设置)')}")
        print(f"  处理人: owner = {story_data.get('owner', '(未设置)')}")
        print(f"  创建人: creator = {story_data.get('creator', '(未设置)')}")
        print(f"  状态: status = {story_data.get('status', '(未设置)')}")
        print(f"  迭代ID: iteration_id = {story_data.get('iteration_id', '(未设置)')}")
        print(f"  需求分类ID: category_id = {story_data.get('category_id', '(未设置)')}")
        print(f"  需求类别ID: workitem_type_id = {story_data.get('workitem_type_id', '(未设置)')}")
    else:
        print("  未找到需求单,可能项目中暂无需求或权限问题")
    
    # 2. 获取自定义字段配置
    print("\n" + "=" * 60)
    print("【方式2】获取自定义字段配置:")
    print("-" * 40)
    
    custom_fields = get_custom_fields()
    if custom_fields:
        print("\n自定义字段列表:")
        if isinstance(custom_fields, list):
            for field in custom_fields:
                field_data = field.get("CustomFieldConfig", field)
                print(f"  - {field_data.get('custom_field')}: {field_data.get('name')} (类型: {field_data.get('type')})")
        elif isinstance(custom_fields, dict):
            if "CustomFieldConfig" in custom_fields:
                for field in custom_fields.get("CustomFieldConfig", []):
                    print(f"  - {field.get('custom_field')}: {field.get('name')} (类型: {field.get('type')})")
            else:
                print(json.dumps(custom_fields, indent=2, ensure_ascii=False))
    else:
        print("  未获取到自定义字段配置")
    
    # 3. 打印API文档参考
    print("\n" + "=" * 60)
    print("【标准字段参考】(来自TAPD API文档)")
    print("-" * 40)
    standard_fields = {
        "name": "需求名称",
        "priority": "优先级 (1-4, 1最高)",
        "priority_label": "优先级标签",
        "business_value": "业务价值",
        "version": "版本",
        "module": "模块",
        "owner": "处理人",
        "creator": "创建人",
        "developer": "开发人员",
        "begin": "预计开始",
        "due": "预计结束",
        "status": "状态",
        "completed": "完成时间",
        "iteration_id": "迭代ID",
        "category_id": "需求分类ID",
        "workitem_type_id": "需求类别ID",
        "release_id": "发布计划ID",
        "source": "需求来源",
        "type": "需求类型",
        "parent_id": "父需求ID",
        "description": "需求描述",
        "label": "标签",
        "size": "规模",
        "effort": "预估工时",
        "effort_completed": "完成工时",
    }
    for field, name in standard_fields.items():
        print(f"  {field}: {name}")

if __name__ == "__main__":
    main()
