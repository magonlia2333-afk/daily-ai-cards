# Daily AI Cards

GitHub Actions 每天北京时间 09:00、16:00 运行两条独立内容线：上午生成 1 张信息密度适中的 AI 新闻长图；下午生成 3-6 张更详尽、可照做的 AI 技能/工作流卡片。每个项目单独发送邮件。

## 必需 Secrets

- `OPENAI_API_KEY`: 用于筛选和撰写结构化文案
- `RESEND_API_KEY`: [Resend](https://resend.com) 邮件 API Key
- `MAIL_FROM`: 已在 Resend 验证的发件地址
- `MAIL_TO`: 接收地址
- `GH_TOKEN`: GitHub PAT（推荐，提升 API 限额）

所有数字和产品事实必须来自 `evidence.json`；卡片会显示来源、更新时间和官方/第三方类型。图像使用 SVG 转 PNG，避免图片模型造成中文字形错误。
