"""Graph pagination utility.

Originally for Zep Cloud's cursor-based pagination.
Now updated to use GraphitiClient adapter.

These functions are kept for backward compatibility but callers
should migrate to using GraphitiClient directly.
"""

from __future__ import annotations

from typing import Any

from .logger import get_logger

logger = get_logger('mirofish.zep_paging')

_DEFAULT_PAGE_SIZE = 100
_MAX_NODES = 2000


def fetch_all_nodes(
    graphiti_client,
    graph_id: str,
    page_size: int = _DEFAULT_PAGE_SIZE,
    max_items: int = _MAX_NODES,
    **kwargs,
) -> list[Any]:
    """Fetch all graph nodes using GraphitiClient pagination.

    Args:
        graphiti_client: A GraphitiClient instance.
        graph_id: The graph namespace ID.
        page_size: Number of nodes per page.
        max_items: Maximum total nodes to fetch.

    Returns:
        List of GraphNode objects.
    """
    all_nodes: list[Any] = []
    cursor: str | None = None

    while True:
        batch = graphiti_client.get_nodes_by_graph(graph_id, limit=page_size, cursor=cursor)
        if not batch:
            break

        all_nodes.extend(batch)
        if len(all_nodes) >= max_items:
            all_nodes = all_nodes[:max_items]
            logger.warning(f"Node count reached limit ({max_items}), stopping pagination for graph {graph_id}")
            break
        if len(batch) < page_size:
            break

        cursor = batch[-1].uuid
        if cursor is None:
            logger.warning(f"Node missing uuid field, stopping pagination at {len(all_nodes)} nodes")
            break

    return all_nodes


def fetch_all_edges(
    graphiti_client,
    graph_id: str,
    page_size: int = _DEFAULT_PAGE_SIZE,
    **kwargs,
) -> list[Any]:
    """Fetch all graph edges using GraphitiClient pagination.

    Args:
        graphiti_client: A GraphitiClient instance.
        graph_id: The graph namespace ID.
        page_size: Number of edges per page.

    Returns:
        List of GraphEdge objects.
    """
    all_edges: list[Any] = []
    cursor: str | None = None

    while True:
        batch = graphiti_client.get_edges_by_graph(graph_id, limit=page_size, cursor=cursor)
        if not batch:
            break

        all_edges.extend(batch)
        if len(batch) < page_size:
            break

        cursor = batch[-1].uuid
        if cursor is None:
            logger.warning(f"Edge missing uuid field, stopping pagination at {len(all_edges)} edges")
            break

    return all_edges
