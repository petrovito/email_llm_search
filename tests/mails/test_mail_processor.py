import pytest
import asyncio
from email_llm_search.types import Mail, ProcessedMail
from email_llm_search.mails.mail_processor import MailProcessor

# Sample HTML email
HTML_EMAIL = """
<html>
<head>
    <style>
        body { font-family: Arial, sans-serif; }
        .header { background-color: #f0f0f0; padding: 10px; }
        .footer { font-size: 12px; color: gray; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Quarterly Report</h1>
    </div>
    <div class="content">
        <p>Dear Team,</p>
        <p>I'm pleased to share our Q3 results. We've exceeded our targets by 15%.</p>
        <ul>
            <li>Revenue: $2.3M (↑18%)</li>
            <li>New customers: 45 (↑12%)</li>
            <li>Customer retention: 94% (↑3%)</li>
        </ul>
        <p>Let's discuss these results in our next meeting.</p>
        <p>Best regards,<br>John</p>
    </div>
    <div class="footer">
        <p>John Doe | CEO | Acme Inc.</p>
        <p>Email: john@example.com | Phone: (555) 123-4567</p>
        <p><a href="https://www.example.com">www.example.com</a></p>
    </div>
</body>
</html>
"""

# Sample plain text email
PLAIN_TEXT_EMAIL = """
Subject: Re: Project Update

Hi Alice,

Thanks for the update on the project. I think we're making good progress.

> On Wed, Oct 5, 2023 at 2:15 PM Alice <alice@example.com> wrote:
> Hi Bob,
> 
> Just wanted to let you know that I've completed the first phase of the project.
> 
> Best,
> Alice

Let's schedule a meeting to discuss next steps.

Regards,
Bob

-- 
Bob Smith
Senior Developer
bob@example.com
"""

# Short email for basic testing
SHORT_EMAIL = "Hello world"

# Long plain text email for testing chunking
LONG_EMAIL = "a" * 2000  # 2000 'a' characters

@pytest.fixture
def mail_processor():
    """Fixture to create a MailProcessor instance."""
    return MailProcessor()

@pytest.mark.asyncio
async def test_process_short_email(mail_processor):
    """Test processing a short plain text email."""
    mail = Mail(
        uid="1", 
        subject="Test", 
        from_="a@b.com", 
        to="c@d.com", 
        date="2023-01-01", 
        body=SHORT_EMAIL
    )
    
    processed = await mail_processor.process_mail(mail)
    
    assert isinstance(processed, ProcessedMail)
    assert processed.mail_uid == "1"
    assert len(processed.chunks) == 1
    assert processed.chunks[0] == "Hello world"

@pytest.mark.asyncio
async def test_process_long_email(mail_processor):
    """Test processing a long plain text email that should be chunked."""
    mail = Mail(
        uid="2", 
        subject="Long", 
        from_="a@b.com", 
        to="c@d.com", 
        date="2023-01-01", 
        body=LONG_EMAIL
    )
    
    processed = await mail_processor.process_mail(mail)
    
    assert isinstance(processed, ProcessedMail)
    assert processed.mail_uid == "2"
    assert len(processed.chunks) > 1  # Should be split into multiple chunks
    assert sum(len(chunk) for chunk in processed.chunks) <= len(LONG_EMAIL)  # No content should be added

@pytest.mark.asyncio
async def test_process_html_email(mail_processor):
    """Test processing an HTML email with trafilatura extraction."""
    mail = Mail(
        uid="123",
        subject="Quarterly Report",
        from_="john@example.com",
        to="team@example.com",
        date="2023-10-10",
        body=HTML_EMAIL
    )
    
    processed = await mail_processor.process_mail(mail)
    
    assert isinstance(processed, ProcessedMail)
    assert processed.mail_uid == "123"
    assert len(processed.chunks) > 0
    
    # Check that HTML tags were removed
    for chunk in processed.chunks:
        assert "<html>" not in chunk
        assert "<body>" not in chunk
        assert "<div>" not in chunk
    
    # Check that content was preserved - focusing on content that is actually extracted
    all_text = " ".join(processed.chunks)
    assert "Dear Team" in all_text
    assert "Q3 results" in all_text
    assert "Revenue" in all_text
    assert "Best regards" in all_text

@pytest.mark.asyncio
async def test_process_email_with_reply(mail_processor):
    """Test processing an email with reply/forwarded content."""
    mail = Mail(
        uid="456",
        subject="Re: Project Update",
        from_="bob@example.com",
        to="alice@example.com",
        date="2023-10-10",
        body=PLAIN_TEXT_EMAIL
    )
    
    processed = await mail_processor.process_mail(mail)
    
    assert isinstance(processed, ProcessedMail)
    assert processed.mail_uid == "456"
    assert len(processed.chunks) > 0
    
    # Check that reply markers and signatures are handled
    all_text = " ".join(processed.chunks)
    assert "Hi Alice" in all_text
    assert "making good progress" in all_text
    
    # The signature should be removed or at least not prominent
    signature_text = "Bob Smith\nSenior Developer\nbob@example.com"
    # Using a standard assertion instead of pytest.fail()
    assert signature_text not in all_text, "Signature was not properly cleaned from the email" 