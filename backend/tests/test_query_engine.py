"""Tests for QueryEngine query rewriting and retrieval."""

from unittest.mock import MagicMock, patch
import pytest
from scribo.rag.query_engine import QueryEngine


@patch("scribo.rag.query_engine.settings")
@patch("scribo.rag.query_engine.VectorStore")
@patch("scribo.rag.query_engine.Ranker")
@patch("scribo.rag.query_engine.genai.Client")
def test_rewrite_query_success(mock_client_cls, mock_ranker_cls, mock_vs_cls, mock_settings, tmp_path):
    mock_settings.GEMINI_API_KEY = "test-key"
    mock_settings.DEFAULT_MODEL = "gemini-2.5-flash"
    mock_settings.COURSES_DATA_DIR = tmp_path

    mock_client = MagicMock()
    mock_response = MagicMock()
    mock_response.text = "Digital Predistortion Carrier Trapping RF Power Amplifier"
    mock_client.models.generate_content.return_value = mock_response
    mock_client_cls.return_value = mock_client

    engine = QueryEngine()
    rewritten = engine.rewrite_query(
        question="What is DPD?",
        history=[{"role": "user", "content": "Tell me about RF PAs"}]
    )

    assert rewritten == "Digital Predistortion Carrier Trapping RF Power Amplifier"
    mock_client.models.generate_content.assert_called_once()


@patch("scribo.rag.query_engine.settings")
@patch("scribo.rag.query_engine.VectorStore")
@patch("scribo.rag.query_engine.Ranker")
@patch("scribo.rag.query_engine.genai.Client")
def test_rewrite_query_fallback_on_error(mock_client_cls, mock_ranker_cls, mock_vs_cls, mock_settings, tmp_path):
    mock_settings.GEMINI_API_KEY = "test-key"
    mock_settings.DEFAULT_MODEL = "gemini-2.5-flash"
    mock_settings.COURSES_DATA_DIR = tmp_path

    mock_client = MagicMock()
    mock_client.models.generate_content.side_effect = Exception("API error")
    mock_client_cls.return_value = mock_client

    engine = QueryEngine()
    rewritten = engine.rewrite_query("What is DPD?")
    assert rewritten == "What is DPD?"


@patch("scribo.rag.query_engine.settings")
@patch("scribo.rag.query_engine.VectorStore")
@patch("scribo.rag.query_engine.Ranker")
@patch("scribo.rag.query_engine.genai.Client")
def test_query_with_rewriting_disabled(mock_client_cls, mock_ranker_cls, mock_vs_cls, mock_settings, tmp_path):
    mock_settings.GEMINI_API_KEY = "test-key"
    mock_settings.DEFAULT_MODEL = "gemini-2.5-flash"
    mock_settings.COURSES_DATA_DIR = tmp_path

    mock_vs = MagicMock()
    mock_vs.search.return_value = [
        {"id": "c1", "text": "Passage text", "metadata": {"course_id": "ee381", "lecture_id": "lec01"}}
    ]
    mock_vs_cls.return_value = mock_vs

    mock_ranker = MagicMock()
    mock_ranker.rerank.return_value = [
        {"id": "c1", "text": "Passage text", "meta": {"course_id": "ee381", "lecture_id": "lec01"}}
    ]
    mock_ranker_cls.return_value = mock_ranker

    mock_client = MagicMock()
    mock_ans_response = MagicMock()
    mock_ans_response.text = "Answer content"
    mock_client.models.generate_content.return_value = mock_ans_response
    mock_client_cls.return_value = mock_client

    engine = QueryEngine()
    result = engine.query(
        question="What is DPD?",
        course_id="ee381",
        enable_query_rewriting=False
    )

    assert result["answer"] == "Answer content"
    assert result["rewritten_query"] is None
    assert result["query_rewriting_enabled"] is False
    # Verify vector store was called with original raw question
    mock_vs.search.assert_called_once_with("What is DPD?", course_id="ee381", top_k=15)
