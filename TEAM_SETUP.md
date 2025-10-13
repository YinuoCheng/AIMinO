# 团队协作设置指南

## 新团队成员设置步骤

### 1. 克隆项目
```bash
git clone <repository-url>
cd docker-example-omero
```

### 2. 设置环境变量
```bash
# 复制环境变量模板
cp env.example .env

# 编辑 .env 文件，添加你的 API 密钥
nano .env  # 或使用你喜欢的编辑器
```

### 3. 在 .env 文件中设置你的密钥
```bash
OPENAI_API_KEY=sk-your-actual-openai-api-key-here
```

### 4. 启动服务
```bash
# 启动基础 OMERO 服务
docker compose up -d

# 启动包含 LLM Agent 的完整服务
docker compose --profile gui up -d
```

## 团队协作最佳实践

### ✅ 应该做的：
- 每个成员都有自己的 `.env` 文件
- 使用 `env.example` 作为模板
- 定期更新 `env.example` 如果有新的环境变量
- 在 README 中记录新的环境变量

### ❌ 不应该做的：
- 不要提交 `.env` 文件到 git
- 不要分享你的 API 密钥
- 不要在代码中硬编码 API 密钥
- 不要将 `.env` 文件发送给其他成员

## 环境变量管理

### 个人环境变量 (.env)
- 包含个人 API 密钥
- 不会被 git 跟踪
- 每个成员独立管理

### 团队共享变量 (env.example)
- 作为新成员的模板
- 包含所有需要的环境变量名称
- 使用示例值或占位符

### 生产环境变量
- 使用 Docker secrets 或环境变量注入
- 通过 CI/CD 管道管理
- 使用专门的密钥管理服务

## 故障排除

### 常见问题：

1. **API 密钥无效**
   - 检查 `.env` 文件中的密钥是否正确
   - 确认密钥没有多余的空格或引号

2. **环境变量未加载**
   - 确认 `.env` 文件在项目根目录
   - 重启 Docker Compose 服务

3. **权限问题**
   - 检查 `.env` 文件权限：`chmod 600 .env`
   - 确认文件所有者正确

## 安全注意事项

- 定期轮换 API 密钥
- 使用最小权限原则
- 监控 API 使用情况
- 不要在日志中输出敏感信息
