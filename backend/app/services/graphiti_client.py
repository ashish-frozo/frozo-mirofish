"""
GraphitiClient - Adapter layer replacing Zep Cloud with self-hosted Graphiti.

Maps the Zep Cloud API surface used by MiroFish to Graphiti Core SDK + Neo4j direct queries.
"""

import asyncio
import os
from typing import Optional, Any
from dataclasses import dataclass, field
from ..config import Config
from ..utils.logger import get_logger

logger = get_logger('mirofish.graphiti')


@dataclass
class GraphNode:
    """Represents a node/entity from the knowledge graph."""
    uuid: str
    name: str
    entity_type: str = ""
    summary: str = ""
    created_at: str = ""
    attributes: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "name": self.name,
            "entity_type": self.entity_type,
            "summary": self.summary,
            "created_at": self.created_at,
            "attributes": self.attributes,
        }


@dataclass
class GraphEdge:
    """Represents an edge/relationship from the knowledge graph."""
    uuid: str
    source_node_uuid: str
    target_node_uuid: str
    relation_type: str = ""
    fact: str = ""
    created_at: str = ""
    expired_at: str = ""  # Graphiti temporal feature
    valid_at: str = ""
    invalid_at: str = ""
    attributes: dict = field(default_factory=dict)

    def to_dict(self):
        return {
            "uuid": self.uuid,
            "source_node_uuid": self.source_node_uuid,
            "target_node_uuid": self.target_node_uuid,
            "relation_type": self.relation_type,
            "fact": self.fact,
            "created_at": self.created_at,
            "expired_at": self.expired_at,
            "valid_at": self.valid_at,
            "invalid_at": self.invalid_at,
            "attributes": self.attributes,
        }


@dataclass
class SearchResult:
    """A search result from the knowledge graph."""
    fact: str
    uuid: str = ""
    score: float = 0.0
    source_node: str = ""
    target_node: str = ""
    relation_type: str = ""
    created_at: str = ""
    valid_at: str = ""
    invalid_at: str = ""


@dataclass
class EpisodeStatus:
    """Status of an episode processing."""
    uuid: str
    processed: bool = True  # Graphiti processes synchronously


def _run_async(coro):
    """Run async coroutine in sync context."""
    try:
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # We're already in an async context, create a new thread
            import concurrent.futures
            with concurrent.futures.ThreadPoolExecutor() as pool:
                return pool.submit(asyncio.run, coro).result()
        return loop.run_until_complete(coro)
    except RuntimeError:
        return asyncio.run(coro)


class GraphitiClient:
    """
    Adapter that provides a Zep-compatible interface over Graphiti Core + Neo4j.

    Each MiroFish graph_id maps to a Graphiti group_id for namespace isolation.
    """

    def __init__(self):
        self._graphiti = None
        self._neo4j_driver = None

    def _get_graphiti(self):
        """Lazy-init Graphiti instance."""
        if self._graphiti is None:
            from graphiti_core import Graphiti
            self._graphiti = Graphiti(
                uri=Config.NEO4J_URI,
                user=Config.NEO4J_USER,
                password=Config.NEO4J_PASSWORD,
            )
        return self._graphiti

    def _get_neo4j(self):
        """Lazy-init Neo4j driver for direct queries."""
        if self._neo4j_driver is None:
            from neo4j import GraphDatabase
            self._neo4j_driver = GraphDatabase.driver(
                Config.NEO4J_URI,
                auth=(Config.NEO4J_USER, Config.NEO4J_PASSWORD),
            )
        return self._neo4j_driver

    # ========== Graph Lifecycle ==========

    def create_graph(self, graph_id: str, name: str = "", description: str = ""):
        """Create/initialize a graph namespace. In Graphiti, this is implicit via group_id."""
        logger.info(f"Initializing graph namespace: {graph_id}")
        # Graphiti uses group_id to namespace data. No explicit create needed.
        # Initialize indexes if first time
        try:
            graphiti = self._get_graphiti()
            _run_async(graphiti.build_indices_and_constraints())
            logger.info(f"Graph {graph_id} initialized")
        except Exception as e:
            logger.warning(f"Index initialization (may already exist): {e}")

    def delete_graph(self, graph_id: str):
        """Delete all data for a graph namespace."""
        logger.info(f"Deleting graph: {graph_id}")
        driver = self._get_neo4j()
        with driver.session() as session:
            # Delete all nodes and edges with this group_id
            session.run(
                "MATCH (n) WHERE n.group_id = $group_id DETACH DELETE n",
                group_id=graph_id
            )
            logger.info(f"Graph {graph_id} deleted")

    def set_ontology(self, graph_ids: list, entities: dict = None, edges: dict = None):
        """Set ontology types. Graphiti extracts types automatically from data."""
        # Graphiti doesn't require explicit ontology definition -- entities and
        # relationships are extracted automatically from episodes.
        # This is a no-op in the adapter.
        logger.info(f"Ontology set (no-op for Graphiti, auto-extracted): {graph_ids}")

    # ========== Episode Management ==========

    def add_episode(self, graph_id: str, text: str, source: str = "document"):
        """Add a single text episode to the graph."""
        graphiti = self._get_graphiti()
        from graphiti_core.nodes import EpisodeType
        from datetime import datetime, timezone

        async def _add():
            await graphiti.add_episode(
                name=source,
                episode_body=text,
                source=EpisodeType.text,
                source_description=f"MiroFish document: {source}",
                reference_time=datetime.now(timezone.utc),
                group_id=graph_id,
            )

        _run_async(_add())
        logger.info(f"Episode added to graph {graph_id} ({len(text)} chars)")

    def add_episodes_batch(self, graph_id: str, texts: list, source: str = "document"):
        """Add multiple text episodes. Processes sequentially (Graphiti is sync per episode)."""
        logger.info(f"Adding {len(texts)} episodes to graph {graph_id}")
        for i, text in enumerate(texts):
            try:
                self.add_episode(graph_id, text, source=f"{source}_chunk_{i}")
                logger.info(f"Episode {i+1}/{len(texts)} processed")
            except Exception as e:
                logger.error(f"Episode {i+1} failed: {e}")
                # Continue with remaining episodes
        logger.info(f"Batch complete: {len(texts)} episodes")

    def get_episode_status(self, episode_uuid: str) -> EpisodeStatus:
        """Get episode processing status. Graphiti processes synchronously, so always returns done."""
        return EpisodeStatus(uuid=episode_uuid, processed=True)

    # ========== Search ==========

    def search(self, graph_id: str, query: str, limit: int = 10, scope: str = "all", **kwargs) -> list:
        """Search the knowledge graph. Returns list of SearchResult."""
        graphiti = self._get_graphiti()

        async def _search():
            results = await graphiti.search(
                query=query,
                group_ids=[graph_id],
                num_results=limit,
            )
            return results

        raw_results = _run_async(_search())

        search_results = []
        for r in raw_results:
            sr = SearchResult(
                fact=getattr(r, 'fact', str(r)),
                uuid=getattr(r, 'uuid', ''),
                score=getattr(r, 'score', 0.0),
                source_node=getattr(r, 'source_node_name', ''),
                target_node=getattr(r, 'target_node_name', ''),
                relation_type=getattr(r, 'name', ''),
                created_at=str(getattr(r, 'created_at', '')),
                valid_at=str(getattr(r, 'valid_at', '')),
                invalid_at=str(getattr(r, 'invalid_at', '')),
            )
            search_results.append(sr)

        logger.info(f"Search '{query[:50]}...' returned {len(search_results)} results")
        return search_results

    # ========== Node/Entity Operations ==========

    def get_node(self, node_uuid: str) -> Optional[GraphNode]:
        """Get a single node by UUID."""
        driver = self._get_neo4j()
        with driver.session() as session:
            result = session.run(
                "MATCH (n) WHERE n.uuid = $uuid RETURN n",
                uuid=node_uuid
            ).single()
            if not result:
                return None
            node = result["n"]
            return GraphNode(
                uuid=node.get("uuid", node_uuid),
                name=node.get("name", ""),
                entity_type=node.get("entity_type", ""),
                summary=node.get("summary", ""),
                created_at=str(node.get("created_at", "")),
                attributes=dict(node),
            )

    def get_nodes_by_graph(self, graph_id: str, limit: int = 100, cursor: str = None) -> list:
        """Get paginated nodes for a graph. Returns list of GraphNode."""
        driver = self._get_neo4j()
        with driver.session() as session:
            if cursor:
                result = session.run(
                    """MATCH (n:Entity) WHERE n.group_id = $group_id AND n.uuid > $cursor
                    RETURN n ORDER BY n.uuid LIMIT $limit""",
                    group_id=graph_id, cursor=cursor, limit=limit
                )
            else:
                result = session.run(
                    """MATCH (n:Entity) WHERE n.group_id = $group_id
                    RETURN n ORDER BY n.uuid LIMIT $limit""",
                    group_id=graph_id, limit=limit
                )

            nodes = []
            for record in result:
                node = record["n"]
                nodes.append(GraphNode(
                    uuid=node.get("uuid", ""),
                    name=node.get("name", ""),
                    entity_type=node.get("entity_type", ""),
                    summary=node.get("summary", ""),
                    created_at=str(node.get("created_at", "")),
                    attributes=dict(node),
                ))
            return nodes

    def get_edges_by_graph(self, graph_id: str, limit: int = 100, cursor: str = None) -> list:
        """Get paginated edges for a graph. Returns list of GraphEdge."""
        driver = self._get_neo4j()
        with driver.session() as session:
            if cursor:
                result = session.run(
                    """MATCH (s)-[r:RELATES_TO]->(t) WHERE r.group_id = $group_id AND r.uuid > $cursor
                    RETURN r, s.uuid AS source_uuid, t.uuid AS target_uuid
                    ORDER BY r.uuid LIMIT $limit""",
                    group_id=graph_id, cursor=cursor, limit=limit
                )
            else:
                result = session.run(
                    """MATCH (s)-[r:RELATES_TO]->(t) WHERE r.group_id = $group_id
                    RETURN r, s.uuid AS source_uuid, t.uuid AS target_uuid
                    ORDER BY r.uuid LIMIT $limit""",
                    group_id=graph_id, limit=limit
                )

            edges = []
            for record in result:
                rel = record["r"]
                edges.append(GraphEdge(
                    uuid=rel.get("uuid", ""),
                    source_node_uuid=record["source_uuid"],
                    target_node_uuid=record["target_uuid"],
                    relation_type=rel.type if hasattr(rel, 'type') else rel.get("name", ""),
                    fact=rel.get("fact", ""),
                    created_at=str(rel.get("created_at", "")),
                    valid_at=str(rel.get("valid_at", "")),
                    invalid_at=str(rel.get("invalid_at", "")),
                    attributes=dict(rel),
                ))
            return edges

    def get_node_edges(self, node_uuid: str) -> list:
        """Get all edges connected to a specific node."""
        driver = self._get_neo4j()
        with driver.session() as session:
            result = session.run(
                """MATCH (s)-[r]-(t) WHERE s.uuid = $uuid
                RETURN r, s.uuid AS source_uuid, t.uuid AS target_uuid""",
                uuid=node_uuid
            )
            edges = []
            for record in result:
                rel = record["r"]
                edges.append(GraphEdge(
                    uuid=rel.get("uuid", ""),
                    source_node_uuid=record["source_uuid"],
                    target_node_uuid=record["target_uuid"],
                    relation_type=rel.type if hasattr(rel, 'type') else rel.get("name", ""),
                    fact=rel.get("fact", ""),
                    created_at=str(rel.get("created_at", "")),
                    attributes=dict(rel),
                ))
            return edges

    # ========== Statistics ==========

    def get_graph_statistics(self, graph_id: str) -> dict:
        """Get node/edge counts and entity type distribution."""
        driver = self._get_neo4j()
        with driver.session() as session:
            # Node count
            node_count = session.run(
                "MATCH (n:Entity) WHERE n.group_id = $gid RETURN count(n) AS cnt",
                gid=graph_id
            ).single()["cnt"]

            # Edge count
            edge_count = session.run(
                "MATCH ()-[r:RELATES_TO]->() WHERE r.group_id = $gid RETURN count(r) AS cnt",
                gid=graph_id
            ).single()["cnt"]

            # Entity types
            type_result = session.run(
                """MATCH (n:Entity) WHERE n.group_id = $gid
                RETURN n.entity_type AS etype, count(*) AS cnt""",
                gid=graph_id
            )
            entity_types = {}
            for record in type_result:
                etype = record["etype"] or "Unknown"
                entity_types[etype] = record["cnt"]

            return {
                "total_nodes": node_count,
                "total_edges": edge_count,
                "entity_types": entity_types,
            }

    def close(self):
        """Close connections."""
        if self._neo4j_driver:
            self._neo4j_driver.close()
        if self._graphiti:
            try:
                _run_async(self._graphiti.close())
            except Exception:
                pass
