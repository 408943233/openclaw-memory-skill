#!/usr/bin/env python3
"""
Enhanced Ontology Skill Usage Demo

This script demonstrates the key features of the enhanced ontology skill:
1. Authority ranking and metadata
2. Conflict detection and resolution
3. Memory decay and compression
4. Temporal reasoning
"""

import sys
import json
from pathlib import Path
from datetime import datetime, timezone, timedelta

# Add the project directory to the path
PROJECT_DIR = Path(__file__).parent.parent
sys.path.append(str(PROJECT_DIR))

from scripts.ontology_optimized import (
    EntityManager,
    RelationManager,
    GraphQuery,
    ConflictManager,
    KnowledgeManager,
    FileManager
)

# Configuration
GRAPH_PATH = str(PROJECT_DIR / "memory/ontology/graph.jsonl")
CONFIG_PATH = str(PROJECT_DIR / "memory/ontology/config.json")

# Clean up any existing test data
def cleanup_test_data():
    """Remove test graph file to start fresh"""
    graph_file = Path(GRAPH_PATH)
    if graph_file.exists():
        graph_file.unlink()
    print("✓ Cleaned up test data")

# Create test entities with different authority levels
def create_test_entities():
    """Create test entities demonstrating authority levels"""
    print("\n=== Creating Test Entities ===")
    
    # Create project with high authority (truth level)
    project = EntityManager.create_entity(
        "Project",
        {"name": "网站重构项目", "status": "in_progress", "budget": "100万"},
        GRAPH_PATH,
        confidence=1.0,
        source="official_prd.md",
        authority="truth"
    )
    print(f"✓ Created Project (truth level): {project['properties']['name']} (ID: {project['id']})")
    
    # Create team members
    alice = EntityManager.create_entity(
        "Person",
        {"name": "Alice", "role": "项目经理", "email": "alice@example.com"},
        GRAPH_PATH,
        confidence=0.9,
        source="hr_system.csv",
        authority="truth"
    )
    print(f"✓ Created Person (truth level): {alice['properties']['name']} (ID: {alice['id']})")
    
    bob = EntityManager.create_entity(
        "Person",
        {"name": "Bob", "role": "前端开发", "email": "bob@example.com"},
        GRAPH_PATH,
        confidence=0.9,
        source="hr_system.csv",
        authority="truth"
    )
    print(f"✓ Created Person (truth level): {bob['properties']['name']} (ID: {bob['id']})")
    
    # Create tasks from meeting minutes (reference level)
    task1 = EntityManager.create_entity(
        "Task",
        {"title": "需求分析", "status": "in_progress", "deadline": "2026-05-01"},
        GRAPH_PATH,
        confidence=0.85,
        source="meeting_minutes_20260413.md",
        authority="reference"
    )
    print(f"✓ Created Task (reference level): {task1['properties']['title']} (ID: {task1['id']})")
    
    task2 = EntityManager.create_entity(
        "Task",
        {"title": "UI设计", "status": "open", "deadline": "2026-05-15"},
        GRAPH_PATH,
        confidence=0.85,
        source="meeting_minutes_20260413.md",
        authority="reference"
    )
    print(f"✓ Created Task (reference level): {task2['properties']['title']} (ID: {task2['id']})")
    
    # Create AI-extracted task (observation level)
    task3 = EntityManager.create_entity(
        "Task",
        {"title": "前端开发", "status": "open", "deadline": "2026-06-15"},
        GRAPH_PATH,
        confidence=0.75,
        source="ai_extracted_20260413.txt",
        authority="observation"
    )
    print(f"✓ Created Task (observation level): {task3['properties']['title']} (ID: {task3['id']})")
    
    # Create relations
    RelationManager.create_relation(
        project["id"],
        "has_owner",
        alice["id"],
        {},
        GRAPH_PATH,
        confidence=1.0,
        source="official_prd.md",
        authority="truth"
    )
    print(f"✓ Created relation: Project has_owner Alice")
    
    RelationManager.create_relation(
        project["id"],
        "has_member",
        bob["id"],
        {},
        GRAPH_PATH,
        confidence=0.9,
        source="hr_system.csv",
        authority="truth"
    )
    print(f"✓ Created relation: Project has_member Bob")
    
    RelationManager.create_relation(
        project["id"],
        "has_task",
        task1["id"],
        {},
        GRAPH_PATH,
        confidence=0.85,
        source="meeting_minutes_20260413.md",
        authority="reference"
    )
    print(f"✓ Created relation: Project has_task 需求分析")
    
    RelationManager.create_relation(
        task1["id"],
        "assigned_to",
        alice["id"],
        {},
        GRAPH_PATH,
        confidence=0.85,
        source="meeting_minutes_20260413.md",
        authority="reference"
    )
    print(f"✓ Created relation: Task assigned_to Alice")
    
    return {
        "project": project,
        "alice": alice,
        "bob": bob,
        "task1": task1,
        "task2": task2,
        "task3": task3
    }

# Demonstrate querying capabilities
def demonstrate_querying(entities):
    """Demonstrate various query capabilities"""
    print("\n=== Querying Demonstration ===")
    
    # Query all projects
    print("\n1. All Projects:")
    projects = GraphQuery.list_entities("Project", GRAPH_PATH)
    for proj in projects:
        print(f"   - {proj['properties']['name']} (status: {proj['properties']['status']})")
        print(f"     Authority: {proj['metadata']['authority_level']}, Confidence: {proj['metadata']['confidence']}")
    
    # Query tasks by status
    print("\n2. Open Tasks:")
    open_tasks = GraphQuery.query_entities("Task", {"status": "open"}, GRAPH_PATH)
    for task in open_tasks:
        print(f"   - {task['properties']['title']} (deadline: {task['properties']['deadline']})")
        print(f"     Source: {task['metadata']['source']}")
    
    # Query related entities
    print("\n3. Project Team Members:")
    members = GraphQuery.get_related(entities['project']['id'], "has_member", GRAPH_PATH)
    for member in members:
        print(f"   - {member['entity']['properties']['name']} ({member['entity']['properties']['role']})")
    
    # Query assigned tasks
    print("\n4. Alice's Assigned Tasks:")
    alice_tasks = GraphQuery.get_related(entities['alice']['id'], "assigned_to", GRAPH_PATH, direction="incoming")
    for task_relation in alice_tasks:
        print(f"   - {task_relation['entity']['properties']['title']}")

# Demonstrate conflict resolution
def demonstrate_conflict_resolution(entities):
    """Demonstrate conflict detection and resolution"""
    print("\n=== Conflict Resolution Demonstration ===")
    
    # Try to create a conflicting project with lower authority
    conflicting_project = {
        "id": EntityManager.generate_id("Project"),
        "type": "Project",
        "properties": {
            "name": "网站重构项目",  # Same name as existing project
            "status": "planning",    # Different status
            "budget": "50万"          # Different budget
        },
        "metadata": {
            "confidence": 0.7,
            "source": "rumor.txt",
            "authority_level": "observation"  # Lower authority
        }
    }
    
    # Load existing entities and detect conflicts
    existing_entities, _ = FileManager.load_graph(GRAPH_PATH)
    conflicts = ConflictManager.detect_conflicts(conflicting_project, existing_entities)
    
    if conflicts:
        print(f"\n1. Detected {len(conflicts)} conflict(s):")
        for conflict in conflicts:
            print(f"   - {conflict}")
    
    # Find the conflicting entity
    existing_proj = None
    for entity in existing_entities.values():
        if (entity["type"] == "Project" and 
            entity["properties"]["name"] == conflicting_project["properties"]["name"]):
            existing_proj = entity
            break
    
    if existing_proj:
        print("\n2. Conflict Resolution Decision:")
        print(f"   Existing: '{existing_proj['properties']['name']}' (Authority: {existing_proj['metadata']['authority_level']}, Confidence: {existing_proj['metadata']['confidence']})")
        print(f"   New: '{conflicting_project['properties']['name']}' (Authority: {conflicting_project['metadata']['authority_level']}, Confidence: {conflicting_project['metadata']['confidence']})")
        
        # Get configuration
        from scripts.ontology_optimized import ConfigManager
        config = ConfigManager.load_config(CONFIG_PATH)
        
        # Resolve conflict
        resolution = ConflictManager.resolve_conflict(conflicting_project, existing_proj, config)
        print(f"   Resolution: {resolution}")
        
        if resolution == "override":
            print("   ✓ New entity would override existing")
        else:
            print("   ✓ Existing entity would be kept")

# Demonstrate memory decay
def demonstrate_decay(entities):
    """Demonstrate memory decay functionality"""
    print("\n=== Memory Decay Demonstration ===")
    
    # Calculate decay scores for entities
    print("\n1. Current Decay Scores:")
    for name, entity in entities.items():
        score = EntityManager.calculate_decay_score(entity)
        print(f"   - {name.capitalize()}: {score:.4f}")
    
    # Show configuration
    from scripts.ontology_optimized import ConfigManager
    config = ConfigManager.load_config(CONFIG_PATH)
    print(f"\n2. Decay Configuration:")
    print(f"   - Half-life: {config['decay']['half_life_days']} days")
    print(f"   - Minimum score: {config['decay']['min_score']}")
    print(f"   - Review interval: {config['decay']['review_interval_days']} days")

# Demonstrate knowledge compression
def demonstrate_compression():
    """Demonstrate knowledge compression functionality"""
    print("\n=== Knowledge Compression Demonstration ===")
    
    # Create some redundant entities to demonstrate compression
    print("\n1. Creating Redundant Entities for Compression Demo:")
    
    # Create similar tasks
    for i in range(3):
        redundant_task = EntityManager.create_entity(
            "Task",
            {"title": "修复登录页面bug", "status": "open"},
            GRAPH_PATH,
            confidence=0.8,
            source=f"issue_tracker_{i}.json",
            authority="observation"
        )
        print(f"   ✓ Created redundant task {i+1}: {redundant_task['properties']['title']} (ID: {redundant_task['id']})")
    
    # Perform compression
    print("\n2. Compressing Knowledge...")
    result = KnowledgeManager.compress_knowledge(GRAPH_PATH)
    print(f"   - Original entities: {result['original_count']}")
    print(f"   - Compressed entities: {result['compressed_count']}")
    print(f"   - Compression ratio: {result['compression_ratio']:.2f}x")

# Demonstrate temporal reasoning
def demonstrate_temporal(entities):
    """Demonstrate temporal reasoning capabilities"""
    print("\n=== Temporal Reasoning Demonstration ===")
    
    # Update an entity to demonstrate versioning
    print("\n1. Updating Task Status:")
    print(f"   Before update: {entities['task1']['properties']['title']} (status: {entities['task1']['properties']['status']})")
    print(f"   Version: {entities['task1']['metadata']['version']}")
    
    updated_task = EntityManager.update_entity(
        entities['task1']['id'],
        {"status": "completed"},
        GRAPH_PATH,
        confidence=0.9,
        source="status_update.md",
        authority="reference"
    )
    
    print(f"   After update: {updated_task['properties']['title']} (status: {updated_task['properties']['status']})")
    print(f"   Version: {updated_task['metadata']['version']}")
    print(f"   Updated at: {updated_task['metadata']['updated']}")
    
    # Show timeline information
    print(f"\n2. Timeline Information:")
    print(f"   - Created: {updated_task['metadata']['created']}")
    print(f"   - Last updated: {updated_task['metadata']['updated']}")
    print(f"   - Last used: {updated_task['metadata']['last_used']}")

# Main demo function
def main():
    """Run the complete demonstration"""
    print("🚀 Enhanced Ontology Skill Demonstration")
    print("=" * 50)
    
    # Clean up any existing test data
    cleanup_test_data()
    
    # Create test entities
    entities = create_test_entities()
    
    # Demonstrate various features
    demonstrate_querying(entities)
    demonstrate_conflict_resolution(entities)
    demonstrate_decay(entities)
    demonstrate_compression()
    demonstrate_temporal(entities)
    
    print("\n" + "=" * 50)
    print("✅ Demonstration completed successfully!")
    print("\nCheck the graph file at:")
    print(f"   {GRAPH_PATH}")
    print("\nTo clean up test data:")
    print("   rm", GRAPH_PATH)

if __name__ == "__main__":
    main()