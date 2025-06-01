import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch

from gitwise.features.changelog import (categorize_changes, changelog_command,
                                        commit_hook, generate_changelog_entry,
                                        generate_release_notes,
                                        get_commits_between_tags,
                                        get_repository_info,
                                        get_unreleased_changes,
                                        get_version_tags, setup_commit_hook,
                                        update_changelog,
                                        update_unreleased_changelog)


@pytest.fixture
def mock_repo():
    with patch("gitwise.features.changelog.Repo") as mock:
        repo = MagicMock()
        mock.return_value = repo
        yield repo


@pytest.fixture
def mock_commit():
    commit = MagicMock()
    commit.message = "feat: add new feature"
    commit.hexsha = "abc123"
    commit.committed_datetime = datetime.now()
    return commit


def test_get_version_tags(mock_repo):
    mock_repo.tags = [
        MagicMock(name="v1.0.0"),
        MagicMock(name="v1.1.0"),
        MagicMock(name="v2.0.0"),
    ]
    tags = get_version_tags()
    assert len(tags) == 3
    assert tags[0].name == "v1.0.0"


def test_get_commits_between_tags(mock_repo, mock_commit):
    mock_repo.iter_commits.return_value = [mock_commit]
    commits = get_commits_between_tags("v1.0.0", "v1.1.0")
    assert len(commits) == 1
    assert commits[0].message == "feat: add new feature"


def test_categorize_changes(mock_commit):
    commits = [mock_commit]
    categories = categorize_changes(commits)
    assert "Features" in categories
    assert len(categories["Features"]) == 1


def test_generate_changelog_entry():
    version = "v1.0.0"
    commits = [
        MagicMock(message="feat: new feature"),
        MagicMock(message="fix: bug fix"),
        MagicMock(message="docs: update docs"),
    ]
    entry = generate_changelog_entry(version, commits)
    assert "## [1.0.0]" in entry
    assert "### Features" in entry
    assert "### Bug Fixes" in entry
    assert "### Documentation" in entry


def test_get_repository_info(mock_repo):
    mock_repo.remotes.origin.url = "https://github.com/user/repo.git"
    info = get_repository_info()
    assert info["url"] == "https://github.com/user/repo.git"
    assert info["name"] == "repo"


def test_generate_release_notes():
    commits = [
        MagicMock(message="feat: new feature"),
        MagicMock(message="fix: bug fix"),
    ]
    notes = generate_release_notes(commits, {"name": "repo"})
    assert "New Features" in notes
    assert "Bug Fixes" in notes


def test_update_changelog(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## [Unreleased]\n")

    version = "v1.0.0"
    commits = [MagicMock(message="feat: new feature")]

    update_changelog(version, commits)
    content = changelog_path.read_text()
    assert "## [1.0.0]" in content
    assert "## [Unreleased]" in content


def test_get_unreleased_changes(mock_repo, mock_commit):
    mock_repo.iter_commits.return_value = [mock_commit]
    changes = get_unreleased_changes()
    assert len(changes) == 1
    assert changes[0].message == "feat: add new feature"


def test_update_unreleased_changelog(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## [Unreleased]\n")

    commits = [MagicMock(message="feat: new feature")]
    update_unreleased_changelog(commits)

    content = changelog_path.read_text()
    assert "### Features" in content
    assert "new feature" in content


def test_commit_hook(tmp_path):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## [Unreleased]\n")

    with patch("gitwise.features.changelog.get_unreleased_changes") as mock:
        mock.return_value = [MagicMock(message="feat: new feature")]
        commit_hook()

    content = changelog_path.read_text()
    assert "### Features" in content


def test_setup_commit_hook(tmp_path):
    git_dir = tmp_path / ".git"
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(parents=True)

    with patch("gitwise.features.changelog.Repo") as mock:
        mock.return_value.git_dir = str(git_dir)
        setup_commit_hook()

    pre_commit = hooks_dir / "pre-commit"
    assert pre_commit.exists()
    assert "gitwise changelog --auto-update" in pre_commit.read_text()


def test_changelog_command_with_version(mock_repo):
    with patch("gitwise.features.changelog.generate_changelog_entry") as mock:
        mock.return_value = "## [1.0.0]"
        changelog_command(version="v1.0.0")
        mock.assert_called_once()


def test_changelog_command_without_version(mock_repo):
    with patch("gitwise.features.changelog.get_version_tags") as mock:
        mock.return_value = [MagicMock(name="v1.0.0")]
        changelog_command()
        mock.assert_called_once()


def test_changelog_command_with_auto_update(mock_repo):
    with patch("gitwise.features.changelog.update_unreleased_changelog") as mock:
        changelog_command(auto_update=True)
        mock.assert_called_once()


def test_changelog_command_with_setup_hook(mock_repo):
    with patch("gitwise.features.changelog.setup_commit_hook") as mock:
        changelog_command(setup_hook=True)
        mock.assert_called_once()
