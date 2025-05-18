import pytest
from unittest.mock import patch, MagicMock
from gitwise.features.commit import (
    commit_command,
    group_commits,
    generate_commit_message,
    validate_commit_message
)

@pytest.fixture
def mock_repo():
    with patch('gitwise.features.commit.Repo') as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo

@pytest.fixture
def mock_diff():
    diff = MagicMock()
    diff.a_path = "test.py"
    diff.b_path = "test.py"
    diff.diff = b"@@ -1,1 +1,1 @@\n- old line\n+ new line"
    return diff

def test_commit_command_with_message(mock_repo):
    with patch('gitwise.features.commit.validate_commit_message') as mock_validate:
        mock_validate.return_value = True
        commit_command(message="feat: add new feature")
        mock_repo.index.commit.assert_called_once_with("feat: add new feature")

def test_commit_command_with_group(mock_repo, mock_diff):
    mock_repo.index.diff.return_value = [mock_diff]
    with patch('gitwise.features.commit.group_commits') as mock_group:
        mock_group.return_value = {"Features": ["new feature"]}
        with patch('gitwise.features.commit.generate_commit_message') as mock_gen:
            mock_gen.return_value = "feat: add new feature"
            commit_command(group=True)
            mock_repo.index.commit.assert_called_once_with("feat: add new feature")

def test_group_commits(mock_diff):
    with patch('gitwise.features.commit.analyze_changes') as mock_analyze:
        mock_analyze.return_value = {"type": "feat", "description": "new feature"}
        groups = group_commits([mock_diff])
        assert "Features" in groups
        assert "new feature" in groups["Features"]

def test_generate_commit_message():
    groups = {
        "Features": ["new feature"],
        "Bug Fixes": ["fix bug"]
    }
    message = generate_commit_message(groups)
    assert "feat" in message.lower()
    assert "fix" in message.lower()

def test_validate_commit_message():
    assert validate_commit_message("feat: add new feature")
    assert validate_commit_message("fix: resolve bug")
    assert not validate_commit_message("invalid message")
    assert not validate_commit_message("feat:")  # Missing description

def test_commit_command_with_invalid_message(mock_repo):
    with patch('gitwise.features.commit.validate_commit_message') as mock_validate:
        mock_validate.return_value = False
        with pytest.raises(ValueError):
            commit_command(message="invalid message")

def test_commit_command_with_no_changes(mock_repo):
    mock_repo.index.diff.return_value = []
    with pytest.raises(ValueError):
        commit_command(group=True)

def test_group_commits_with_multiple_changes(mock_diff):
    diff2 = MagicMock()
    diff2.a_path = "test2.py"
    diff2.b_path = "test2.py"
    diff2.diff = b"@@ -1,1 +1,1 @@\n- old line\n+ new line"
    
    with patch('gitwise.features.commit.analyze_changes') as mock_analyze:
        mock_analyze.side_effect = [
            {"type": "feat", "description": "new feature"},
            {"type": "fix", "description": "fix bug"}
        ]
        groups = group_commits([mock_diff, diff2])
        assert "Features" in groups
        assert "Bug Fixes" in groups
        assert len(groups["Features"]) == 1
        assert len(groups["Bug Fixes"]) == 1

def test_generate_commit_message_with_breaking_changes():
    groups = {
        "Features": ["new feature"],
        "Breaking Changes": ["remove old API"]
    }
    message = generate_commit_message(groups)
    assert "feat" in message.lower()
    assert "BREAKING CHANGE" in message
    assert "remove old API" in message

def test_validate_commit_message_with_scope():
    assert validate_commit_message("feat(api): add new endpoint")
    assert validate_commit_message("fix(ui): resolve layout issue")
    assert not validate_commit_message("feat(): missing scope description")

def test_validate_commit_message_with_breaking_changes():
    assert validate_commit_message("feat!: remove deprecated API")
    assert validate_commit_message("feat(api)!: change response format")
    assert not validate_commit_message("feat! invalid message") 