#!/usr/bin/env python3
"""
Database Inspector for Chroma Vector Database

Provides comprehensive SQLite queries to debug:
- Chunking quality and distribution
- Metadata extraction and storage
- Retrieval performance and ranking
- File processing statistics
- Vector embeddings analysis
"""

import os
import sqlite3
import json
import pandas as pd
from typing import Dict, List, Any, Optional
from datetime import datetime
import numpy as np

class ChromaDBInspector:
    """Comprehensive inspector for Chroma vector database debugging."""
    
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
    
    def get_database_info(self) -> Dict[str, Any]:
        """Get basic database information."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Get table information
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
        tables = [row[0] for row in cursor.fetchall()]
        
        # Get embedding count
        cursor.execute("SELECT COUNT(*) FROM embeddings;")
        embedding_count = cursor.fetchone()[0]
        
        # Get collection info
        cursor.execute("SELECT COUNT(*) FROM collections;")
        collection_count = cursor.fetchone()[0]
        
        return {
            "tables": tables,
            "embedding_count": embedding_count,
            "collection_count": collection_count,
            "database_size_mb": os.path.getsize(self.db_path) / (1024 * 1024)
        }
    
    def analyze_chunking_quality(self) -> Dict[str, Any]:
        """Analyze chunking quality and distribution."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Get chunk statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                AVG(LENGTH(content)) as avg_chunk_length,
                MIN(LENGTH(content)) as min_chunk_length,
                MAX(LENGTH(content)) as max_chunk_length,
                COUNT(DISTINCT metadata->>'$.source') as unique_files
            FROM embeddings;
        """)
        
        chunk_stats = cursor.fetchone()
        
        # Get chunk length distribution
        cursor.execute("""
            SELECT 
                CASE 
                    WHEN LENGTH(content) < 100 THEN 'Very Short (<100)'
                    WHEN LENGTH(content) < 500 THEN 'Short (100-500)'
                    WHEN LENGTH(content) < 1000 THEN 'Medium (500-1000)'
                    WHEN LENGTH(content) < 2000 THEN 'Long (1000-2000)'
                    ELSE 'Very Long (>2000)'
                END as length_category,
                COUNT(*) as count
            FROM embeddings
            GROUP BY length_category
            ORDER BY count DESC;
        """)
        
        length_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Get file-level chunk distribution
        cursor.execute("""
            SELECT 
                metadata->>'$.source' as file_path,
                COUNT(*) as chunk_count,
                AVG(LENGTH(content)) as avg_chunk_length
            FROM embeddings
            GROUP BY metadata->>'$.source'
            ORDER BY chunk_count DESC
            LIMIT 10;
        """)
        
        file_distribution = [dict(row) for row in cursor.fetchall()]
        
        return {
            "chunk_statistics": dict(chunk_stats),
            "length_distribution": length_distribution,
            "file_distribution": file_distribution
        }
    
    def analyze_metadata_quality(self) -> Dict[str, Any]:
        """Analyze metadata extraction and quality."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Check metadata completeness
        cursor.execute("""
            SELECT 
                COUNT(*) as total_chunks,
                SUM(CASE WHEN metadata->>'$.source' IS NOT NULL THEN 1 ELSE 0 END) as has_source,
                SUM(CASE WHEN metadata->>'$.class_names' IS NOT NULL THEN 1 ELSE 0 END) as has_class_names,
                SUM(CASE WHEN metadata->>'$.function_names' IS NOT NULL THEN 1 ELSE 0 END) as has_function_names,
                SUM(CASE WHEN metadata->>'$.screen_name' IS NOT NULL THEN 1 ELSE 0 END) as has_screen_name,
                SUM(CASE WHEN metadata->>'$.business_logic_indicators' IS NOT NULL THEN 1 ELSE 0 END) as has_business_logic,
                SUM(CASE WHEN metadata->>'$.ui_elements' IS NOT NULL THEN 1 ELSE 0 END) as has_ui_elements,
                SUM(CASE WHEN metadata->>'$.dependencies' IS NOT NULL THEN 1 ELSE 0 END) as has_dependencies,
                SUM(CASE WHEN metadata->>'$.api_endpoints' IS NOT NULL THEN 1 ELSE 0 END) as has_api_endpoints
            FROM embeddings;
        """)
        
        metadata_completeness = dict(cursor.fetchone())
        
        # Get metadata field distribution
        cursor.execute("""
            SELECT 
                metadata->>'$.source' as file_path,
                metadata->>'$.class_names' as class_names,
                metadata->>'$.function_names' as function_names,
                metadata->>'$.screen_name' as screen_name,
                metadata->>'$.type' as chunk_type
            FROM embeddings
            WHERE metadata->>'$.source' IS NOT NULL
            LIMIT 20;
        """)
        
        sample_metadata = [dict(row) for row in cursor.fetchall()]
        
        # Analyze chunk types
        cursor.execute("""
            SELECT 
                metadata->>'$.type' as chunk_type,
                COUNT(*) as count
            FROM embeddings
            WHERE metadata->>'$.type' IS NOT NULL
            GROUP BY metadata->>'$.type'
            ORDER BY count DESC;
        """)
        
        chunk_types = [dict(row) for row in cursor.fetchall()]
        
        return {
            "metadata_completeness": metadata_completeness,
            "sample_metadata": sample_metadata,
            "chunk_types": chunk_types
        }
    
    def analyze_retrieval_performance(self, test_queries: List[str] = None) -> Dict[str, Any]:
        """Analyze retrieval performance and ranking."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Get embedding statistics
        cursor.execute("""
            SELECT 
                COUNT(*) as total_embeddings,
                AVG(LENGTH(embedding)) as avg_embedding_size,
                MIN(LENGTH(embedding)) as min_embedding_size,
                MAX(LENGTH(embedding)) as max_embedding_size
            FROM embeddings;
        """)
        
        embedding_stats = dict(cursor.fetchone())
        
        # Get distance distribution (if available)
        cursor.execute("""
            SELECT 
                distance,
                COUNT(*) as count
            FROM embeddings
            WHERE distance IS NOT NULL
            GROUP BY distance
            ORDER BY distance;
        """)
        
        distance_distribution = [dict(row) for row in cursor.fetchall()]
        
        # Sample embeddings for analysis
        cursor.execute("""
            SELECT 
                id,
                metadata->>'$.source' as source,
                LENGTH(embedding) as embedding_size,
                distance
            FROM embeddings
            ORDER BY RANDOM()
            LIMIT 10;
        """)
        
        sample_embeddings = [dict(row) for row in cursor.fetchall()]
        
        return {
            "embedding_statistics": embedding_stats,
            "distance_distribution": distance_distribution,
            "sample_embeddings": sample_embeddings
        }
    
    def get_file_processing_stats(self) -> Dict[str, Any]:
        """Get statistics about file processing."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Get file processing statistics
        cursor.execute("""
            SELECT 
                metadata->>'$.source' as file_path,
                COUNT(*) as chunk_count,
                AVG(LENGTH(content)) as avg_chunk_length,
                MIN(LENGTH(content)) as min_chunk_length,
                MAX(LENGTH(content)) as max_chunk_length,
                COUNT(DISTINCT metadata->>'$.type') as chunk_type_count
            FROM embeddings
            WHERE metadata->>'$.source' IS NOT NULL
            GROUP BY metadata->>'$.source'
            ORDER BY chunk_count DESC;
        """)
        
        file_stats = [dict(row) for row in cursor.fetchall()]
        
        # Get file extension distribution
        cursor.execute("""
            SELECT 
                SUBSTR(metadata->>'$.source', -4) as file_extension,
                COUNT(*) as chunk_count,
                COUNT(DISTINCT metadata->>'$.source') as file_count
            FROM embeddings
            WHERE metadata->>'$.source' IS NOT NULL
            GROUP BY SUBSTR(metadata->>'$.source', -4)
            ORDER BY chunk_count DESC;
        """)
        
        extension_stats = [dict(row) for row in cursor.fetchall()]
        
        return {
            "file_processing_stats": file_stats,
            "extension_distribution": extension_stats
        }
    
    def get_semantic_analysis(self) -> Dict[str, Any]:
        """Analyze semantic relationships and anchors."""
        if not self.conn:
            return {}
        
        cursor = self.conn.cursor()
        
        # Get semantic anchors distribution
        cursor.execute("""
            SELECT 
                SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as chunks_with_anchors,
                SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'false' THEN 1 ELSE 0 END) as chunks_without_anchors,
                COUNT(*) as total_chunks
            FROM embeddings;
        """)
        
        anchor_stats = dict(cursor.fetchone())
        
        # Get class and function distribution
        cursor.execute("""
            SELECT 
                metadata->>'$.class_names' as class_names,
                metadata->>'$.function_names' as function_names,
                metadata->>'$.screen_name' as screen_name,
                COUNT(*) as count
            FROM embeddings
            WHERE metadata->>'$.class_names' IS NOT NULL 
               OR metadata->>'$.function_names' IS NOT NULL
               OR metadata->>'$.screen_name' IS NOT NULL
            GROUP BY metadata->>'$.class_names', metadata->>'$.function_names', metadata->>'$.screen_name'
            ORDER BY count DESC
            LIMIT 20;
        """)
        
        semantic_entities = [dict(row) for row in cursor.fetchall()]
        
        # Get business logic indicators
        cursor.execute("""
            SELECT 
                metadata->>'$.business_logic_indicators' as business_logic,
                COUNT(*) as count
            FROM embeddings
            WHERE metadata->>'$.business_logic_indicators' IS NOT NULL
            GROUP BY metadata->>'$.business_logic_indicators'
            ORDER BY count DESC
            LIMIT 10;
        """)
        
        business_logic = [dict(row) for row in cursor.fetchall()]
        
        return {
            "anchor_statistics": anchor_stats,
            "semantic_entities": semantic_entities,
            "business_logic_indicators": business_logic
        }
    
    def get_debug_queries(self) -> List[str]:
        """Get a list of useful debug queries."""
        return [
            # Basic database info
            "SELECT COUNT(*) FROM embeddings;",
            "SELECT COUNT(DISTINCT metadata->>'$.source') FROM embeddings;",
            
            # Chunking analysis
            "SELECT AVG(LENGTH(content)) as avg_length, MIN(LENGTH(content)) as min_length, MAX(LENGTH(content)) as max_length FROM embeddings;",
            "SELECT metadata->>'$.source' as file, COUNT(*) as chunks FROM embeddings GROUP BY metadata->>'$.source' ORDER BY chunks DESC LIMIT 10;",
            
            # Metadata analysis
            "SELECT metadata->>'$.type' as chunk_type, COUNT(*) as count FROM embeddings GROUP BY metadata->>'$.type' ORDER BY count DESC;",
            "SELECT COUNT(*) as total, SUM(CASE WHEN metadata->>'$.has_semantic_anchors' = 'true' THEN 1 ELSE 0 END) as with_anchors FROM embeddings;",
            
            # File processing
            "SELECT SUBSTR(metadata->>'$.source', -4) as ext, COUNT(*) as count FROM embeddings GROUP BY SUBSTR(metadata->>'$.source', -4) ORDER BY count DESC;",
            
            # Embedding analysis
            "SELECT AVG(LENGTH(embedding)) as avg_embedding_size FROM embeddings;",
            
            # Sample data
            "SELECT id, metadata->>'$.source' as source, LENGTH(content) as content_length FROM embeddings ORDER BY RANDOM() LIMIT 5;"
        ]
    
    def run_custom_query(self, query: str) -> List[Dict[str, Any]]:
        """Run a custom SQL query."""
        if not self.conn:
            return []
        
        try:
            cursor = self.conn.cursor()
            cursor.execute(query)
            return [dict(row) for row in cursor.fetchall()]
        except Exception as e:
            print(f"Error running query: {e}")
            return []
    
    def generate_debug_report(self) -> Dict[str, Any]:
        """Generate a comprehensive debug report."""
        if not self.connect():
            return {"error": "Could not connect to database"}
        
        try:
            report = {
                "database_info": self.get_database_info(),
                "chunking_quality": self.analyze_chunking_quality(),
                "metadata_quality": self.analyze_metadata_quality(),
                "retrieval_performance": self.analyze_retrieval_performance(),
                "file_processing_stats": self.get_file_processing_stats(),
                "semantic_analysis": self.get_semantic_analysis(),
                "debug_queries": self.get_debug_queries(),
                "timestamp": datetime.now().isoformat()
            }
            
            return report
        finally:
            self.disconnect()

def inspect_chroma_database(db_path: str) -> Dict[str, Any]:
    """Convenience function to inspect a Chroma database."""
    inspector = ChromaDBInspector(db_path)
    return inspector.generate_debug_report()

def print_debug_report(report: Dict[str, Any]):
    """Print a formatted debug report."""
    print("=" * 80)
    print("CHROMA VECTOR DATABASE DEBUG REPORT")
    print("=" * 80)
    
    # Database Info
    if "database_info" in report:
        print("\n📊 DATABASE INFORMATION:")
        print("-" * 40)
        info = report["database_info"]
        print(f"Tables: {info.get('tables', [])}")
        print(f"Embeddings: {info.get('embedding_count', 0)}")
        print(f"Collections: {info.get('collection_count', 0)}")
        print(f"Database Size: {info.get('database_size_mb', 0):.2f} MB")
    
    # Chunking Quality
    if "chunking_quality" in report:
        print("\n🔪 CHUNKING QUALITY ANALYSIS:")
        print("-" * 40)
        chunking = report["chunking_quality"]
        if "chunk_statistics" in chunking:
            stats = chunking["chunk_statistics"]
            print(f"Total Chunks: {stats.get('total_chunks', 0)}")
            print(f"Unique Files: {stats.get('unique_files', 0)}")
            print(f"Avg Chunk Length: {stats.get('avg_chunk_length', 0):.0f} chars")
            print(f"Min/Max Length: {stats.get('min_chunk_length', 0)}/{stats.get('max_chunk_length', 0)} chars")
        
        if "length_distribution" in chunking:
            print("\nChunk Length Distribution:")
            for dist in chunking["length_distribution"]:
                print(f"  {dist['length_category']}: {dist['count']} chunks")
    
    # Metadata Quality
    if "metadata_quality" in report:
        print("\n🏷️ METADATA QUALITY ANALYSIS:")
        print("-" * 40)
        metadata = report["metadata_quality"]
        if "metadata_completeness" in metadata:
            completeness = metadata["metadata_completeness"]
            total = completeness.get('total_chunks', 0)
            if total > 0:
                print(f"Total Chunks: {total}")
                print(f"Has Source: {completeness.get('has_source', 0)} ({completeness.get('has_source', 0)/total*100:.1f}%)")
                print(f"Has Class Names: {completeness.get('has_class_names', 0)} ({completeness.get('has_class_names', 0)/total*100:.1f}%)")
                print(f"Has Function Names: {completeness.get('has_function_names', 0)} ({completeness.get('has_function_names', 0)/total*100:.1f}%)")
                print(f"Has Screen Name: {completeness.get('has_screen_name', 0)} ({completeness.get('has_screen_name', 0)/total*100:.1f}%)")
                print(f"Has Business Logic: {completeness.get('has_business_logic', 0)} ({completeness.get('has_business_logic', 0)/total*100:.1f}%)")
    
    # File Processing Stats
    if "file_processing_stats" in report:
        print("\n📁 FILE PROCESSING STATISTICS:")
        print("-" * 40)
        file_stats = report["file_processing_stats"]
        if "file_processing_stats" in file_stats:
            print("Top 5 Files by Chunk Count:")
            for i, file_stat in enumerate(file_stats["file_processing_stats"][:5]):
                print(f"  {i+1}. {file_stat['file_path']}: {file_stat['chunk_count']} chunks")
    
    # Semantic Analysis
    if "semantic_analysis" in report:
        print("\n🧠 SEMANTIC ANALYSIS:")
        print("-" * 40)
        semantic = report["semantic_analysis"]
        if "anchor_statistics" in semantic:
            anchors = semantic["anchor_statistics"]
            total = anchors.get('total_chunks', 0)
            if total > 0:
                with_anchors = anchors.get('chunks_with_anchors', 0)
                print(f"Chunks with Semantic Anchors: {with_anchors}/{total} ({with_anchors/total*100:.1f}%)")
    
    print("\n" + "=" * 80)

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        db_path = sys.argv[1]
        report = inspect_chroma_database(db_path)
        print_debug_report(report)
    else:
        print("Usage: python db_inspector.py <path_to_chroma_db>") 