#!/usr/bin/env python3
"""
Query Runner for RAG Pipeline Debugging

Executes SQL queries against the Chroma database and provides formatted output
for debugging chunking, metadata, retrieval, and ranking issues.
"""

import os
import sqlite3
import json
from typing import Dict, List, Any, Optional
from datetime import datetime

class QueryRunner:
    """Executes debug queries against the Chroma database."""
    
    def __init__(self, db_path: str):
        self.db_path = db_path
        self.conn = None
    
    def connect(self):
        """Connect to the Chroma SQLite database."""
        try:
            self.conn = sqlite3.connect(self.db_path)
            self.conn.row_factory = sqlite3.Row
            return True
        except Exception as e:
            print(f"Error connecting to database: {e}")
            return False
    
    def disconnect(self):
        """Close database connection."""
        if self.conn:
            self.conn.close()
    
    def run_query(self, query: str, description: str = "") -> List[Dict[str, Any]]:
        """Run a single query and return results."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error running query '{description}': {e}")
            return []
    
    def run_quick_analysis(self) -> Dict[str, Any]:
        """Run a quick analysis of the database."""
        if not self.connect():
            return {"error": "Could not connect to database"}
        
        try:
            results = {}
            
            # Basic database info
            results["database_info"] = self.run_query(
                "SELECT COUNT(*) as total_embeddings, COUNT(DISTINCT metadata->>'$.source') as unique_files, AVG(LENGTH(content)) as avg_chunk_length FROM embeddings;",
                "Database Overview"
            )
            
            # Chunk length distribution
            results["chunk_distribution"] = self.run_query(
                """SELECT 
                    CASE 
                        WHEN LENGTH(content) < 100 THEN 'Very Short (<100)'
                        WHEN LENGTH(content) < 500 THEN 'Short (100-500)'
                        WHEN LENGTH(content) < 1000 THEN 'Medium (500-1000)'
                        WHEN LENGTH(content) < 2000 THEN 'Long (1000-2000)'
                        ELSE 'Very Long (>2000)'
                    END as length_category,
                    COUNT(*) as chunk_count
                FROM embeddings
                GROUP BY length_category
                ORDER BY chunk_count DESC;""",
                "Chunk Length Distribution"
            )
            
            # Metadata completeness
            results["metadata_completeness"] = self.run_query(
                """SELECT 
                    COUNT(*) as total_chunks,
                    SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
                    SUM(CASE WHEN metadata->>'$.class_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_class_names,
                    SUM(CASE WHEN metadata->>'$.function_names' IS NOT NULL THEN 1 ELSE 0 END) as chunks_with_function_names
                FROM embeddings;""",
                "Metadata Completeness"
            )
            
            # Top files by chunk count
            results["top_files"] = self.run_query(
                """SELECT 
                    metadata->>'$.source' as file_path,
                    COUNT(*) as chunk_count,
                    AVG(LENGTH(content)) as avg_chunk_length
                FROM embeddings
                WHERE metadata->>'$.source' IS NOT NULL
                GROUP BY metadata->>'$.source'
                ORDER BY chunk_count DESC
                LIMIT 10;""",
                "Top Files by Chunk Count"
            )
            
            # Chunk types
            results["chunk_types"] = self.run_query(
                """SELECT 
                    metadata->>'$.type' as chunk_type,
                    COUNT(*) as count
                FROM embeddings
                WHERE metadata->>'$.type' IS NOT NULL
                GROUP BY metadata->>'$.type'
                ORDER BY count DESC;""",
                "Chunk Types"
            )
            
            return results
        finally:
            self.disconnect()
    
    def run_specific_debug(self, debug_type: str) -> Dict[str, Any]:
        """Run specific debug queries based on type."""
        if not self.connect():
            return {"error": "Could not connect to database"}
        
        try:
            results = {}
            
            if debug_type == "chunking":
                # Chunking quality analysis
                results["very_short_chunks"] = self.run_query(
                    "SELECT id, metadata->>'$.source' as source, LENGTH(content) as length, content FROM embeddings WHERE LENGTH(content) < 50 ORDER BY LENGTH(content);",
                    "Very Short Chunks (<50 chars)"
                )
                
                results["very_long_chunks"] = self.run_query(
                    "SELECT id, metadata->>'$.source' as source, LENGTH(content) as length, SUBSTR(content, 1, 200) as preview FROM embeddings WHERE LENGTH(content) > 3000 ORDER BY LENGTH(content) DESC LIMIT 10;",
                    "Very Long Chunks (>3000 chars)"
                )
                
                results["file_distribution"] = self.run_query(
                    """SELECT 
                        metadata->>'$.source' as file_path,
                        COUNT(*) as chunk_count,
                        AVG(LENGTH(content)) as avg_length,
                        MIN(LENGTH(content)) as min_length,
                        MAX(LENGTH(content)) as max_length
                    FROM embeddings
                    WHERE metadata->>'$.source' IS NOT NULL
                    GROUP BY metadata->>'$.source'
                    ORDER BY chunk_count DESC
                    LIMIT 15;""",
                    "File-level Chunk Distribution"
                )
            
            elif debug_type == "metadata":
                # Metadata quality analysis
                results["missing_metadata"] = self.run_query(
                    """SELECT 
                        id,
                        metadata->>'$.source' as source,
                        metadata->>'$.type' as chunk_type,
                        CASE 
                            WHEN metadata->>'$.class_names' IS NULL THEN 'Missing class names'
                            WHEN metadata->>'$.function_names' IS NULL THEN 'Missing function names'
                            WHEN metadata->>'$.screen_name' IS NULL THEN 'Missing screen name'
                            ELSE 'Other missing metadata'
                        END as missing_field
                    FROM embeddings
                    WHERE metadata->>'$.class_names' IS NULL 
                       OR metadata->>'$.function_names' IS NULL
                       OR metadata->>'$.screen_name' IS NULL
                    ORDER BY metadata->>'$.source'
                    LIMIT 20;""",
                    "Chunks with Missing Metadata"
                )
                
                results["semantic_anchors"] = self.run_query(
                    """SELECT 
                        SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
                        SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'false' THEN 1 ELSE 0 END) as chunks_without_anchors,
                        COUNT(*) as total_chunks
                    FROM embeddings;""",
                    "Semantic Anchors Analysis"
                )
                
                results["sample_metadata"] = self.run_query(
                    """SELECT 
                        id,
                        metadata->>'$.source' as source,
                        metadata->>'$.class_names' as class_names,
                        metadata->>'$.function_names' as function_names,
                        metadata->>'$.screen_name' as screen_name,
                        metadata->>'$.type' as chunk_type,
                        metadata->>'$.has_semantic_anchors' as has_anchors
                    FROM embeddings
                    WHERE metadata->>'$.source' IS NOT NULL
                    ORDER BY RANDOM()
                    LIMIT 10;""",
                    "Sample Metadata"
                )
            
            elif debug_type == "retrieval":
                # Retrieval performance analysis
                results["embedding_stats"] = self.run_query(
                    """SELECT 
                        COUNT(*) as total_embeddings,
                        AVG(LENGTH(embedding)) as avg_embedding_size,
                        MIN(LENGTH(embedding)) as min_embedding_size,
                        MAX(LENGTH(embedding)) as max_embedding_size
                    FROM embeddings;""",
                    "Embedding Statistics"
                )
                
                results["sample_embeddings"] = self.run_query(
                    """SELECT 
                        id,
                        metadata->>'$.source' as source,
                        LENGTH(embedding) as embedding_size,
                        metadata->>'$.type' as chunk_type
                    FROM embeddings
                    ORDER BY RANDOM()
                    LIMIT 10;""",
                    "Sample Embeddings"
                )
            
            elif debug_type == "performance":
                # Performance analysis
                results["database_size"] = self.run_query(
                    """SELECT 
                        'embeddings' as table_name,
                        COUNT(*) as row_count,
                        SUM(LENGTH(content)) as total_content_size,
                        SUM(LENGTH(embedding)) as total_embedding_size
                    FROM embeddings;""",
                    "Database Size Analysis"
                )
                
                results["file_extensions"] = self.run_query(
                    """SELECT 
                        SUBSTR(metadata->>'$.source', -4) as file_extension,
                        COUNT(*) as chunk_count,
                        COUNT(DISTINCT metadata->>'$.source') as file_count
                    FROM embeddings
                    WHERE metadata->>'$.source' IS NOT NULL
                    GROUP BY SUBSTR(metadata->>'$.source', -4)
                    ORDER BY chunk_count DESC;""",
                    "File Extension Distribution"
                )
            
            return results
        finally:
            self.disconnect()

def print_quick_analysis(results: Dict[str, Any]):
    """Print a formatted quick analysis."""
    print("=" * 80)
    print("QUICK RAG PIPELINE ANALYSIS")
    print("=" * 80)
    
    if "database_info" in results and results["database_info"]:
        info = results["database_info"][0]
        print(f"\n📊 DATABASE OVERVIEW:")
        print(f"  Total Embeddings: {info.get('total_embeddings', 0)}")
        print(f"  Unique Files: {info.get('unique_files', 0)}")
        print(f"  Avg Chunk Length: {info.get('avg_chunk_length', 0):.0f} chars")
    
    if "chunk_distribution" in results:
        print(f"\n🔪 CHUNK LENGTH DISTRIBUTION:")
        for dist in results["chunk_distribution"]:
            print(f"  {dist['length_category']}: {dist['chunk_count']} chunks")
    
    if "metadata_completeness" in results and results["metadata_completeness"]:
        meta = results["metadata_completeness"][0]
        total = meta.get('total_chunks', 0)
        if total > 0:
            print(f"\n🏷️ METADATA COMPLETENESS:")
            print(f"  Total Chunks: {total}")
            print(f"  With Semantic Anchors: {meta.get('chunks_with_anchors', 0)} ({meta.get('chunks_with_anchors', 0)/total*100:.1f}%)")
            print(f"  With Class Names: {meta.get('chunks_with_class_names', 0)} ({meta.get('chunks_with_class_names', 0)/total*100:.1f}%)")
            print(f"  With Function Names: {meta.get('chunks_with_function_names', 0)} ({meta.get('chunks_with_function_names', 0)/total*100:.1f}%)")
    
    if "top_files" in results:
        print(f"\n📁 TOP FILES BY CHUNK COUNT:")
        for i, file_info in enumerate(results["top_files"][:5]):
            print(f"  {i+1}. {file_info['file_path']}: {file_info['chunk_count']} chunks")
    
    if "chunk_types" in results:
        print(f"\n🏷️ CHUNK TYPES:")
        for chunk_type in results["chunk_types"][:5]:
            print(f"  {chunk_type['chunk_type']}: {chunk_type['count']} chunks")
    
    print("\n" + "=" * 80)

def run_debug_analysis(db_path: str, debug_type: str = "quick") -> Dict[str, Any]:
    """Run debug analysis on the Chroma database."""
    runner = QueryRunner(db_path)
    
    if debug_type == "quick":
        return runner.run_quick_analysis()
    else:
        return runner.run_specific_debug(debug_type)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        debug_type = sys.argv[2] if len(sys.argv) > 2 else "quick"
        
        results = run_debug_analysis(db_path, debug_type)
        
        if debug_type == "quick":
            print_quick_analysis(results)
        else:
            print(json.dumps(results, indent=2))
    else:
        print("Usage: python query_runner.py <path_to_chroma_db> [debug_type]")
        print("Debug types: quick, chunking, metadata, retrieval, performance") 