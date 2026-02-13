# 创建需求单

## SDK 方法名

* addBug

## URL

* https://api.tapd.cn/bugs

## 支持格式

* JSON/XML（默认JSON格式）

## HTTP请求方式

POST

## 请求参数

| 字段名 | 必选 | 类型及范围 | 说明 |
|--------|------|------------|------|
| workspace_id | 是 | integer | 项目ID |
| title | 是 | string | 缺陷标题 |
| priority | 否 | string | 优先级。为了兼容自定义优先级，请使用 priority_label 字段 |
| priority_label | 否 | string | 优先级。推荐使用这个字段 |
| severity | 否 | string | 严重程度 |
| module | 否 | string | 模块 |
| feature | 否 | string | 特性 |
| release_id | 否 | integer | 发布计划 |
| version_report | 否 | string | 发现版本 |
| version_test | 否 | string | 验证版本 |
| version_fix | 否 | string | 合入版本 |
| version_close | 否 | string | 关闭版本 |
| baseline_find | 否 | string | 发现基线 |
| baseline_join | 否 | string | 合入基线 |
| baseline_test | 否 | string | 验证基线 |
| baseline_close | 否 | string | 关闭基线 |
| current_owner | 否 | string | 处理人 |
| template_id | 否 | integer | 模板ID |
| cc | 否 | string | 抄送人 |
| reporter | 否 | string | 创建人 |
| participator | 否 | string | 参与人 |
| te | 否 | string | 测试人员 |
| de | 否 | string | 开发人员 |
| auditer | 否 | string | 审核人 |
| confirmer | 否 | string | 验证人 |
| fixer | 否 | string | 修复人 |
| closer | 否 | string | 关闭人 |
| lastmodify | 否 | string | 最后修改人 |
| in_progress_time | 否 | datetime | 接受处理时间 |
| verify_time | 否 | datetime | 验证时间 |
| reject_time | 否 | datetime | 拒绝时间 |
| begin | 否 | date | 预计开始 |
| due | 否 | date | 预计结束 |
| deadline | 否 | date | 解决期限 |
| iteration_id | 否 | string | 迭代ID |
| size | 否 | string | 规模 |
| os | 否 | string | 操作系统 |
| platform | 否 | string | 软件平台 |
| testmode | 否 | string | 测试方式 |
| testphase | 否 | string | 测试阶段 |
| testtype | 否 | string | 测试类型 |
| source | 否 | string | 缺陷根源 |
| bugtype | 否 | string | 缺陷类型 |
| frequency | 否 | string | 重现规律 |
| originphase | 否 | string | 发现阶段 |
| sourcephase | 否 | string | 引入阶段 |
| resolution | 否 | string | 解决方法 |
| estimate | 否 | integer | 预计解决时间 |
| description | 否 | string | 详细描述 |
| label | 否 | string | 标签，标签不存在时将自动创建，多个以英文竖线分隔 |
| effort | 否 | integer | 预估工时 |
| is_apply_template_default_value | 否 | integer | 是否从模板继承默认值（传值=1继承模板默认值） |
| cus_{$自定义字段别名} | 否 | string | 缺陷自定义字段值，参数名会由后台自动转义为custom_field_* |
| custom_field_* | 否 | string/integer | 缺陷自定义字段参数，具体字段名通过接口获取 |
| custom_plan_field_* | 否 | string/integer | 自定义计划应用参数，具体字段名通过接口获取 |