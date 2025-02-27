import pytest
from email_llm_search.mail_processor import MailProcessor
from email_llm_search.types import Mail

def test_process_mail():
    """Test email processing into chunks."""
    processor = MailProcessor()

    # Short email
    mail = Mail(uid="1", subject="Test", from_="a@b.com", to="c@d.com", date="2023-01-01", body="Hello world")
    processed = processor.process_mail(mail)
    assert len(processed) == 1
    assert processed[0].text == "Hello world"

    # Long email
    long_body = "a" * 1000
    mail = Mail(uid="2", subject="Long", from_="a@b.com", to="c@d.com", date="2023-01-01", body=long_body)
    processed = processor.process_mail(mail)
    assert len(processed) == 2
    assert processed[0].text == "a" * 500
    assert processed[1].text == "a" * 500