# OpenClaw Enhanced Memory Skill

An enhanced ontology-based memory system for OpenClaw that implements enterprise-grade knowledge management features.

## Features

### Authority Ranking (Weight & Permission Levels)
- **Truth Level**: Official PRD, API documentation (highest authority)
- **Reference Level**: Meeting minutes, technical plans
- **Observation Level**: AI extracted data, conversation logs
- **Manual Level**: User direct input (lowest authority)

### Temporal Reasoning
- Complete timestamp tracking (created, updated, last_used)
- Version control for all entities and relations
- Validity period tracking (valid_from, valid_until)

### Conflict Resolution
- Automatic conflict detection between entities
- Resolution based on authority level, confidence, and recency
- Configurable auto-resolution rules

### Memory Decay
- Exponential decay based on last usage time
- Configurable half-life and minimum score threshold
- Automatic identification of stale knowledge

### Knowledge Compression
- Redundant knowledge detection
- Similar entity merging
- Maintainable knowledge graph size

### Enhanced Metadata
- Confidence scores (0-1)
- Source tracking
- Usage statistics
- Version information

## Installation

1. Clone or copy the project to your OpenClaw extensions directory:

```bash
cp -r openclaw-memory-skill /path/to/openclaw/extensions/
```

2. Ensure Python 3.8+ is installed:

```bash
python3 --version
```

3. Install required dependencies:

```bash
# Required for YAML schema support
pip3 install pyyaml
```

## Quick Start

### 1. Create Entities with Metadata

```bash
# Create a project with high authority (truth level)
python3 scripts/ontology_optimized.py create --type Project --props '{"name":"网站重构","status":"in_progress"}' --confidence 1.0 --source "official_prd.md" --authority "truth"

# Create a person
python3 scripts/ontology_optimized.py create --type Person --props '{"name":"张三","role":"项目经理"}' --confidence 0.9 --source "hr_system"

# Create a task
python3 scripts/ontology_optimized.py create --type Task --props '{"title":"需求分析","status":"open"}' --confidence 0.8 --source "meeting_minutes.md" --authority "reference"
```

### 2. Create Relations

```bash
# Set project owner
python3 scripts/ontology_optimized.py relate --from proj_7a1b2c3d --rel has_owner --to pers_4e5f6a7b --confidence 1.0 --source "official_prd.md"

# Assign task to person
python3 scripts/ontology_optimized.py relate --from task_8b9c0d1e --rel assigned_to --to pers_4e5f6a7b --confidence 0.9 --source "project_plan.md"
```

### 3. Query Knowledge

```bash
# Get entity by ID
python3 scripts/ontology_optimized.py get --id proj_7a1b2c3d

# Query open tasks
python3 scripts/ontology_optimized.py query --type Task --where '{"status":"open"}'

# List all persons
python3 scripts/ontology_optimized.py list --type Person

# Get project members
python3 scripts/ontology_optimized.py related --id proj_7a1b2c3d --rel has_member
```

### 4. Knowledge Management

```bash
# Validate graph against schema
python3 scripts/ontology_optimized.py validate

# Clean stale knowledge
python3 scripts/ontology_optimized.py clean

# Compress redundant knowledge
python3 scripts/ontology_optimized.py compress
```

### 5. Configuration

```bash
# Show current configuration
python3 scripts/ontology_optimized.py config --show

# Set decay half-life to 60 days
python3 scripts/ontology_optimized.py config --set decay.half_life_days 60
```

## Architecture

### Core Components

1. **Entity Manager** - Handles entity lifecycle with metadata
2. **Relation Manager** - Manages entity relationships
3. **Conflict Manager** - Detects and resolves knowledge conflicts
4. **Knowledge Compressor** - Removes redundancy and compresses knowledge
5. **Graph Validator** - Validates graph against schema constraints
6. **File Manager** - Handles safe file operations
7. **Config Manager** - Manages system configuration

### Data Storage

The ontology is stored in JSON Lines format at `memory/ontology/graph.jsonl`. Each line represents an operation:

```jsonl
{"op":"create","entity":{"id":"proj_7a1b2c3d","type":"Project","properties":{"name":"网站重构","status":"in_progress"},"metadata":{"confidence":1.0,"source":"official_prd.md","authority_level":"truth","created":"2026-04-13T10:00:00Z","updated":"2026-04-13T10:00:00Z","last_used":"2026-04-13T10:00:00Z","valid_from":"2026-04-13T10:00:00Z","valid_until":null,"version":1}},"timestamp":"2026-04-13T10:00:00Z"}
{"op":"relate","from":"proj_7a1b2c3d","rel":"has_owner","to":"pers_4e5f6a7b","properties":{},"metadata":{"confidence":1.0,"source":"official_prd.md","authority_level":"truth","created":"2026-04-13T10:01:00Z","updated":"2026-04-13T10:01:00Z","last_used":"2026-04-13T10:01:00Z","valid_from":"2026-04-13T10:01:00Z","valid_until":null,"version":1},"timestamp":"2026-04-13T10:01:00Z"}
```

### Schema Definition

The schema defines entity types, properties, and relationships:

```yaml
types:
  Project:
    required:
      - name
      - status
    status_enum:
      - planning
      - in_progress
      - completed
      - cancelled

relations:
  has_owner:
    from_types: [Project]
    to_types: [Person]
    cardinality: one_to_one
```

## API Reference

### Entity Operations

#### Create Entity
```bash
python3 scripts/ontology_optimized.py create --type TYPE --props PROPS [--id ID] [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```

#### Get Entity
```bash
python3 scripts/ontology_optimized.py get --id ID
```

#### Query Entities
```bash
python3 scripts/ontology_optimized.py query --type TYPE --where WHERE [--include-stale]
```

#### List Entities
```bash
python3 scripts/ontology_optimized.py list --type TYPE [--include-stale]
```

#### Update Entity
```bash
python3 scripts/ontology_optimized.py update --id ID --props PROPS [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```

#### Delete Entity
```bash
python3 scripts/ontology_optimized.py delete --id ID
```

### Relation Operations

#### Create Relation
```bash
python3 scripts/ontology_optimized.py relate --from FROM_ID --rel RELATION_TYPE --to TO_ID --props PROPS [--confidence CONFIDENCE] [--source SOURCE] [--authority AUTHORITY]
```

#### Get Related Entities
```bash
python3 scripts/ontology_optimized.py related --id ID --rel RELATION_TYPE --dir [outgoing|incoming|both]
```

### Knowledge Management

#### Validate Graph
```bash
python3 scripts/ontology_optimized.py validate
```

#### Clean Stale Knowledge
```bash
python3 scripts/ontology_optimized.py clean
```

#### Compress Knowledge
```bash
python3 scripts/ontology_optimized.py compress
```

#### Configuration
```bash
python3 scripts/ontology_optimized.py config --show
python3 scripts/ontology_optimized.py config --set KEY VALUE
```

## Integration with OpenClaw

### Usage in Python

```python
#!/usr/bin/env python3

from pathlib import Path
import sys

# Add the skill directory to path
sys.path.append(str(Path(__file__).parent.parent))

from scripts.ontology_optimized import EntityManager, RelationManager, GraphQuery, FileManager

# Define paths
GRAPH_PATH = "memory/ontology/graph.jsonl"

# Create entities
project = EntityManager.create_entity(
    "Project",
    {"name": "OpenClaw Enhancement", "status": "in_progress"},
    GRAPH_PATH,
    confidence=0.9,
    source="github_issue",
    authority="reference"
)

person = EntityManager.create_entity(
    "Person",
    {"name": "OpenClaw User", "role": "Developer"},
    GRAPH_PATH,
    confidence=1.0,
    source="system",
    authority="truth"
)

# Create relation
RelationManager.create_relation(
    project["id"],
    "has_owner",
    person["id"],
    {},
    GRAPH_PATH,
    confidence=0.9,
    source="github_issue",
    authority="reference"
)

# Query knowledge
open_projects = GraphQuery.query_entities(
    "Project",
    {"status": "in_progress"},
    GRAPH_PATH
)

print("Open Projects:")
for proj in open_projects:
    print(f"- {proj['properties']['name']} (ID: {proj['id']})")
```

### Integration Example

Create a file `openclaw_integration.py` in your project:

```python
#!/usr/bin/env python3
"""
OpenClaw Memory Skill Integration Example
"""

import json
import sys
from pathlib import Path

# Add this skill to Python path
SKILL_PATH = Path("/path/to/openclaw/extensions/openclaw-memory-skill")
sys.path.append(str(SKILL_PATH))

from scripts.ontology_optimized import (
    EntityManager,
    RelationManager,
    GraphQuery,
    ConflictManager,
    KnowledgeManager
)

class OpenClawMemory:
    """Memory interface for OpenClaw"""
    
    def __init__(self, graph_path="memory/ontology/graph.jsonl"):
        self.graph_path = str(SKILL_PATH / graph_path)
    
    def remember(self, entity_type, properties, confidence=0.8, source="openclaw"):
        """Remember a fact"""
        return EntityManager.create_entity(
            entity_type,
            properties,
            self.graph_path,
            confidence=confidence,
            source=source,
            authority="observation"
        )
    
    def recall(self, entity_type, filters=None):
        """Recall facts"""
        return GraphQuery.query_entities(
            entity_type,
            filters or {},
            self.graph_path
        )
    
    def connect(self, from_entity, relation, to_entity, confidence=0.8, source="openclaw"):
        """Connect two entities"""
        return RelationManager.create_relation(
            from_entity,
            relation,
            to_entity,
            {},
            self.graph_path,
            confidence=confidence,
            source=source,
            authority="observation"
        )
    
    def manage_knowledge(self):
        """Clean and compress knowledge"""
        cleaned = KnowledgeManager.clean_stale_knowledge(self.graph_path)
        compressed = KnowledgeManager.compress_knowledge(self.graph_path)
        return {
            "cleaned_entities": len(cleaned),
            "compression_result": compressed
        }

# Example usage
if __name__ == "__main__":
    memory = OpenClawMemory()
    
    # Remember some facts
    project = memory.remember(
        "Project",
        {"name": "UI自动化测试", "status": "in_progress"},
        confidence=0.9,
        source="user_request"
    )
    
    user = memory.remember(
        "Person",
        {"name": "张三", "role": "用户"},
        confidence=1.0,
        source="user_profile"
    )
    
    # Connect them
    memory.connect(
        project["id"],
        "requested_by",
        user["id"],
        confidence=0.9,
        source="conversation_history"
    )
    
    # Recall what we remember
    projects = memory.recall("Project", {"status": "in_progress"})
    print("进行中的项目:")
    for proj in projects:
        print(f"- {proj['properties']['name']}")
    
    # Manage knowledge
    # result = memory.manage_knowledge()
    # print(f"清理了 {result['cleaned_entities']} 个过期实体")
    # print(f"压缩比: {result['compression_result']['compression_ratio']:.2f}x")
```

## Configuration

### Authority Levels

| Level | Value | Description |
|-------|-------|-------------|
| truth | 1 | Official PRD, API documentation |
| reference | 2 | Meeting minutes, technical plans |
| observation | 3 | AI extracted data, conversation logs |
| manual | 4 | User direct input |

### Decay Parameters

| Parameter | Default | Description |
|-----------|---------|-------------|
| half_life_days | 30 | Knowledge loses half its score after 30 days |
| min_score | 0.1 | Minimum score to stay in active memory |
| review_interval_days | 7 | How often to review and clean knowledge |

### Conflict Resolution

| Parameter | Default | Description |
|-----------|---------|-------------|
| auto_resolve_truth_level | true | Automatically resolve conflicts when truth level is involved |
| send_notifications | true | Send notifications about unresolved conflicts |

## Best Practices

1. **Use appropriate authority levels**: Always use the highest appropriate authority level for each piece of knowledge.

2. **Include sources**: Always specify the source of information for traceability.

3. **Set confidence scores**: Use confidence scores to indicate how reliable the information is.

4. **Regular maintenance**: Schedule regular runs of `clean` and `compress` to keep the knowledge graph healthy.

5. **Define a schema**: Use the schema to enforce data integrity and consistency.

6. **Monitor conflicts**: Review conflict notifications to maintain knowledge quality.

## Troubleshooting

### Common Issues

1. **Permission errors**: Ensure the script has write permissions to the memory directory.

2. **Schema validation failures**: Check that all required properties are provided and follow the schema constraints.

3. **Slow performance**: Large knowledge graphs may need more frequent compression. Try adjusting the decay parameters.

4. **Conflicts not resolving**: Check that authority levels are set correctly and that auto-resolution is enabled.

### Logs and Debugging

- The script writes all operations to `memory/ontology/graph.jsonl`
- Use `validate` command to check for schema violations
- Use `config --show` to verify current configuration

## Future Enhancements

1. **NLP Integration**: Add natural language processing for better entity disambiguation and relation extraction

2. **Vector Database Integration**: Combine with vector storage for enhanced semantic search

3. **Web Interface**: Add a web UI for easier knowledge graph management

4. **Collaboration Features**: Support for multiple users and concurrent edits

5. **Advanced Analytics**: Add knowledge usage analytics and insights

## License

MIT
