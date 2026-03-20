"""
Graph building service
Interface 2: Build Standalone Graph using Zep API
"""

import os
import uuid
import time
import threading
from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass

from ..config import Config
from ..models.task import TaskManager, TaskStatus
from .graphiti_client import GraphitiClient
from .text_processor import TextProcessor


@dataclass
class GraphInfo:
    """Graph information"""
    graph_id: str
    node_count: int
    edge_count: int
    entity_types: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "graph_id": self.graph_id,
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "entity_types": self.entity_types,
        }


class GraphBuilderService:
    """
    Graph building service
    Responsible for calling Zep API to build knowledge graphs
    """
    
    def __init__(self, api_key: Optional[str] = None):
        self.graphiti = GraphitiClient()
        self.task_manager = TaskManager()
    
    def build_graph_async(
        self,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str = "MiroFish Graph",
        chunk_size: int = 500,
        chunk_overlap: int = 50,
        batch_size: int = 3
    ) -> str:
        """
        Build graph asynchronously

        Args:
            text: Input text
            ontology: Ontology definition (output from Interface 1)
            graph_name: Graph name
            chunk_size: Text chunk size
            chunk_overlap: Chunk overlap size
            batch_size: Number of chunks per batch

        Returns:
            Task ID
        """
        # Create task
        task_id = self.task_manager.create_task(
            task_type="graph_build",
            metadata={
                "graph_name": graph_name,
                "chunk_size": chunk_size,
                "text_length": len(text),
            }
        )
        
        # Execute build in background thread
        thread = threading.Thread(
            target=self._build_graph_worker,
            args=(task_id, text, ontology, graph_name, chunk_size, chunk_overlap, batch_size)
        )
        thread.daemon = True
        thread.start()
        
        return task_id
    
    def _build_graph_worker(
        self,
        task_id: str,
        text: str,
        ontology: Dict[str, Any],
        graph_name: str,
        chunk_size: int,
        chunk_overlap: int,
        batch_size: int
    ):
        """Graph building worker thread"""
        try:
            self.task_manager.update_task(
                task_id,
                status=TaskStatus.PROCESSING,
                progress=5,
                message="Starting graph construction..."
            )

            # 1. Create graph
            graph_id = self.create_graph(graph_name)
            self.task_manager.update_task(
                task_id,
                progress=10,
                message=f"Graph created: {graph_id}"
            )

            # 2. Set ontology
            self.set_ontology(graph_id, ontology)
            self.task_manager.update_task(
                task_id,
                progress=15,
                message="Ontology configured"
            )

            # 3. Split text into chunks
            chunks = TextProcessor.split_text(text, chunk_size, chunk_overlap)
            total_chunks = len(chunks)
            self.task_manager.update_task(
                task_id,
                progress=20,
                message=f"Text split into {total_chunks} chunks"
            )

            # 4. Send data in batches
            episode_uuids = self.add_text_batches(
                graph_id, chunks, batch_size,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=20 + int(prog * 0.4),  # 20-60%
                    message=msg
                )
            )

            # 5. Wait for Zep processing to complete
            self.task_manager.update_task(
                task_id,
                progress=60,
                message="Waiting for Zep to process data..."
            )

            self._wait_for_episodes(
                episode_uuids,
                lambda msg, prog: self.task_manager.update_task(
                    task_id,
                    progress=60 + int(prog * 0.3),  # 60-90%
                    message=msg
                )
            )

            # 6. Get graph info
            self.task_manager.update_task(
                task_id,
                progress=90,
                message="Retrieving graph information..."
            )

            graph_info = self._get_graph_info(graph_id)

            # Complete
            self.task_manager.complete_task(task_id, {
                "graph_id": graph_id,
                "graph_info": graph_info.to_dict(),
                "chunks_processed": total_chunks,
            })
            
        except Exception as e:
            import traceback
            error_msg = f"{str(e)}\n{traceback.format_exc()}"
            self.task_manager.fail_task(task_id, error_msg)
    
    def create_graph(self, name: str) -> str:
        """Create graph namespace (public method)"""
        graph_id = f"mirofish_{uuid.uuid4().hex[:16]}"

        self.graphiti.create_graph(
            graph_id=graph_id,
            name=name,
            description="MiroFish Social Simulation Graph"
        )

        return graph_id
    
    def set_ontology(self, graph_id: str, ontology: Dict[str, Any]):
        """Set graph ontology (no-op for Graphiti, which auto-extracts types)"""
        entities = ontology.get("entity_types", {})
        edges = ontology.get("edge_types", {})
        self.graphiti.set_ontology(
            graph_ids=[graph_id],
            entities=entities,
            edges=edges,
        )
    
    def add_text_batches(
        self,
        graph_id: str,
        chunks: List[str],
        batch_size: int = 3,
        progress_callback: Optional[Callable] = None
    ) -> List[str]:
        """Add text to graph in batches. Graphiti processes synchronously, returns empty list."""
        total_chunks = len(chunks)

        if progress_callback:
            progress_callback(
                f"Adding {total_chunks} text chunks to graph (Graphiti processes synchronously)...",
                0
            )

        texts = [chunk for chunk in chunks]
        try:
            self.graphiti.add_episodes_batch(graph_id=graph_id, texts=texts)
        except Exception as e:
            if progress_callback:
                progress_callback(f"Batch add failed: {str(e)}", 0)
            raise

        if progress_callback:
            progress_callback(f"All {total_chunks} chunks processed.", 1.0)

        # Graphiti processes synchronously, no episode UUIDs to track
        return []
    
    def _wait_for_episodes(
        self,
        episode_uuids: List[str],
        progress_callback: Optional[Callable] = None,
        timeout: int = 600
    ):
        """Graphiti processes episodes synchronously, so no polling needed."""
        if progress_callback:
            progress_callback("All episodes processed synchronously (Graphiti).", 1.0)
    
    def _get_graph_info(self, graph_id: str) -> GraphInfo:
        """Get graph information"""
        stats = self.graphiti.get_graph_statistics(graph_id)

        return GraphInfo(
            graph_id=graph_id,
            node_count=stats.get("total_nodes", 0),
            edge_count=stats.get("total_edges", 0),
            entity_types=list(stats.get("entity_types", {}).keys())
        )
    
    def get_graph_data(self, graph_id: str) -> Dict[str, Any]:
        """
        Get complete graph data (including detailed information)

        Args:
            graph_id: Graph ID

        Returns:
            Dictionary containing nodes and edges, including timestamps, attributes, and other detailed data
        """
        nodes = self.graphiti.get_nodes_by_graph(graph_id, limit=2000)
        edges = self.graphiti.get_edges_by_graph(graph_id, limit=5000)

        # Create node mapping for getting node names
        node_map = {}
        for node in nodes:
            node_map[node.uuid] = node.name or ""

        def _s(v):
            """Convert any value to JSON-safe type."""
            if v is None:
                return None
            if isinstance(v, (str, int, float, bool)):
                return v
            if isinstance(v, dict):
                return {k: _s(val) for k, val in v.items()}
            if isinstance(v, list):
                return [_s(item) for item in v]
            return str(v)

        nodes_data = []
        for node in nodes:
            nodes_data.append({
                "uuid": str(node.uuid) if node.uuid else "",
                "name": node.name or "",
                "labels": [node.entity_type] if node.entity_type else [],
                "summary": node.summary or "",
                "attributes": _s(node.attributes) or {},
                "created_at": _s(node.created_at),
            })

        edges_data = []
        for edge in edges:
            edges_data.append({
                "uuid": str(edge.uuid) if edge.uuid else "",
                "name": edge.relation_type or "",
                "fact": edge.fact or "",
                "fact_type": edge.relation_type or "",
                "source_node_uuid": str(edge.source_node_uuid) if edge.source_node_uuid else "",
                "target_node_uuid": str(edge.target_node_uuid) if edge.target_node_uuid else "",
                "source_node_name": node_map.get(edge.source_node_uuid, ""),
                "target_node_name": node_map.get(edge.target_node_uuid, ""),
                "attributes": _s(edge.attributes) or {},
                "created_at": _s(edge.created_at),
                "valid_at": _s(edge.valid_at),
                "invalid_at": _s(edge.invalid_at),
                "expired_at": _s(edge.expired_at),
                "episodes": [],
            })

        return {
            "graph_id": graph_id,
            "nodes": nodes_data,
            "edges": edges_data,
            "node_count": len(nodes_data),
            "edge_count": len(edges_data),
        }
    
    def delete_graph(self, graph_id: str):
        """Delete graph"""
        self.graphiti.delete_graph(graph_id=graph_id)

