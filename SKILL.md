# OpenClaw Enhanced Memory Skill

## 1. 基本信息

- **技能名称**：openclaw-memory
- **技能版本**：1.0.0
- **作者**：OpenClaw Team
- **功能描述**：企业级增强型结构化记忆系统，支持权威等级、时间推理、冲突解决和记忆衰减等高级功能

## 2. 安装信息

### 依赖要求
- Python 3.8+
- pyyaml (用于Schema支持)

### 安装命令
```bash
# 安装依赖
pip3 install pyyaml

# 将技能复制到OpenClaw扩展目录
cp -r openclaw-memory-skill /path/to/openclaw/extensions/
```

## 3. 功能列表

### 3.1 实体管理

#### 创建实体
**功能描述**：创建新的知识实体，支持元数据和权威等级
**调用方式**：
```bash
python3 scripts/ontology_optimized.py create --type TYPE --props PROPS [--id ID] [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```
**参数说明**：
- `--type`/`-t`：实体类型（必填）
- `--props`/`-p`：实体属性（JSON格式，默认：`{}`）
- `--id`：实体ID（自动生成如果不提供）
- `--confidence`/`-c`：置信度（0-1，默认：0.8）
- `--source`/`-s`：信息来源（默认：manual）
- `--authority`/`-a`：权威等级（truth/reference/observation/manual，默认：manual）
**返回结果**：创建的实体JSON

#### 获取实体
**功能描述**：根据ID获取实体
**调用方式**：
```bash
python3 scripts/ontology_optimized.py get --id ID
```
**参数说明**：
- `--id`：实体ID（必填）
**返回结果**：实体JSON或"Entity not found"

#### 查询实体
**功能描述**：根据类型和属性查询实体
**调用方式**：
```bash
python3 scripts/ontology_optimized.py query --type TYPE --where WHERE [--include-stale]
```
**参数说明**：
- `--type`/`-t`：实体类型（可选）
- `--where`/`-w`：过滤条件（JSON格式，默认：`{}`）
- `--include-stale`：是否包含过期实体（默认：false）
**返回结果**：实体列表JSON

#### 更新实体
**功能描述**：更新实体属性和元数据
**调用方式**：
```bash
python3 scripts/ontology_optimized.py update --id ID --props PROPS [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```
**参数说明**：
- `--id`：实体ID（必填）
- `--props`/`-p`：要更新的属性（JSON格式，必填）
- `--confidence`/`-c`：置信度（0-1，默认：0.8）
- `--source`/`-s`：信息来源（默认：manual）
- `--authority`/`-a`：权威等级（truth/reference/observation/manual，默认：manual）
**返回结果**：更新后的实体JSON或"Entity not found"

#### 删除实体
**功能描述**：删除实体
**调用方式**：
```bash
python3 scripts/ontology_optimized.py delete --id ID
```
**参数说明**：
- `--id`：实体ID（必填）
**返回结果**："Deleted: ID"或"Entity not found"

### 3.2 关系管理

#### 创建关系
**功能描述**：创建实体之间的关系，支持元数据和权威等级
**调用方式**：
```bash
python3 scripts/ontology_optimized.py relate --from FROM_ID --rel RELATION_TYPE --to TO_ID --props PROPS [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```
**参数说明**：
- `--from`：源实体ID（必填）
- `--rel`/`-r`：关系类型（必填）
- `--to`：目标实体ID（必填）
- `--props`/`-p`：关系属性（JSON格式，默认：`{}`）
- `--confidence`/`-c`：置信度（0-1，默认：0.8）
- `--source`/`-s`：信息来源（默认：manual）
- `--authority`/`-a`：权威等级（truth/reference/observation/manual，默认：manual）
**返回结果**：创建的关系JSON

#### 获取相关实体
**功能描述**：获取与指定实体相关的实体
**调用方式**：
```bash
python3 scripts/ontology_optimized.py related --id ID --rel RELATION_TYPE --dir [outgoing|incoming|both]
```
**参数说明**：
- `--id`：实体ID（必填）
- `--rel`/`-r`：关系类型（可选）
- `--dir`/`-d`：关系方向（outgoing/incoming/both，默认：outgoing）
**返回结果**：相关实体列表JSON

### 3.3 知识管理

#### 验证知识图谱
**功能描述**：验证知识图谱是否符合Schema约束
**调用方式**：
```bash
python3 scripts/ontology_optimized.py validate
```
**返回结果**：验证错误列表或"Graph is valid"

#### 清理过期知识
**功能描述**：根据记忆衰减算法清理过期知识
**调用方式**：
```bash
python3 scripts/ontology_optimized.py clean
```
**返回结果**：标记为过期的实体列表或"No stale entities found"

#### 压缩知识
**功能描述**：压缩冗余知识，合并相似实体
**调用方式**：
```bash
python3 scripts/ontology_optimized.py compress
```
**返回结果**：压缩统计信息

#### 迁移知识
**功能描述**：从旧版Ontology迁移知识到增强版
**调用方式**：
```bash
python3 scripts/ontology_optimized.py migrate --from OLD_PATH --to NEW_PATH
```
**参数说明**：
- `--from`：旧版graph.jsonl路径（必填）
- `--to`：新版graph.jsonl路径（默认：memory/ontology/graph.jsonl）
**返回结果**：迁移结果统计信息

### 3.4 配置管理

#### 查看配置
**功能描述**：查看当前配置
**调用方式**：
```bash
python3 scripts/ontology_optimized.py config --show
```
**返回结果**：配置JSON

#### 设置配置
**功能描述**：设置配置参数
**调用方式**：
```bash
python3 scripts/ontology_optimized.py config --set KEY VALUE
```
**参数说明**：
- `--set`：键值对（例如：decay.half_life_days 60）
**返回结果**："Updated config: KEY = VALUE"

## 4. 数据格式

### 4.1 实体格式
```json
{
  "id": "proj_7a1b2c3d",
  "type": "Project",
  "properties": {
    "name": "网站重构",
    "status": "in_progress"
  },
  "metadata": {
    "confidence": 1.0,
    "source": "official_prd.md",
    "authority_level": "truth",
    "created": "2026-04-13T10:00:00Z",
    "updated": "2026-04-13T10:00:00Z",
    "last_used": "2026-04-13T10:00:00Z",
    "valid_from": "2026-04-13T10:00:00Z",
    "valid_until": null,
    "version": 1
  }
}
```

### 4.2 关系格式
```json
{
  "from": "proj_7a1b2c3d",
  "rel": "has_owner",
  "to": "pers_4e5f6a7b",
  "properties": {},
  "metadata": {
    "confidence": 1.0,
    "source": "official_prd.md",
    "authority_level": "truth",
    "created": "2026-04-13T10:01:00Z",
    "updated": "2026-04-13T10:01:00Z",
    "last_used": "2026-04-13T10:01:00Z",
    "valid_from": "2026-04-13T10:01:00Z",
    "valid_until": null,
    "version": 1
  }
}
```

## 5. 权威等级系统

| 等级 | 优先级 | 描述 | 示例来源 |
|------|--------|------|----------|
| truth | 1 | 官方事实，最高权威 | 官方PRD、API文档、HR系统 |
| reference | 2 | 参考资料，较高权威 | 会议纪要、技术方案、设计文档 |
| observation | 3 | 观察数据，中等权威 | AI提取数据、对话记录、日志 |
| manual | 4 | 手动输入，较低权威 | 用户直接输入、临时记录 |

## 6. 记忆衰减机制

- **半衰期**：知识的热度值在半衰期后减半（默认30天）
- **最小分数**：低于此分数的知识会被标记为过期（默认0.1）
- **计算公式**：`Score = Confidence * (0.5)^(TimeDiff / HalfLife) * (1 + AuthorityFactor)`
- **权威因子**：基于权威等级的衰减调整因子（truth=1.25, reference=1.167, observation=1.125, manual=1.0）

## 7. 冲突解决策略

1. **权威等级优先**：高权威等级的知识自动覆盖低权威等级的知识
2. **置信度次之**：相同权威等级下，置信度高的知识优先
3. **时间最新优先**：相同权威等级和置信度下，最新的知识优先
4. **默认保留现有**：以上条件都相同时，保留现有知识

## 8. 与旧版Ontology的兼容性

- **命令行兼容**：保持与旧版完全相同的命令行接口
- **存储格式兼容**：增强版可以直接加载旧版的graph.jsonl文件
- **自动升级**：加载旧版数据时自动添加默认元数据
- **迁移工具**：提供`migrate`命令用于完整迁移

## 9. 最佳实践

1. **使用适当的权威等级**：为不同来源的知识设置合适的权威等级
2. **提供详细的来源信息**：记录信息的来源以便追溯
3. **设置合理的置信度**：根据信息的可靠性设置置信度
4. **定期维护知识库**：使用`clean`和`compress`命令保持知识库健康
5. **定义Schema**：使用schema.yaml定义实体类型和约束，确保数据一致性

## 10. 故障排除

### 常见问题

1. **权限错误**：确保脚本对memory目录有写权限
2. **Schema验证失败**：检查实体属性是否符合schema.yaml中的约束
3. **迁移失败**：确保旧版graph.jsonl文件存在且格式正确
4. **性能问题**：大型知识库建议增加半衰期或提高最小分数阈值

### 日志和调试

- 所有操作记录保存在`memory/ontology/graph.jsonl`
- 使用`validate`命令检查schema违规
- 使用`config --show`查看当前配置

## 11. 扩展接口

### Python API

增强版提供完整的Python API，便于其他模块集成：

```python
from scripts.ontology_optimized import EntityManager, RelationManager, GraphQuery

# 创建实体
entity = EntityManager.create_entity("Project", {"name":"网站重构"}, "memory/ontology/graph.jsonl")

# 创建关系
RelationManager.create_relation(entity["id"], "has_owner", person_id, {}, "memory/ontology/graph.jsonl")

# 查询实体
entities = GraphQuery.query_entities("Project", {"status":"in_progress"}, "memory/ontology/graph.jsonl")
```

### 自定义组件

增强版采用模块化设计，支持自定义扩展：
- **自定义压缩算法**：扩展KnowledgeCompressor类
- **自定义冲突规则**：扩展ConflictManager类
- **自定义存储后端**：扩展FileManager类

## 12. 更新日志

### v1.0.0 (2026-04-13)
- 初始版本
- 实现权威等级系统
- 实现时间推理和版本控制
- 实现冲突检测和解决
- 实现记忆衰减机制
- 实现知识压缩功能
- 提供完整的命令行接口
- 支持与旧版Ontology兼容
- 提供迁移工具
