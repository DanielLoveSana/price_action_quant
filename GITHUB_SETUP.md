# GitHub 仓库设置指南

## 项目状态
- ✅ Git仓库已初始化
- ✅ 初始提交已完成 (Phase 1.2 - 数据模块)
- ✅ .gitignore已配置 (排除venv、缓存等)

## 推送到GitHub的步骤

### 选项1: 创建新仓库 (推荐)

1. **登录GitHub** 并创建新仓库:
   - 仓库名: `price-action-quant` (或您喜欢的名称)
   - 描述: "价格行为学量化分析系统"
   - 选择: **私有仓库** (建议)
   - 不要初始化README、.gitignore等

2. **获取仓库URL**:
   ```
   https://github.com/<您的用户名>/price-action-quant.git
   ```

3. **添加远程仓库并推送**:
   ```bash
   cd /home/admin/.openclaw/workspace-coding-assistant/price_action_quant
   
   # 添加远程仓库
   git remote add origin https://github.com/<您的用户名>/price-action-quant.git
   
   # 重命名分支为main (可选)
   git branch -M main
   
   # 推送代码
   git push -u origin main
   ```

### 选项2: 使用现有仓库

1. **添加远程仓库**:
   ```bash
   git remote add origin <您的仓库URL>
   ```

2. **推送代码**:
   ```bash
   git push -u origin main
   ```

## 配置Git用户信息 (如果需要)

如果您想使用自己的身份提交:

```bash
git config --global user.name "您的姓名"
git config --global user.email "您的邮箱@example.com"
```

## 阶段提交策略

建议在每个Phase完成后提交:

### Phase 1 提交计划
- ✅ **Phase 1.2**: 数据接入模块 (已提交)
- 🔄 **Phase 1.3**: 市场结构因子 (完成后提交)
- 🔄 **Phase 1.4**: 关键价位因子 (完成后提交)
- 🔄 **Phase 1.5**: 基础可视化 (完成后提交)
- 🔄 **Phase 1.6**: 自测验收 (完成后提交)

### 提交命令示例
```bash
# 添加所有更改
git add .

# 提交当前阶段
git commit -m "Phase 1.3: Market structure factors

- Support/resistance detection algorithms
- Trend line calculation
- Volume profile analysis
- Market regime classification"

# 推送到GitHub
git push
```

## 分支策略建议

```bash
# 创建开发分支
git checkout -b develop

# 功能分支 (每个新功能)
git checkout -b feature/data-module
git checkout -b feature/factors-market-structure
git checkout -b feature/visualization

# 合并到develop
git checkout develop
git merge --no-ff feature/data-module

# 发布时合并到main
git checkout main
git merge --no-ff develop
git tag -a v1.0.0 -m "Phase 1 complete"
```

## 备份和恢复

### 从GitHub恢复项目
```bash
# 克隆仓库
git clone https://github.com/<您的用户名>/price-action-quant.git

# 恢复虚拟环境
cd price-action-quant
python -m venv venv
source venv/bin/activate
pip install -r requirements_3.11_fixed.txt
```

## 注意事项

1. **不要提交敏感信息**:
   - API密钥、密码等
   - 个人配置文件
   - 大型数据文件

2. **保持.gitignore更新**:
   - 虚拟环境文件
   - 缓存文件
   - 临时文件
   - IDE配置文件

3. **提交信息规范**:
   - 第一行: 简短描述
   - 空行
   - 详细说明更改内容
   - 关联的Issue/PR编号

## 当前提交状态

```bash
# 查看提交历史
git log --oneline

# 查看文件状态
git status

# 查看远程仓库
git remote -v
```

## 需要您提供的信息

1. GitHub仓库URL (创建后)
2. 是否使用私有仓库 (建议是)
3. 分支命名偏好 (main vs master)
4. 提交者身份信息 (姓名/邮箱)