# Neo4j AuraDB 配置指南

## 什么是 AuraDB？

Neo4j AuraDB 是 Neo4j 的云托管服务，提供：
- 免费层（适合开发和小规模使用）
- 自动化备份和维护
- 无需管理自己的服务器
- 安全的连接（TLS 加密）

## 获取 AuraDB 连接字符串

### 步骤 1：创建账户

1. 访问 [Neo4j Aura](https://neo4j.com/cloud/aura/)
2. 注册或登录账户
3. 创建一个新的实例（选择免费层）

### 步骤 2：获取连接信息

在实例详情页面，你会看到以下信息：
- **Connection URI**: 这是完整的连接字符串，例如：
  ```
  neo4j+s://username:password@xxxxx.databases.neo4j.io
  ```
- **Username**: 用户名
- **Password**: 密码（创建时设置，需要保存）

### 步骤 3：配置 Evolith

在项目根目录的 `.env` 文件中添加：

```env
# Neo4j AuraDB 配置
NEO4J_URI=neo4j+s://username:password@xxxxx.databases.neo4j.io
```

或者如果只想设置用户名和密码：

```env
NEO4J_URI=neo4j+s://xxxxx.databases.neo4j.io
NEO4J_USER=username
NEO4J_PASSWORD=password
```

**重要**：
- 将 `username`、`password` 和 `xxxxx.databases.neo4j.io` 替换为你的实际值
- 连接字符串中的 `:` 是用户名和密码的分隔符
- 保留 `neo4j+s://` 协议前缀

### 步骤 4：验证配置

启动应用：

```bash
npm run dev
```

如果连接成功，后端日志会显示：
```
Neo4j Driver 初始化成功: neo4j+s://...
Neo4j 连接验证成功
```

## 故障排除

### 连接失败

如果看到以下错误：
- `Neo4j Driver 初始化失败`
- `连接被拒绝`

检查清单：
1. ✅ 连接字符串格式正确（包含用户名和密码）
2. ✅ 密码中没有特殊字符转义问题
3. ✅ 网络可以访问 Neo4j AuraDB
4. ✅ AuraDB 实例状态为 "Running"

### 认证错误

错误信息包含 `authentication` 或 `unauthorized`：

- 确认用户名和密码正确
- 尝试重新生成密码（在 AuraDB 控制台）
- 确认连接字符串格式：`neo4j+s://username:password@host`

### 端口问题

错误信息包含 `connection refused` 或 `timeout`：

- 确认使用正确的协议前缀（`neo4j+s://`）
- 检查防火墙设置
- AuraDB 使用标准端口（443 for URI, 7687 for Bolt）

## 本地 Neo4j 替代方案

如果需要使用本地 Neo4j 而不是 AuraDB：

```env
# 本地 Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
```

启动本地 Neo4j：

```bash
docker compose up -d
```

## 免费层限制

AuraDB 免费层（Free tier）的典型限制：

| 资源 | 限制 |
|--------|------|
| 存储空间 | 约 1GB |
| 节点数量 | 约 500,000 |
| 边数量 | 约 500,000 |
| 并发连接 | 有限 |

注意：如果项目规模较大，可能需要升级到付费层。

## 相关链接

- [Neo4j AuraDB 官方文档](https://neo4j.com/docs/aura/auradb/)
- [Neo4j Cloud Console](https://console.neo4j.io/)
- [Neo4j 驱动文档](https://neo4j.com/docs/python-manual/current/)

## 从 Zep 迁移到 AuraDB

如果你之前使用 Zep Cloud，迁移到 AuraDB 的好处：

1. **成本降低**：AuraDB 免费层可用于开发和测试
2. **数据主权**：完全控制你的数据
3. **性能提升**：本地查询更快，不受 API 限制
4. **简化架构**：不再依赖第三方服务

详细的迁移文档请参考 [NEO4J_MIGRATION.md](./NEO4J_MIGRATION.md)
