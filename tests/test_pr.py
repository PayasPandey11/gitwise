from unittest.mock import MagicMock, patch

import pytest

from gitwise.features.pr import (generate_pr_description, generate_pr_title,
                                 get_base_branch, get_current_branch,
                                 pr_command, validate_branch_name)


@pytest.fixture
def mock_repo():
    with patch("gitwise.features.pr.Repo") as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_commit():
    commit = MagicMock()
    commit.message = "feat: add new feature"
    commit.hexsha = "abc123"
    return commit


def test_pr_command_with_title(mock_repo):
    with patch("gitwise.features.pr.create_pull_request") as mock_create:
        mock_create.return_value = {"html_url": "https://github.com/user/repo/pull/1"}
        pr_command(title="Add new feature")
        mock_create.assert_called_once()


def test_pr_command_without_title(mock_repo, mock_commit):
    mock_repo.iter_commits.return_value = [mock_commit]
    with patch("gitwise.features.pr.generate_pr_title") as mock_gen_title:
        mock_gen_title.return_value = "Add new feature"
        with patch("gitwise.features.pr.create_pull_request") as mock_create:
            mock_create.return_value = {
                "html_url": "https://github.com/user/repo/pull/1"
            }
            pr_command()
            mock_create.assert_called_once()


def test_generate_pr_title(mock_commit):
    with patch("gitwise.features.pr.get_commits_since_base") as mock_get:
        mock_get.return_value = [mock_commit]
        title = generate_pr_title()
        assert "Add new feature" in title


def test_generate_pr_description(mock_commit):
    with patch("gitwise.features.pr.get_commits_since_base") as mock_get:
        mock_get.return_value = [mock_commit]
        description = generate_pr_description()
        assert "## Changes" in description
        assert "feat: add new feature" in description


def test_validate_branch_name():
    assert validate_branch_name("feature/new-feature")
    assert validate_branch_name("fix/bug-fix")
    assert not validate_branch_name("invalid branch name")
    assert not validate_branch_name("main")  # Protected branch


def test_get_current_branch(mock_repo):
    mock_repo.active_branch.name = "feature/new-feature"
    branch = get_current_branch()
    assert branch == "feature/new-feature"


def test_get_base_branch(mock_repo):
    mock_repo.remotes.origin.refs.main.name = "main"
    base = get_base_branch()
    assert base == "main"


def test_pr_command_with_invalid_branch(mock_repo):
    mock_repo.active_branch.name = "main"
    with pytest.raises(ValueError):
        pr_command()


def test_pr_command_with_no_commits(mock_repo):
    mock_repo.iter_commits.return_value = []
    with pytest.raises(ValueError):
        pr_command()


def test_generate_pr_title_with_multiple_commits(mock_commit):
    commit2 = MagicMock()
    commit2.message = "fix: resolve bug"

    with patch("gitwise.features.pr.get_commits_since_base") as mock_get:
        mock_get.return_value = [mock_commit, commit2]
        title = generate_pr_title()
        assert "Add new feature" in title
        assert "resolve bug" in title


def test_generate_pr_description_with_breaking_changes(mock_commit):
    commit = MagicMock()
    commit.message = "feat!: remove deprecated API"

    with patch("gitwise.features.pr.get_commits_since_base") as mock_get:
        mock_get.return_value = [commit]
        description = generate_pr_description()
        assert "## Breaking Changes" in description
        assert "remove deprecated API" in description


def test_pr_command_with_custom_base(mock_repo, mock_commit):
    mock_repo.iter_commits.return_value = [mock_commit]
    with patch("gitwise.features.pr.create_pull_request") as mock_create:
        mock_create.return_value = {"html_url": "https://github.com/user/repo/pull/1"}
        pr_command(base="develop")
        mock_create.assert_called_once()


def test_pr_command_with_draft(mock_repo, mock_commit):
    mock_repo.iter_commits.return_value = [mock_commit]
    with patch("gitwise.features.pr.create_pull_request") as mock_create:
        mock_create.return_value = {"html_url": "https://github.com/user/repo/pull/1"}
        pr_command(draft=True)
        mock_create.assert_called_once()
