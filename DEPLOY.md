# 部署到 GitHub

当前目录还没有 GitHub 登录态或远程仓库，因此不能代替你创建并推送到个人账号。完成下面步骤后，工作流即可运行。

```powershell
gh auth login
git init
git add .
git commit -m "feat: daily AI cards workflow"
gh repo create daily-ai-cards --private --source . --remote origin --push
```

在仓库的 Settings -> Secrets and variables -> Actions 中添加：

- `OPENAI_API_KEY`
- `OPENAI_BASE_URL`：官方 OpenAI 留空；第三方中转站填 OpenAI 兼容 API 地址
- `OPENAI_MODEL`：中转站支持的模型名
- `RESEND_API_KEY`
- `MAIL_FROM`：Resend 已验证的发件地址
- `MAIL_TO`：你的收件地址
- GitHub API 使用 Actions 自带的 `github.token`，无需额外配置 PAT

然后在 Actions 页面手动运行一次 `Daily AI Cards`，确认邮件和 PNG 正常后再等待定时任务。GitHub Actions 的定时任务可能有几分钟延迟。

上午运行发送 1 封新闻邮件和 1 张长图；下午运行发送 3-6 封技能邮件，每封对应一个技巧和一张 PNG 卡片。
