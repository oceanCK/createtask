"""
获取TAPD缺陷单的所有字段
用于查看缺陷单的完整字段结构
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

def get_bugs_list(limit=1):
    """获取缺陷列表"""
    url = "https://api.tapd.cn/bugs"
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

def get_bug_by_id(bug_id):
    """根据ID获取单个缺陷详情"""
    url = "https://api.tapd.cn/bugs"
    params = {
        "workspace_id": WORKSPACE_ID,
        "id": 1141827997001224459
    }
    response = requests.get(url, headers=headers, params=params)
    data = response.json()
    
    if data.get("status") == 1:
        bugs = data.get("data", [])
        if bugs and len(bugs) > 0:
            return bugs[0].get("Bug", bugs[0])
    return {}

def get_custom_fields():
    """获取缺陷的自定义字段配置"""
    url = "https://api.tapd.cn/workflows/custom_fields_settings"
    params = {
        "workspace_id": WORKSPACE_ID,
        "system": "bug"  # bug/story/task
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
    print("TAPD 缺陷单字段查询工具")
    print("=" * 60)
    
    # 1. 获取一个缺陷单示例，查看所有字段
    print("\n【方式1】获取缺陷单示例，查看所有字段:")
    print("-" * 40)
    
    bugs = get_bugs_list(limit=1)
    if bugs:
        bug_data = bugs[0].get("Bug", bugs[0])
        print("\n缺陷单所有字段:")
        for key, value in bug_data.items():
            # 高亮显示重现规律和版本号相关字段
            if key in ['frequency', 'version_report', 'version_test', 'version_fix', 'version_close']:
                print(f"  ★ {key}: {value}")
            else:
                print(f"  {key}: {value}")
        
        print("\n" + "=" * 60)
        print("【重点字段确认】")
        print("-" * 40)
        print(f"  重现规律字段: frequency = {bug_data.get('frequency', '(未设置)')}")
        print(f"  发现版本字段: version_report = {bug_data.get('version_report', '(未设置)')}")
        print(f"  验证版本字段: version_test = {bug_data.get('version_test', '(未设置)')}")
        print(f"  合入版本字段: version_fix = {bug_data.get('version_fix', '(未设置)')}")
    else:
        print("  未找到缺陷单,可能项目中暂无缺陷或权限问题")
    
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
        "frequency": "重现规律",
        "version_report": "发现版本",
        "version_test": "验证版本", 
        "version_fix": "合入版本",
        "version_close": "关闭版本",
        "severity": "严重程度",
        "priority": "优先级",
        "current_owner": "处理人",
        "module": "模块",
        "bugtype": "缺陷类型",
        "source": "缺陷根源",
        "testphase": "测试阶段",
        "originphase": "发现阶段",
        "sourcephase": "引入阶段",
    }
    for field, name in standard_fields.items():
        print(f"  {field}: {name}")

if __name__ == "__main__":
    main()
