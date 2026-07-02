"""
BA Intelligence Toolkit — RTM Generator & Impact Analyzer
Generates a Requirements Traceability Matrix and dependency graph.
"""

import json

import networkx as nx
import plotly.graph_objects as go

from ai_engine import AIEngine, GENERATE_RTM_PROMPT


class RTMGenerator:
    """Generate RTM and dependency graph from extracted requirements."""

    def __init__(self, engine: AIEngine):
        self.engine = engine

    def generate(self, requirements: list[dict]) -> dict:
        """Generate RTM entries and dependency graph.

        Args:
            requirements: list of requirement dicts (from extractor).

        Returns:
            dict with keys: rtm_entries, dependency_graph
        """
        req_json = json.dumps(requirements, ensure_ascii=False, indent=2)
        prompt = GENERATE_RTM_PROMPT.format(requirements=req_json)
        result = self.engine.generate_json(prompt)
        return result

    @staticmethod
    def build_dependency_graph(dependency_edges: list[dict]) -> nx.DiGraph:
        """Build a NetworkX directed graph from dependency edges."""
        G = nx.DiGraph()
        for edge in dependency_edges:
            src = edge.get("source", "")
            tgt = edge.get("target", "")
            if src and tgt:
                G.add_edge(src, tgt, type=edge.get("type", "depends_on"))
        return G

    @staticmethod
    def visualize_graph(G: nx.DiGraph) -> go.Figure:
        """Create an interactive Plotly visualization of the dependency graph."""
        if len(G.nodes) == 0:
            fig = go.Figure()
            fig.update_layout(
                title="No dependencies identified",
                xaxis=dict(visible=False),
                yaxis=dict(visible=False),
                height=400,
            )
            return fig

        # Use spring layout for positioning
        pos = nx.spring_layout(G, k=2, iterations=50)

        # Edge traces
        edge_x, edge_y = [], []
        for u, v in G.edges():
            edge_x += [pos[u][0], pos[v][0], None]
            edge_y += [pos[u][1], pos[v][1], None]

        edge_trace = go.Scatter(
            x=edge_x, y=edge_y,
            line=dict(width=1, color="#888"),
            hoverinfo="none",
            mode="lines",
        )

        # Node traces
        node_x = [pos[node][0] for node in G.nodes()]
        node_y = [pos[node][1] for node in G.nodes()]
        node_text = [str(node) for node in G.nodes()]

        # Color nodes by degree (more connections = different color)
        degrees = dict(G.degree())
        node_colors = [degrees.get(node, 0) for node in G.nodes()]

        node_trace = go.Scatter(
            x=node_x, y=node_y,
            mode="markers+text",
            text=node_text,
            textposition="top center",
            hoverinfo="text",
            marker=dict(
                size=20,
                color=node_colors,
                colorscale="Viridis",
                line=dict(width=2, color="#fff"),
            ),
        )

        fig = go.Figure(data=[edge_trace, node_trace])
        fig.update_layout(
            title="Requirement Dependency Graph",
            showlegend=False,
            xaxis=dict(visible=False),
            yaxis=dict(visible=False),
            height=500,
            margin=dict(l=20, r=20, t=50, b=20),
        )
        return fig

    @staticmethod
    def analyze_impact(
        G: nx.DiGraph, changed_req: str
    ) -> dict:
        """Analyze the impact of changing a requirement.

        Returns all requirements that depend on (directly or transitively)
        the changed requirement. Handles circular dependencies gracefully.
        """
        if changed_req not in G:
            return {"changed": changed_req, "impacted": [], "total_impacted": 0}

        # Check for cycles — if the graph is not a DAG, fall back to
        # shortest_path-based traversal to avoid infinite loops
        if not nx.is_directed_acyclic_graph(G):
            # Use BFS traversal instead of descendants/ancestors
            impacted = set()
            queue = [changed_req]
            while queue:
                node = queue.pop(0)
                for successor in G.successors(node):
                    if successor not in impacted and successor != changed_req:
                        impacted.add(successor)
                        queue.append(successor)

            upstream = set()
            queue = [changed_req]
            while queue:
                node = queue.pop(0)
                for predecessor in G.predecessors(node):
                    if predecessor not in upstream and predecessor != changed_req:
                        upstream.add(predecessor)
                        queue.append(predecessor)

            impacted = list(impacted)
            upstream = list(upstream)
        else:
            # Safe to use descendants/ancestors on a DAG
            impacted = list(nx.descendants(G, changed_req))
            upstream = list(nx.ancestors(G, changed_req))

        return {
            "changed": changed_req,
            "impacted_downstream": impacted,
            "impacted_upstream": upstream,
            "total_impacted": len(impacted) + len(upstream),
        }
