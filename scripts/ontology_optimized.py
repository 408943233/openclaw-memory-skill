#!/usr/bin/env python3
"""
Optimized Ontology graph operations with enhanced memory management.

Features:
- Authority Ranking (Weight & Permission Levels)
- Temporal Reasoning (Timestamp & Version Control)
- Conflict Resolution
- Memory Decay & Compression
- Entity Disambiguation
- Enhanced Metadata Support

Usage:
    python ontology_optimized.py create --type Person --props '{"name":"Alice"}' --confidence 0.9 --source "manual_input"
    python ontology_optimized.py query --type Task --where '{"status":"open"}'
    python ontology_optimized.py relate --from proj_001 --rel has_task --to task_001 --source "project_plan.md"
    python ontology_optimized.py validate
    python ontology_optimized.py compress  # Compress redundant knowledge
    python ontology_optimized.py clean  # Clean stale knowledge
"""

import argparse
import json
import uuid
import time
import logging
import subprocess
import fcntl
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
from collections import defaultdict

logger = logging.getLogger(__name__)

def _get_commit_hash() -> str:
    """获取当前代码仓库的 commit 版本号"""
    try:
        script_dir = Path(__file__).resolve().parent
        result = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            capture_output=True, text=True, cwd=str(script_dir), timeout=5
        )
        if result.returncode == 0:
            return result.stdout.strip()
    except Exception:
        pass
    return "unknown"

_APP_VERSION = _get_commit_hash()

DEFAULT_GRAPH_PATH = "memory/ontology/graph.jsonl"
DEFAULT_SCHEMA_PATH = "memory/ontology/schema.yaml"
DEFAULT_CONFIG_PATH = "memory/ontology/config.json"

# Resolve config path relative to skill script directory (not cwd)
_SCRIPT_DIR = Path(__file__).parent.parent
_CONFIG_DIR = _SCRIPT_DIR / "memory" / "ontology"
_CONFIG_DIR.mkdir(parents=True, exist_ok=True)

# Authority Levels
AUTHORITY_LEVELS = {
    "truth": 1,    # Source of Truth: Official PRD, API docs
    "reference": 2, # Reference: Meeting minutes, technical plans
    "observation": 3, # Observation: AI extracted data, conversation logs
    "manual": 4     # Manual input: User direct input
}

# Default decay parameters
DEFAULT_DECAY_CONFIG = {
    "half_life_days": 30,  # Knowledge loses half its score after 30 days
    "min_score": 0.1,      # Minimum score to stay in active memory
    "review_interval_days": 7  # How often to review and clean knowledge
}

class ConfigManager:
    """Manages ontology configuration"""
    
    @staticmethod
    def load_config(path: str = None) -> Dict:
        """Load configuration from file. If path is relative, resolve to skill dir."""
        resolved = Path(path) if path else _CONFIG_DIR / "config.json"
        if not resolved.is_absolute():
            resolved = _CONFIG_DIR / resolved.name
        config_path = resolved
        if not config_path.exists():
            return {
                "authority_levels": AUTHORITY_LEVELS,
                "decay": DEFAULT_DECAY_CONFIG,
                "conflict_resolution": {
                    "auto_resolve_truth_level": True,
                    "send_notifications": True
                }
            }
        
        with open(config_path, "r") as f:
            return json.load(f)
    
    @staticmethod
    def save_config(config: Dict, path: str = None) -> None:
        """Save configuration to file."""
        resolved = Path(path) if path else _CONFIG_DIR / "config.json"
        if not resolved.is_absolute():
            resolved = _CONFIG_DIR / resolved.name
        config_path = resolved
        config_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_path, "w") as f:
            json.dump(config, f, indent=2)

class MetadataManager:
    """Manages metadata for entities and relations"""
    
    @staticmethod
    def create_metadata(
        confidence: float = 0.8,
        source: str = "manual",
        authority_level: str = "manual",
        **kwargs
    ) -> Dict:
        """Create standardized metadata"""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        return {
            "confidence": confidence,
            "source": source,
            "authority_level": authority_level,
            "created": timestamp,
            "updated": timestamp,
            "last_used": timestamp,
            "valid_from": timestamp,
            "valid_until": None,
            "version": 1,
            **kwargs
        }

class EntityManager:
    """Manages entity operations with enhanced features"""
    
    @staticmethod
    def generate_id(type_name: str) -> str:
        """Generate a unique ID for an entity."""
        prefix = type_name.lower()[:4]
        suffix = uuid.uuid4().hex[:8]
        return f"{prefix}_{suffix}"
    
    @staticmethod
    def create_entity(
        type_name: str,
        properties: Dict,
        graph_path: str,
        entity_id: Optional[str] = None,
        confidence: float = 0.8,
        source: str = "manual",
        authority_level: str = "manual",
        skip_dedup: bool = False,
        **metadata_kwargs
    ) -> Dict:
        """Create a new entity with dedup via ConflictManager.
        If a duplicate is found, resolve by authority→confidence→recency.
        Returns the created or existing entity dict."""
        entity_id = entity_id or EntityManager.generate_id(type_name)
        timestamp = datetime.now(timezone.utc).isoformat()

        metadata = MetadataManager.create_metadata(
            confidence=confidence,
            source=source,
            authority_level=authority_level,
            **metadata_kwargs
        )

        entity = {
            "id": entity_id,
            "type": type_name,
            "properties": properties,
            "metadata": metadata
        }

        if not skip_dedup:
            existing_entities, _ = FileManager.load_graph(graph_path)
            conflicts = ConflictManager.detect_conflicts(entity, existing_entities)
            if conflicts:
                conflict = conflicts[0]
                existing = conflict["existing_entity"]
                config = ConfigManager.load_config()
                action = ConflictManager.resolve_conflict(entity, existing, config)

                if action == "override":
                    logger.info(f"conflict_override: {conflict['conflict_reason']} → update {existing['id'][:16]}")
                    print(f"    [Skill] 冲突裁决(override): {conflict['conflict_reason']} → 更新 {existing['id']}")
                    return EntityManager.update_entity(
                        entity_id=existing["id"],
                        properties=properties,
                        graph_path=graph_path,
                        confidence=confidence,
                        source=source,
                        authority_level=authority_level
                    ) or existing
                else:
                    logger.info(f"conflict_ignore: {conflict['conflict_reason']} → keep {existing['id'][:16]}")
                    print(f"    [Skill] 冲突裁决(ignore): {conflict['conflict_reason']} → 保留 {existing['id']}")
                    return existing

        record = {"op": "create", "entity": entity, "timestamp": timestamp}
        FileManager.append_op(graph_path, record)

        return entity
    
    @staticmethod
    def update_entity(
        entity_id: str, 
        properties: Dict, 
        graph_path: str,
        confidence: float = 0.8,
        source: str = "manual",
        authority_level: str = "manual"
    ) -> Optional[Dict]:
        """Update entity properties with versioning."""
        entities, _ = FileManager.load_graph(graph_path)
        if entity_id not in entities:
            return None
        
        timestamp = datetime.now(timezone.utc).isoformat()
        
        # Create update record with metadata
        update_record = {
            "op": "update", 
            "id": entity_id, 
            "properties": properties, 
            "timestamp": timestamp,
            "metadata": {
                "confidence": confidence,
                "source": source,
                "authority_level": authority_level
            }
        }
        
        FileManager.append_op(graph_path, update_record)
        
        # Update in-memory entity for immediate use
        entities[entity_id]["properties"].update(properties)
        entities[entity_id]["metadata"]["updated"] = timestamp
        entities[entity_id]["metadata"]["last_used"] = timestamp
        entities[entity_id]["metadata"]["confidence"] = confidence
        entities[entity_id]["metadata"]["version"] += 1
        
        return entities[entity_id]
    
    @staticmethod
    def _parse_iso_timestamp(ts_str: str) -> float:
        """Parse ISO timestamp safely, handling Z suffix and timezone variants."""
        if not ts_str:
            return 0.0
        normalized = ts_str.replace("Z", "+00:00")
        try:
            return datetime.fromisoformat(normalized).timestamp()
        except (ValueError, TypeError):
            return 0.0

    @staticmethod
    def calculate_decay_score(entity: Dict) -> float:
        """Calculate decay score based on last used time and importance."""
        config = ConfigManager.load_config()
        half_life = timedelta(days=config["decay"]["half_life_days"])
        
        last_used_str = entity.get("metadata", {}).get("last_used", "")
        if not last_used_str:
            last_used_str = entity.get("metadata", {}).get("created", "")
        
        try:
            last_used = datetime.fromisoformat(last_used_str)
            if last_used.tzinfo is None:
                last_used = last_used.replace(tzinfo=timezone.utc)
        except (ValueError, TypeError):
            return 1.0
        
        current_time = datetime.now(timezone.utc)
        if current_time.tzinfo is None:
            current_time = current_time.replace(tzinfo=timezone.utc)
        
        time_diff = current_time - last_used
        
        # Calculate decay based on exponential decay formula
        # Score = confidence * (0.5)^(time_diff / half_life)
        decay_factor = 0.5 ** (time_diff.total_seconds() / half_life.total_seconds())
        score = entity["metadata"]["confidence"] * decay_factor
        
        # Adjust based on authority level (higher authority = lower decay)
        authority_factor = 1.0 / AUTHORITY_LEVELS.get(entity["metadata"]["authority_level"], 4)
        score *= (1 + authority_factor)
        
        return score

class RelationManager:
    """Manages relation operations with enhanced features"""
    
    @staticmethod
    def create_relation(
        from_id: str, 
        rel_type: str, 
        to_id: str, 
        properties: Dict, 
        graph_path: str,
        confidence: float = 0.8,
        source: str = "manual",
        authority_level: str = "manual"
    ) -> Dict:
        """Create a relation between entities with enhanced metadata. Idempotent."""
        timestamp = datetime.now(timezone.utc).isoformat()
        
        entities, existing_relations = FileManager.load_graph(graph_path)
        for er in existing_relations:
            if (er.get("from") == from_id and er.get("rel") == rel_type 
                    and er.get("to") == to_id):
                return er
        
        metadata = MetadataManager.create_metadata(
            confidence=confidence,
            source=source,
            authority_level=authority_level
        )
        
        record = {
            "op": "relate",
            "from": from_id,
            "rel": rel_type,
            "to": to_id,
            "properties": properties,
            "metadata": metadata,
            "timestamp": timestamp
        }
        
        FileManager.append_op(graph_path, record)
        return record

class ConflictManager:
    """Manages conflict detection and resolution"""
    
    @staticmethod
    def detect_conflicts(
        new_entity: Dict,
        existing_entities: Dict
    ) -> List[Dict]:
        """Detect conflicts between new entity and existing entities.
        Returns list of {existing_id, existing_entity, conflict_reason}. Empty if no conflict."""
        conflicts = []
        new_type = new_entity.get("type", "?")
        new_id = new_entity.get("id", "")[:16]
        new_props = new_entity.get("properties", {})
        same_type_count = sum(1 for e in existing_entities.values() if e.get("type") == new_type)
        print(f"    [ConflictManager] 检测: type={new_type} id={new_id} | 已有同类型实体: {same_type_count}")

        for existing_id, existing in existing_entities.items():
            if existing["type"] != new_type:
                continue
            if existing_id == new_entity.get("id"):
                continue

            reason = None
            existing_props = existing.get("properties", {})

            if new_props.get("name") and existing_props.get("name") == new_props["name"]:
                reason = f"Name conflict: '{new_props['name']}'"
            elif new_props.get("url") and existing_props.get("url") == new_props["url"]:
                reason = f"URL conflict: '{new_props['url']}'"
            elif new_props.get("api_path") and existing_props.get("api_path") == new_props["api_path"]:
                reason = f"API path conflict: '{new_props['api_path']}'"
            elif new_props.get("domain") and existing_props.get("domain") == new_props.get("domain") \
                    and new_type == "CookieDomain":
                reason = f"CookieDomain conflict: '{new_props['domain']}'"
            elif new_props.get("fingerprint_hash") and existing_props.get("fingerprint_hash") == new_props["fingerprint_hash"]:
                reason = f"Fingerprint hash conflict"
            elif new_type == "System" and new_props.get("name") \
                    and existing_props.get("name") == new_props["name"]:
                reason = f"System name conflict: '{new_props['name']}'"
            elif new_props.get("task_id") and existing_props.get("task_id") == new_props["task_id"] \
                    and new_type in ("TaskRecording", "RecordingMetadata"):
                reason = f"Task id conflict: '{new_props['task_id']}'"
            elif new_props.get("title") and existing_props.get("title") == new_props["title"] \
                    and new_props.get("url") and existing_props.get("url") == new_props["url"]:
                reason = f"Title+URL conflict: '{new_props['title']}'"

            if reason:
                existing_authority = existing.get("metadata", {}).get("authority_level", "?")
                existing_conf = existing.get("metadata", {}).get("confidence", "?")
                logger.warning(f"conflict_detected: {reason} existing={existing_id[:16]} (auth={existing_authority}, conf={existing_conf})")
                print(f"    [ConflictManager] ⚡ 冲突: {reason} | 已有: {existing_id[:16]} (auth={existing_authority}, conf={existing_conf})")
                conflicts.append({
                    "existing_id": existing_id,
                    "existing_entity": existing,
                    "conflict_reason": reason
                })

        if not conflicts and same_type_count == 0:
            print(f"    [ConflictManager] ✅ 无同类型实体，无需去重")
        elif not conflicts:
            print(f"    [ConflictManager] ✅ 同类型实体 {same_type_count} 个但无冲突（name/url 等均不同）")

        return conflicts
    
    @staticmethod
    def resolve_conflict(
        new_entity: Dict,
        existing_entity: Dict,
        config: Dict
    ) -> str:
        """Resolve conflict between new and existing entity."""
        new_level = AUTHORITY_LEVELS.get(new_entity["metadata"]["authority_level"], 4)
        existing_level = AUTHORITY_LEVELS.get(existing_entity["metadata"]["authority_level"], 4)
        new_conf = new_entity["metadata"]["confidence"]
        existing_conf = existing_entity["metadata"]["confidence"]

        print(f"    [ConflictManager] 裁决: new(auth={new_level}, conf={new_conf}) vs existing(auth={existing_level}, conf={existing_conf})")

        if new_level < existing_level:
            print(f"    [ConflictManager] → override (new authority {new_level} > existing {existing_level})")
            return "override"
        elif new_level > existing_level:
            print(f"    [ConflictManager] → ignore (existing authority {existing_level} > new {new_level})")
            return "ignore"

        if new_conf > existing_conf:
            print(f"    [ConflictManager] → override (new confidence {new_conf} > existing {existing_conf})")
            return "override"

        new_time = datetime.fromisoformat(new_entity["metadata"]["created"])
        existing_time = datetime.fromisoformat(existing_entity["metadata"]["created"])

        if new_time > existing_time:
            print(f"    [ConflictManager] → override (new time {new_time.isoformat()[:19]} newer)")
            return "override"

        print(f"    [ConflictManager] → ignore (existing retained by default)")
        return "ignore"

class KnowledgeCompressor:
    """Handles knowledge compression and redundancy removal"""
    
    @staticmethod
    def compress_entities(
        entities: Dict, 
        graph_path: str
    ) -> Dict:
        """Compress redundant entities by type."""
        compressed_entities = {}
        entity_groups = defaultdict(list)
        
        # Group entities by type
        for entity_id, entity in entities.items():
            entity_groups[entity["type"]].append((entity_id, entity))
        
        # Process each type group
        compressible_types = ["Task", "Event", "Note", "JSError", "TaskRecording", "APIResponse",
                              "RecordingMetadata", "OperationSequence", "PageLoadEvent"]
        for entity_type, group in entity_groups.items():
            if entity_type in compressible_types:
                compressed_entities.update(KnowledgeCompressor._compress_similar_entities(group, graph_path))
            else:
                # Keep other types as is
                for entity_id, entity in group:
                    compressed_entities[entity_id] = entity
        
        return compressed_entities
    
    @staticmethod
    def _compress_similar_entities(
        entities: List[Tuple[str, Dict]], 
        graph_path: str
    ) -> Dict:
        """Compress highly similar entities into a single entity."""
        compressed = {}
        processed = set()
        
        # Simple similarity check based on content hash (can be enhanced with NLP)
        for i, (id1, entity1) in enumerate(entities):
            if id1 in processed:
                continue
            
            similar_entities = [entity1]
            processed.add(id1)
            
            for j, (id2, entity2) in enumerate(entities[i+1:], i+1):
                if id2 in processed:
                    continue
                
                # Check similarity based on content
                if KnowledgeCompressor._is_similar(entity1, entity2):
                    similar_entities.append(entity2)
                    processed.add(id2)
            
            if len(similar_entities) == 1:
                # Keep single entity
                compressed[id1] = entity1
            else:
                # Create compressed entity
                compressed_entity = KnowledgeCompressor._merge_entities(similar_entities)
                # Mark original entities as merged
                for entity in similar_entities:
                    FileManager.append_op(graph_path, {
                        "op": "merge",
                        "id": entity["id"],
                        "merged_into": compressed_entity["id"],
                        "timestamp": datetime.now(timezone.utc).isoformat()
                    })
                # Add compressed entity
                FileManager.append_op(graph_path, {
                    "op": "create",
                    "entity": compressed_entity,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                compressed[compressed_entity["id"]] = compressed_entity
        
        return compressed
    
    @staticmethod
    def _is_similar(entity1: Dict, entity2: Dict, threshold: float = 0.8) -> bool:
        """Check if two entities are similar."""
        # Simple check: same type and same name/content
        if entity1["type"] != entity2["type"]:
            return False
        
        # Compare name if exists
        if "name" in entity1["properties"] and "name" in entity2["properties"]:
            if entity1["properties"]["name"] != entity2["properties"]["name"]:
                return False
        
        # For Task type, compare title
        if entity1["type"] == "Task":
            if ("title" in entity1["properties"] and "title" in entity2["properties"]):
                return entity1["properties"]["title"] == entity2["properties"]["title"]
        
        return False
    
    @staticmethod
    def _merge_entities(entities: List[Dict]) -> Dict:
        """Merge multiple similar entities into one."""
        if not entities:
            return {}
        
        # Use the entity with highest authority/confidence as base
        base_entity = max(entities, key=lambda e: (
            1.0 / AUTHORITY_LEVELS.get(e["metadata"]["authority_level"], 4),
            e["metadata"]["confidence"]
        ))
        
        merged = {
            "id": EntityManager.generate_id(base_entity["type"]),
            "type": base_entity["type"],
            "properties": base_entity["properties"].copy(),
            "metadata": base_entity["metadata"].copy()
        }
        
        # Update metadata to reflect merged status
        merged["metadata"]["merged_from"] = [e["id"] for e in entities]
        merged["metadata"]["merged_count"] = len(entities)
        merged["metadata"]["created"] = datetime.now(timezone.utc).isoformat()
        merged["metadata"]["updated"] = merged["metadata"]["created"]
        
        return merged

class FileManager:
    """Manages file operations for the ontology"""
    
    @staticmethod
    def resolve_safe_path(
        user_path: str,
        *, 
        root: Optional[Path] = None,
        must_exist: bool = False,
        label: str = "path",
    ) -> Path:
        """Resolve user path within root and reject traversal outside it."""
        if not user_path or not user_path.strip():
            raise SystemExit(f"Invalid {label}: empty path")

        safe_root = (root or Path.cwd()).resolve()
        candidate = Path(user_path).expanduser()
        if not candidate.is_absolute():
            candidate = safe_root / candidate

        try:
            resolved = candidate.resolve(strict=False)
        except OSError as exc:
            raise SystemExit(f"Invalid {label}: {exc}") from exc

        try:
            resolved.relative_to(safe_root)
        except ValueError:
            raise SystemExit(
                f"Invalid {label}: must stay within workspace root '{safe_root}'"
            )

        if must_exist and not resolved.exists():
            raise SystemExit(f"Invalid {label}: file not found '{resolved}'")

        return resolved
    
    @staticmethod
    def load_graph(path: str) -> Tuple[Dict, List]:
        """Load entities and relations from graph file with metadata support."""
        entities = {}
        relations = []
        
        graph_path = Path(path)
        if not graph_path.exists():
            return entities, relations
        
        with open(graph_path) as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_SH)
            try:
                for line in f:
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        record = json.loads(line)
                    except json.JSONDecodeError:
                        logger.warning(f"load_graph: skipping malformed JSON line")
                        continue
                    op = record.get("op")
                    
                    if op == "create":
                        entity = record["entity"]
                        entities[entity["id"]] = entity
                    elif op == "update":
                        entity_id = record["id"]
                        if entity_id in entities:
                            entities[entity_id]["properties"].update(record.get("properties", {}))
                            entities[entity_id]["metadata"]["updated"] = record.get("timestamp")
                            entities[entity_id]["metadata"]["version"] += 1
                            if "metadata" in record:
                                entities[entity_id]["metadata"].update(record["metadata"])
                    elif op == "delete":
                        entity_id = record["id"]
                        entities.pop(entity_id, None)
                    elif op == "relate":
                        relations.append({
                            "from": record["from"],
                            "rel": record["rel"],
                            "to": record["to"],
                            "properties": record.get("properties", {}),
                            "metadata": record.get("metadata", {})
                        })
                    elif op == "unrelate":
                        relations = [r for r in relations 
                                   if not (r["from"] == record["from"] 
                                          and r["rel"] == record["rel"] 
                                          and r["to"] == record["to"])]
                    elif op == "mark_stale":
                        entity_id = record["id"]
                        if entity_id in entities:
                            entities[entity_id]["metadata"]["stale"] = True
                            entities[entity_id]["metadata"]["stale_score"] = record.get("score", 0)
                            entities[entity_id]["metadata"]["stale_timestamp"] = record.get("timestamp")
                    elif op == "merge":
                        entity_id = record["id"]
                        merged_into = record.get("merged_into", "")
                        if entity_id in entities and merged_into:
                            entities[entity_id]["metadata"]["merged_into"] = merged_into
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)
        
        return entities, relations
    
    @staticmethod
    def append_op(path: str, record: Dict) -> None:
        """Append an operation to the graph file with file lock for concurrency safety."""
        graph_path = Path(path)
        graph_path.parent.mkdir(parents=True, exist_ok=True)
        
        op_type = record.get("op", "?")
        entity_id = record.get("id", record.get("entity", {}).get("id", "?"))[:16]
        logger.debug(f"append_op: {op_type} id={entity_id} path={graph_path.name}")
        
        with open(graph_path, "a") as f:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
            try:
                f.write(json.dumps(record) + "\n")
                f.flush()
            finally:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)

class GraphQuery:
    """Handles advanced graph queries"""
    
    @staticmethod
    def get_entity(entity_id: str, graph_path: str) -> Optional[Dict]:
        """Get entity by ID."""
        entities, _ = FileManager.load_graph(graph_path)
        return entities.get(entity_id)
    
    @staticmethod
    def query_entities(
        type_name: Optional[str], 
        where: Dict, 
        graph_path: str,
        include_stale: bool = False
    ) -> List[Dict]:
        """Query entities by type and properties with unified stale filtering.
        An entity is considered stale if EITHER:
          - It has been marked via op:mark_stale (metadata.stale == True)
          - Its decay_score is below config threshold
        """
        entities, _ = FileManager.load_graph(graph_path)
        results = []
        config = ConfigManager.load_config()
        
        for entity in entities.values():
            if type_name and entity["type"] != type_name:
                continue
            
            match = True
            for key, value in where.items():
                if entity["properties"].get(key) != value:
                    match = False
                    break
            
            if not match:
                continue
            
            if not include_stale:
                meta = entity.get("metadata", {})
                if meta.get("stale") is True:
                    continue
                score = EntityManager.calculate_decay_score(entity)
                if score < config["decay"]["min_score"]:
                    continue
            
            results.append(entity)
        
        results.sort(key=lambda e: (
            -e["metadata"]["confidence"],
            -EntityManager._parse_iso_timestamp(e["metadata"].get("created", ""))
        ))
        
        return results
    
    @staticmethod
    def list_entities(
        type_name: Optional[str], 
        graph_path: str,
        include_stale: bool = False
    ) -> List[Dict]:
        """List all entities of a type with decay filtering."""
        return GraphQuery.query_entities(type_name, {}, graph_path, include_stale)
    
    @staticmethod
    def get_related(
        entity_id: str, 
        rel_type: Optional[str], 
        graph_path: str, 
        direction: str = "outgoing"
    ) -> List[Dict]:
        """Get related entities."""
        entities, relations = FileManager.load_graph(graph_path)
        results = []
        
        for rel in relations:
            if direction == "outgoing" and rel["from"] == entity_id:
                if not rel_type or rel["rel"] == rel_type:
                    if rel["to"] in entities:
                        results.append({
                            "relation": rel["rel"],
                            "metadata": rel.get("metadata", {}),
                            "entity": entities[rel["to"]]
                        })
            elif direction == "incoming" and rel["to"] == entity_id:
                if not rel_type or rel["rel"] == rel_type:
                    if rel["from"] in entities:
                        results.append({
                            "relation": rel["rel"],
                            "metadata": rel.get("metadata", {}),
                            "entity": entities[rel["from"]]
                        })
            elif direction == "both":
                if rel["from"] == entity_id or rel["to"] == entity_id:
                    if not rel_type or rel["rel"] == rel_type:
                        other_id = rel["to"] if rel["from"] == entity_id else rel["from"]
                        if other_id in entities:
                            results.append({
                                "relation": rel["rel"],
                                "direction": "outgoing" if rel["from"] == entity_id else "incoming",
                                "metadata": rel.get("metadata", {}),
                                "entity": entities[other_id]
                            })
        
        return results

class GraphValidator:
    """Validates graph against schema constraints"""
    
    @staticmethod
    def validate_graph(graph_path: str, schema_path: str) -> List[str]:
        """Validate graph against schema constraints."""
        entities, relations = FileManager.load_graph(graph_path)
        errors = []
        
        # Load schema if exists
        schema = GraphValidator.load_schema(schema_path)
        
        type_schemas = schema.get("types", {})
        relation_schemas = schema.get("relations", {})
        global_constraints = schema.get("constraints", [])
        
        for entity_id, entity in entities.items():
            type_name = entity["type"]
            type_schema = type_schemas.get(type_name, {})
            
            # Check required properties
            required = type_schema.get("required", [])
            for prop in required:
                if prop not in entity["properties"]:
                    errors.append(f"{entity_id}: missing required property '{prop}'")
            
            # Check forbidden properties
            forbidden = type_schema.get("forbidden_properties", [])
            for prop in forbidden:
                if prop in entity["properties"]:
                    errors.append(f"{entity_id}: contains forbidden property '{prop}'")
            
            # Check enum values
            for prop, allowed in type_schema.items():
                if prop.endswith("_enum"):
                    field = prop.replace("_enum", "")
                    value = entity["properties"].get(field)
                    if value and value not in allowed:
                        errors.append(f"{entity_id}: '{field}' must be one of {allowed}, got '{value}'")
        
        # Relation constraints (type + cardinality + acyclicity)
        rel_index = {}
        for rel in relations:
            rel_index.setdefault(rel["rel"], []).append(rel)
        
        for rel_type, rel_schema in relation_schemas.items():
            rels = rel_index.get(rel_type, [])
            from_types = rel_schema.get("from_types", [])
            to_types = rel_schema.get("to_types", [])
            cardinality = rel_schema.get("cardinality")
            acyclic = rel_schema.get("acyclic", False)
            
            # Type checks
            for rel in rels:
                from_entity = entities.get(rel["from"])
                to_entity = entities.get(rel["to"])
                if not from_entity or not to_entity:
                    errors.append(f"{rel_type}: relation references missing entity ({rel['from']} -> {rel['to']})")
                    continue
                if from_types and from_entity["type"] not in from_types:
                    errors.append(
                        f"{rel_type}: from entity {rel['from']} type {from_entity['type']} not in {from_types}"
                    )
                if to_types and to_entity["type"] not in to_types:
                    errors.append(
                        f"{rel_type}: to entity {rel['to']} type {to_entity['type']} not in {to_types}"
                    )

            if cardinality:
                if cardinality == "one_to_one":
                    from_entities = set(r["from"] for r in rels)
                    to_entities = set(r["to"] for r in rels)
                    if len(from_entities) != len(rels):
                        errors.append(f"{rel_type}: one_to_one violation — duplicate from entity")
                    if len(to_entities) != len(rels):
                        errors.append(f"{rel_type}: one_to_one violation — duplicate to entity")
                elif cardinality == "one_to_many":
                    to_entities = set(r["to"] for r in rels)
                    if len(to_entities) != len(rels):
                        errors.append(f"{rel_type}: one_to_many violation — duplicate to entity")

            if acyclic:
                graph = defaultdict(set)
                for rel in rels:
                    graph[rel["from"]].add(rel["to"])
                visited = set()
                rec_stack = set()

                def _has_cycle(node):
                    if node in rec_stack:
                        return True
                    if node in visited:
                        return False
                    visited.add(node)
                    rec_stack.add(node)
                    for neighbor in graph.get(node, set()):
                        if _has_cycle(neighbor):
                            return True
                    rec_stack.discard(node)
                    return False

                for node in list(graph.keys()):
                    if _has_cycle(node):
                        errors.append(f"{rel_type}: acyclic violation — cycle detected starting from {node}")
                        break
        
        return errors
    
    @staticmethod
    def load_schema(schema_path: str) -> Dict:
        """Load schema from YAML if it exists."""
        schema = {}
        schema_file = Path(schema_path)
        if schema_file.exists():
            import yaml
            with open(schema_file) as f:
                schema = yaml.safe_load(f) or {}
        return schema
    
    @staticmethod
    def write_schema(schema_path: str, schema: Dict) -> None:
        """Write schema to YAML."""
        schema_file = Path(schema_path)
        schema_file.parent.mkdir(parents=True, exist_ok=True)
        import yaml
        with open(schema_file, "w") as f:
            yaml.safe_dump(schema, f, sort_keys=False)

class KnowledgeManager:
    """Main knowledge management class"""
    
    @staticmethod
    def clean_stale_knowledge(graph_path: str) -> List[str]:
        """Clean stale knowledge based on decay score."""
        entities, relations = FileManager.load_graph(graph_path)
        config = ConfigManager.load_config()
        cleaned_entities = []
        
        for entity_id, entity in entities.items():
            score = EntityManager.calculate_decay_score(entity)
            if score < config["decay"]["min_score"]:
                # Mark as stale instead of deleting
                FileManager.append_op(graph_path, {
                    "op": "mark_stale",
                    "id": entity_id,
                    "score": score,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                })
                cleaned_entities.append(entity_id)
        
        return cleaned_entities
    
    @staticmethod
    def compress_knowledge(graph_path: str) -> Dict:
        """Compress redundant knowledge."""
        entities, relations = FileManager.load_graph(graph_path)
        compressed_entities = KnowledgeCompressor.compress_entities(entities, graph_path)
        
        # Write compressed graph (this would normally be more efficient)
        # For simplicity, we're just appending the compression operations
        
        return {
            "original_count": len(entities),
            "compressed_count": len(compressed_entities),
            "compression_ratio": len(compressed_entities) / len(entities) if entities else 1.0
        }

class MigrationManager:
    """Handles migration from old ontology format"""
    
    @staticmethod
    def load_old_graph(path: str) -> Tuple[Dict, List]:
        """Load old format graph data"""
        entities = {}
        relations = []
        
        graph_path = Path(path)
        if not graph_path.exists():
            raise SystemExit(f"❌ Old graph file not found: {path}")
        
        with open(graph_path) as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                record = json.loads(line)
                op = record.get("op")
                
                if op == "create":
                    entity = record["entity"]
                    entities[entity["id"]] = entity
                elif op == "update":
                    entity_id = record["id"]
                    if entity_id in entities:
                        entities[entity_id]["properties"].update(record.get("properties", {}))
                elif op == "delete":
                    entity_id = record["id"]
                    entities.pop(entity_id, None)
                elif op == "relate":
                    relations.append({
                        "from": record["from"],
                        "rel": record["rel"],
                        "to": record["to"],
                        "properties": record.get("properties", {})
                    })
        
        return entities, relations
    
    @staticmethod
    def migrate(old_graph_path: str, new_graph_path: str) -> Dict:
        """Migrate data from old format to new format"""
        print(f"🚀 Starting migration from {old_graph_path} to {new_graph_path}")
        
        # Load old graph data
        old_entities, old_relations = MigrationManager.load_old_graph(old_graph_path)
        print(f"📊 Found {len(old_entities)} entities and {len(old_relations)} relations")
        
        # Clear new graph if it exists
        new_graph = Path(new_graph_path)
        if new_graph.exists():
            print(f"⚠️  Removing existing new graph file: {new_graph_path}")
            new_graph.unlink()
        
        # Ensure directory exists
        new_graph.parent.mkdir(parents=True, exist_ok=True)
        
        # Migrate entities
        print("\n📦 Migrating entities...")
        migrated_entities = 0
        
        for entity_id, entity in old_entities.items():
            # Check if entity already has enhanced format
            if "metadata" in entity:
                # Already enhanced, just copy
                record = {
                    "op": "create", 
                    "entity": entity, 
                    "timestamp": entity["metadata"]["created"]
                }
                FileManager.append_op(new_graph_path, record)
            else:
                # Create enhanced entity with default metadata
                enhanced_entity = {
                    "id": entity["id"],
                    "type": entity["type"],
                    "properties": entity["properties"],
                    "metadata": MetadataManager.create_metadata(
                        confidence=0.8,
                        source="legacy_migration",
                        authority_level="manual",
                        migrated_from="original_ontology"
                    )
                }
                record = {
                    "op": "create", 
                    "entity": enhanced_entity, 
                    "timestamp": enhanced_entity["metadata"]["created"]
                }
                FileManager.append_op(new_graph_path, record)
            migrated_entities += 1
        
        print(f"✅ Migrated {migrated_entities} entities to enhanced format")
        
        # Migrate relations
        print("\n🔗 Migrating relations...")
        migrated_relations = 0
        
        for relation in old_relations:
            # Check if relation already has enhanced format
            if "metadata" in relation:
                # Already enhanced, just copy
                record = {
                    "op": "relate",
                    "from": relation["from"],
                    "rel": relation["rel"],
                    "to": relation["to"],
                    "properties": relation["properties"],
                    "metadata": relation["metadata"],
                    "timestamp": relation["metadata"]["created"]
                }
                FileManager.append_op(new_graph_path, record)
            else:
                # Create enhanced relation with default metadata
                metadata = MetadataManager.create_metadata(
                    confidence=0.8,
                    source="legacy_migration",
                    authority_level="manual"
                )
                record = {
                    "op": "relate",
                    "from": relation["from"],
                    "rel": relation["rel"],
                    "to": relation["to"],
                    "properties": relation.get("properties", {}),
                    "metadata": metadata,
                    "timestamp": metadata["created"]
                }
                FileManager.append_op(new_graph_path, record)
            migrated_relations += 1
        
        print(f"✅ Migrated {migrated_relations} relations to enhanced format")
        
        # Validate migration
        print("\n✅ Validation: Loading migrated data...")
        new_entities, new_relations = FileManager.load_graph(new_graph_path)
        print(f"✅ Loaded {len(new_entities)} entities and {len(new_relations)} relations from new graph")
        
        # Verify all entities were migrated
        entity_success = len(new_entities) == len(old_entities)
        relation_success = len(new_relations) == len(old_relations)
        
        if entity_success:
            print("✅ All entities successfully migrated!")
        else:
            print(f"⚠️  Entity count mismatch: {len(old_entities)} -> {len(new_entities)}")
        
        if relation_success:
            print("✅ All relations successfully migrated!")
        else:
            print(f"⚠️  Relation count mismatch: {len(old_relations)} -> {len(new_relations)}")
        
        print("\n🎉 Migration completed successfully!")
        print(f"📁 Original data: {old_graph_path}")
        print(f"📁 Migrated data: {new_graph_path}")
        print("\n🔧 Next steps:")
        print("   1. Validate the migrated data: python scripts/ontology_optimized.py validate")
        print("   2. Test queries: python scripts/ontology_optimized.py list --type Person")
        print("   3. Review metadata: python scripts/ontology_optimized.py get --id <entity_id>")
        
        return {
            "success": entity_success and relation_success,
            "entities_migrated": migrated_entities,
            "relations_migrated": migrated_relations,
            "entity_count": len(new_entities),
            "relation_count": len(new_relations)
        }

def main():
    """Main entry point"""
    logger.info(f"openclaw-memory-skill v{_APP_VERSION} starting")
    parser = argparse.ArgumentParser(description="Optimized Ontology graph operations")
    subparsers = parser.add_subparsers(dest="command", required=True)
    
    # Create entity
    create_p = subparsers.add_parser("create", help="Create entity")
    create_p.add_argument("--type", "-t", required=True, help="Entity type")
    create_p.add_argument("--props", "-p", default="{}", help="Properties JSON")
    create_p.add_argument("--id", help="Entity ID (auto-generated if not provided)")
    create_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    create_p.add_argument("--confidence", "-c", type=float, default=0.8, help="Confidence score (0-1)")
    create_p.add_argument("--source", "-s", default="manual", help="Source of information")
    create_p.add_argument("--authority", "-a", default="manual", choices=AUTHORITY_LEVELS.keys(), help="Authority level")
    
    # Get entity
    get_p = subparsers.add_parser("get", help="Get entity by ID")
    get_p.add_argument("--id", required=True, help="Entity ID")
    get_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Query entities
    query_p = subparsers.add_parser("query", help="Query entities")
    query_p.add_argument("--type", "-t", help="Entity type")
    query_p.add_argument("--where", "-w", default="{}", help="Filter JSON")
    query_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    query_p.add_argument("--include-stale", action="store_true", help="Include stale entities")
    
    # List entities
    list_p = subparsers.add_parser("list", help="List entities")
    list_p.add_argument("--type", "-t", help="Entity type")
    list_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    list_p.add_argument("--include-stale", action="store_true", help="Include stale entities")
    
    # Update entity
    update_p = subparsers.add_parser("update", help="Update entity")
    update_p.add_argument("--id", required=True, help="Entity ID")
    update_p.add_argument("--props", "-p", required=True, help="Properties JSON")
    update_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    update_p.add_argument("--confidence", "-c", type=float, default=0.8, help="Confidence score (0-1)")
    update_p.add_argument("--source", "-s", default="manual", help="Source of information")
    update_p.add_argument("--authority", "-a", default="manual", choices=AUTHORITY_LEVELS.keys(), help="Authority level")
    
    # Delete entity
    delete_p = subparsers.add_parser("delete", help="Delete entity")
    delete_p.add_argument("--id", required=True, help="Entity ID")
    delete_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Relate entities
    relate_p = subparsers.add_parser("relate", help="Create relation")
    relate_p.add_argument("--from", dest="from_id", required=True, help="From entity ID")
    relate_p.add_argument("--rel", "-r", required=True, help="Relation type")
    relate_p.add_argument("--to", dest="to_id", required=True, help="To entity ID")
    relate_p.add_argument("--props", "-p", default="{}", help="Relation properties JSON")
    relate_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    relate_p.add_argument("--confidence", "-c", type=float, default=0.8, help="Confidence score (0-1)")
    relate_p.add_argument("--source", "-s", default="manual", help="Source of information")
    relate_p.add_argument("--authority", "-a", default="manual", choices=AUTHORITY_LEVELS.keys(), help="Authority level")
    
    # Related entities
    related_p = subparsers.add_parser("related", help="Get related entities")
    related_p.add_argument("--id", required=True, help="Entity ID")
    related_p.add_argument("--rel", "-r", help="Relation type filter")
    related_p.add_argument("--dir", "-d", choices=["outgoing", "incoming", "both"], default="outgoing")
    related_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Unrelate entities
    unrelate_p = subparsers.add_parser("unrelate", help="Remove relation")
    unrelate_p.add_argument("--from", dest="from_id", required=True, help="From entity ID")
    unrelate_p.add_argument("--rel", "-r", required=True, help="Relation type")
    unrelate_p.add_argument("--to", dest="to_id", required=True, help="To entity ID")
    unrelate_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Validate graph
    validate_p = subparsers.add_parser("validate", help="Validate graph")
    validate_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    validate_p.add_argument("--schema", "-s", default=DEFAULT_SCHEMA_PATH)
    
    # Clean stale knowledge
    clean_p = subparsers.add_parser("clean", help="Clean stale knowledge")
    clean_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Compress knowledge
    compress_p = subparsers.add_parser("compress", help="Compress redundant knowledge")
    compress_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    
    # Configuration
    config_p = subparsers.add_parser("config", help="Manage configuration")
    config_p.add_argument("--show", action="store_true", help="Show current configuration")
    config_p.add_argument("--set", nargs=2, help="Set configuration key value")
    
    # Migration
    migrate_p = subparsers.add_parser("migrate", help="Migrate data from old ontology format")
    migrate_p.add_argument("--from", dest="old_path", required=True, help="Path to old graph.jsonl")
    migrate_p.add_argument("--to", dest="new_path", default=DEFAULT_GRAPH_PATH, help="Path to new graph.jsonl")
    
    # Stats
    stats_p = subparsers.add_parser("stats", help="Show graph statistics")
    stats_p.add_argument("--graph", "-g", default=DEFAULT_GRAPH_PATH)
    stats_p.add_argument("--include-stale", action="store_true", help="Include stale entities")
    
    args = parser.parse_args()
    workspace_root = Path.cwd().resolve()

    if hasattr(args, "graph"):
        args.graph = str(
            FileManager.resolve_safe_path(args.graph, root=workspace_root, label="graph path")
        )
    if hasattr(args, "schema"):
        args.schema = str(
            FileManager.resolve_safe_path(args.schema, root=workspace_root, label="schema path")
        )
    
    # Execute commands
    if args.command == "create":
        props = json.loads(args.props)
        entity = EntityManager.create_entity(
            args.type, props, args.graph, args.id,
            confidence=args.confidence,
            source=args.source,
            authority_level=args.authority
        )
        print(json.dumps(entity, indent=2, ensure_ascii=False))
    
    elif args.command == "get":
        entity = GraphQuery.get_entity(args.id, args.graph)
        if entity:
            print(json.dumps(entity, indent=2, ensure_ascii=False))
        else:
            print(f"Entity not found: {args.id}")
    
    elif args.command == "query":
        where = json.loads(args.where)
        results = GraphQuery.query_entities(
            args.type, where, args.graph, args.include_stale
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == "list":
        results = GraphQuery.list_entities(
            args.type, args.graph, args.include_stale
        )
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == "update":
        props = json.loads(args.props)
        entity = EntityManager.update_entity(
            args.id, props, args.graph,
            confidence=args.confidence,
            source=args.source,
            authority_level=args.authority
        )
        if entity:
            print(json.dumps(entity, indent=2, ensure_ascii=False))
        else:
            print(f"Entity not found: {args.id}")
    
    elif args.command == "delete":
        entities, _ = FileManager.load_graph(args.graph)
        if args.id in entities:
            FileManager.append_op(args.graph, {
                "op": "delete",
                "id": args.id,
                "timestamp": datetime.now(timezone.utc).isoformat()
            })
            print(f"Deleted: {args.id}")
        else:
            print(f"Entity not found: {args.id}")
    
    elif args.command == "relate":
        props = json.loads(args.props)
        rel = RelationManager.create_relation(
            args.from_id, args.rel, args.to_id, props, args.graph,
            confidence=args.confidence,
            source=args.source,
            authority_level=args.authority
        )
        print(json.dumps(rel, indent=2, ensure_ascii=False))
    
    elif args.command == "related":
        results = GraphQuery.get_related(args.id, args.rel, args.graph, args.dir)
        print(json.dumps(results, indent=2, ensure_ascii=False))
    
    elif args.command == "unrelate":
        FileManager.append_op(args.graph, {
            "op": "unrelate",
            "from": args.from_id,
            "rel": args.rel,
            "to": args.to_id,
            "timestamp": datetime.now(timezone.utc).isoformat()
        })
        print(json.dumps({"status": "unrelated", "from": args.from_id, "rel": args.rel, "to": args.to_id}, ensure_ascii=False))
    
    elif args.command == "validate":
        errors = GraphValidator.validate_graph(args.graph, args.schema)
        if errors:
            print("Validation errors:")
            for err in errors:
                print(f"  - {err}")
        else:
            print("Graph is valid.")
    
    elif args.command == "clean":
        cleaned = KnowledgeManager.clean_stale_knowledge(args.graph)
        if cleaned:
            print(f"Marked {len(cleaned)} entities as stale:")
            for entity_id in cleaned:
                print(f"  - {entity_id}")
        else:
            print("No stale entities found.")
    
    elif args.command == "compress":
        result = KnowledgeManager.compress_knowledge(args.graph)
        print(f"Compression result:")
        print(f"  Original entities: {result['original_count']}")
        print(f"  Compressed entities: {result['compressed_count']}")
        print(f"  Compression ratio: {result['compression_ratio']:.2f}x")
    
    elif args.command == "config":
        config = ConfigManager.load_config()
        if args.show:
            print(json.dumps(config, indent=2))
        elif args.set:
            key, value = args.set
            # Simple key path parsing (e.g., decay.half_life_days)
            keys = key.split(".")
            current = config
            for k in keys[:-1]:
                if k not in current:
                    current[k] = {}
                current = current[k]
            current[keys[-1]] = json.loads(value)
            ConfigManager.save_config(config)
            print(f"Updated config: {key} = {value}")
    
    elif args.command == "migrate":
        # Resolve safe paths
        args.old_path = str(
            FileManager.resolve_safe_path(args.old_path, root=workspace_root, label="old graph path")
        )
        args.new_path = str(
            FileManager.resolve_safe_path(args.new_path, root=workspace_root, label="new graph path")
        )
        
        MigrationManager.migrate(args.old_path, args.new_path)
    
    elif args.command == "stats":
        entities, relations = FileManager.load_graph(args.graph)
        type_counts = {}
        total_relations = len(relations)
        stale_count = 0
        
        for e in entities.values():
            t = e["type"]
            type_counts[t] = type_counts.get(t, 0) + 1
            meta = e.get("metadata", {})
            if meta.get("stale") is True:
                stale_count += 1
            elif EntityManager.calculate_decay_score(e) < ConfigManager.load_config()["decay"]["min_score"]:
                stale_count += 1
        
        rel_types = {}
        for r in relations:
            rt = r["rel"]
            rel_types[rt] = rel_types.get(rt, 0) + 1
        
        output = {
            "total_entities": len(entities),
            "total_relations": total_relations,
            "stale_count": stale_count if not args.include_stale else "n/a",
            "entity_types": dict(sorted(type_counts.items(), key=lambda x: -x[1])),
            "relation_types": dict(sorted(rel_types.items(), key=lambda x: -x[1]))
        }
        print(json.dumps(output, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    main()