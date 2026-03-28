"""LangGraph pipeline graph definition for the podcast processing workflow.

Builds and compiles the directed graph connecting moment detection,
content generation, and quality checking nodes.
"""

import structlog
from langgraph.graph import END, START, StateGraph

from api.agent.nodes.content_factory import content_factory
from api.agent.nodes.moment_detector import moment_detector
from api.agent.nodes.quality_checker import quality_checker
from api.agent.state import PodcastState

log = structlog.get_logger(__name__)


def build_podcast_graph() -> object:
    """Construct and compile the full podcast processing LangGraph pipeline.

    Graph structure:
        START → moment_detector → content_factory → quality_checker → END

    Returns:
        A compiled LangGraph graph ready for invocation via .ainvoke().
    """
    graph: StateGraph = StateGraph(PodcastState)

    graph.add_node("moment_detector", moment_detector)
    graph.add_node("content_factory", content_factory)
    graph.add_node("quality_checker", quality_checker)

    graph.add_edge(START, "moment_detector")
    graph.add_edge("moment_detector", "content_factory")
    graph.add_edge("content_factory", "quality_checker")
    graph.add_edge("quality_checker", END)

    return graph.compile()


# Compiled graph singleton — instantiated once at module import
podcast_graph = build_podcast_graph()
