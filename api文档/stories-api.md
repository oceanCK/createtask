# 创建需求单

## SDK 方法名

* addStory

## URL

* https://api.tapd.cn/stories

## 支持格式

* JSON/XML（默认JSON格式）

## HTTP请求方式

POST

## 请求参数

| 字段名 | 必选 | 类型及范围 | 说明 |
|--------|------|------------|------|
| workspace_id | 是 | integer | 项目ID |
| name | 是 | string | 标题 |
| priority | 否 | string | 优先级。为了兼容自定义优先级，请使用 priority_label 字段，详情参考：如何兼容自定义优先级 |
| priority_label | 否 | string | 优先级。推荐使用这个字段 |
| business_value | 否 | integer | 业务价值 |
| version | 否 | string | 版本 |
| module | 否 | string | 模块 |
| test_focus | 否 | string | 测试重点 |
| size | 否 | integer | 规模 |
| owner | 否 | string | 处理人 |
| cc | 否 | string | 抄送人 |
| creator | 否 | string | 创建人 |
| developer | 否 | string | 开发人员 |
| begin | 否 | date | 预计开始 |
| due | 否 | date | 预计结束 |
| iteration_id | 否 | string | 迭代ID |
| templated_id | 否 | integer | 模板ID |
| parent_id | 否 | integer | 父需求ID |
| effort | 否 | string | 预估工时 |
| effort_completed | 否 | string | 完成工时 |
| remain | 否 | float | 剩余工时 |
| exceed | 否 | float | 超出工时 |
| category_id | 否 | integer | 需求分类 |
| workitem_type_id | 否 | integer | 需求类别 |
| release_id | 否 | integer | 发布计划 |
| source | 否 | string | 来源 |
| type | 否 | string | 类型 |
| feature | 否 | string | 特性 |
| tech_risk | 否 | string | 技术风险 |
| business_value | 否 | string | 业务价值 |
| description | 否 | string | 详细描述 |
| label | 否 | string | 标签，标签不存在时将自动创建，多个以英文坚线分格 |
| cus_{$自定义字段别名} | 否 | string | 自定义字段值，参数名会由后台自动转义为custom_field_*，如：cus_自定义字段的名称 |
| custom_field_* | 否 | string或者integer | 自定义字段参数，具体字段名通过接口 获取需求自定义字段配置 获取 |
| custom_plan_field_* | 否 | string或者integer | 自定义计划应用参数，具体字段名通过接口 获取自定义计划应用 获取 |
| is_apply_template_default_value | 否 | integer | 是否从模板继承默认值、保密设置（传值=1继承模板默认值） |
| apply_template | 否 | string | 模版选项,支持多个选项传入,使用','隔开 如: "option1,option2" 当前支持参数:preset_stories(支持创建需求模板预设子需求),preset_tasks(支持创建需求模板预设子任务) |
