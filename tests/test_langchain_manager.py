import pytest
from email_llm_search.langchain_manager import LangChainManager
from email_llm_search.types import ProcessedMail, SearchResult

@pytest.fixture
def langchain_manager():
    """Fixture to create a LangChainManager instance."""
    return LangChainManager()  # In-memory for testing

def test_add_and_search_documents():
    """Test adding documents and searching."""
    # Create a new instance for this test
    manager = LangChainManager()
    
    # Create some test processed mails
    processed_mails = [
        ProcessedMail(
            mail_uid="1",
            chunks=["This is a test email about machine learning and AI."]
        ),
        ProcessedMail(
            mail_uid="2",
            chunks=["Meeting scheduled for tomorrow at 2 PM to discuss the project."]
        ),
        ProcessedMail(
            mail_uid="3",
            chunks=["The quarterly financial report shows a 15% increase in revenue."]
        )
    ]
    
    # Add to vector store
    manager.add_processed_mails(processed_mails)
    
    # Search for relevant documents
    results = manager.search("machine learning", n_results=2)
    
    # Verify results
    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    assert any("machine learning" in result.text.lower() for result in results)
    assert any(result.mail_uid == "1" for result in results)
    
    # Search for another topic
    results = manager.search("meeting schedule", n_results=2)
    
    # Verify results
    assert len(results) > 0
    assert isinstance(results[0], SearchResult)
    assert any("meeting" in result.text.lower() for result in results)
    assert any(result.mail_uid == "2" for result in results)

def test_empty_search():
    """Test searching with no documents."""
    # Create a new instance for this test
    manager = LangChainManager()
    
    # Search before adding any documents
    results = manager.search("test query", n_results=5)
    
    # Should return empty list
    assert isinstance(results, list)
    assert len(results) == 0

def test_add_empty_processed_mails():
    """Test adding empty processed mails."""
    # Create a new instance for this test
    manager = LangChainManager()
    
    # Add empty list
    manager.add_processed_mails([])
    
    # Add processed mail with empty chunks
    manager.add_processed_mails([
        ProcessedMail(mail_uid="4", chunks=[])
    ])
    
    # Should not raise any errors
    assert True 