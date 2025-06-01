import pytest
from datetime import datetime
from unittest.mock import MagicMock, patch, call
import os

from gitwise.features.changelog import (
    ChangelogFeature,
    _get_latest_tag,
    _get_unreleased_commits_as_dicts,
    _categorize_changes,
    _parse_version,
    _format_version,
    _suggest_next_version,
    _create_version_tag,
    _write_version_to_changelog,
    _update_unreleased_changelog_section,
    _setup_commit_hook,
    VersionInfo,
)
from gitwise.core.git_manager import GitManager


@pytest.fixture
def mock_git_manager():
    with patch("gitwise.features.changelog.git_manager", spec=GitManager) as mock_gm:
        mock_gm.get_current_branch.return_value = "feature/test"
        mock_gm.get_default_remote_branch_name.return_value = "main"
        mock_gm.get_commits_between.return_value = []
        mock_gm._run_git_command.return_value = MagicMock(stdout="", returncode=0)
        mock_gm.repo_path = "/fake/repo"
        yield mock_gm


@pytest.fixture
def mock_commit_dict():
    return {
        "hash": "abc123xyz",
        "message": "feat: add new feature",
        "author": "Test Author",
    }


@pytest.fixture
def mock_multiple_commit_dicts():
    return [
        {
            "hash": "abc123xyz",
            "message": "feat: add new feature",
            "author": "Test Author",
        },
        {
            "hash": "def456uvw",
            "message": "fix: resolve critical bug",
            "author": "Test Author",
        },
        {
            "hash": "ghi789rst",
            "message": "docs: update installation guide",
            "author": "Test Author",
        },
    ]


@patch("gitwise.features.changelog.git_manager")
def test_get_latest_tag_found(mock_git_manager):
    mock_git_manager._run_git_command.return_value = MagicMock(
        stdout="v1.1.0\nv1.0.0", returncode=0
    )
    assert _get_latest_tag() == "v1.1.0"


def test_get_latest_tag_not_found(mock_git_manager):
    mock_git_manager._run_git_command.return_value = MagicMock(stdout="", returncode=0)
    assert _get_latest_tag() is None


def test_get_unreleased_commits_as_dicts_with_tag(mock_git_manager, mock_commit_dict):
    with patch("gitwise.features.changelog._get_latest_tag", return_value="v1.0.0"):
        mock_git_manager.get_commits_between.return_value = [mock_commit_dict]
        commits = _get_unreleased_commits_as_dicts()
        assert commits == [mock_commit_dict]
        mock_git_manager.get_commits_between.assert_called_once_with("v1.0.0", "HEAD")


def test_get_unreleased_commits_as_dicts_no_tag(mock_git_manager, mock_commit_dict):
    with patch("gitwise.features.changelog._get_latest_tag", return_value=None):
        mock_git_manager.get_default_remote_branch_name.return_value = "main"
        mock_git_manager.get_merge_base.return_value = "merge_base_hash"
        mock_git_manager.get_commits_between.return_value = [mock_commit_dict]

        commits = _get_unreleased_commits_as_dicts()
        assert commits == [mock_commit_dict]
        mock_git_manager.get_commits_between.assert_called_once_with(
            "merge_base_hash", "HEAD"
        )


def test_categorize_changes(mock_multiple_commit_dicts):
    categories = _categorize_changes(mock_multiple_commit_dicts)
    assert len(categories["Features"]) == 1
    assert categories["Features"][0]["message"] == "feat: add new feature"
    assert len(categories["Bug Fixes"]) == 1
    assert categories["Bug Fixes"][0]["message"] == "fix: resolve critical bug"
    assert len(categories["Documentation"]) == 1
    assert (
        categories["Documentation"][0]["message"] == "docs: update installation guide"
    )


def test_parse_version():
    assert _parse_version("v1.2.3") == VersionInfo(1, 2, 3, None, None)
    assert _parse_version("1.2.3") == VersionInfo(1, 2, 3, None, None)
    assert _parse_version("v1.2.3-alpha.1") == VersionInfo(1, 2, 3, "alpha.1", None)
    assert _parse_version("1.2.3-rc.2+build.100") == VersionInfo(
        1, 2, 3, "rc.2", "build.100"
    )
    assert _parse_version("invalid") is None


def test_format_version():
    assert _format_version(VersionInfo(1, 2, 3)) == "v1.2.3"
    assert _format_version(VersionInfo(1, 2, 3, "alpha.1")) == "v1.2.3-alpha.1"
    assert (
        _format_version(VersionInfo(1, 2, 3, "rc.2", "build.100"))
        == "v1.2.3-rc.2+build.100"
    )


def test_suggest_next_version_no_tags(mock_git_manager, mock_multiple_commit_dicts):
    with patch("gitwise.features.changelog._get_latest_tag", return_value=None):
        version, reason = _suggest_next_version(mock_multiple_commit_dicts)
        assert version == "v0.1.0"
        assert reason == "First release"


def test_suggest_next_version_with_tags(mock_git_manager, mock_multiple_commit_dicts):
    with patch("gitwise.features.changelog._get_latest_tag", return_value="v1.0.0"):
        version, reason = _suggest_next_version(mock_multiple_commit_dicts)
        assert version == "v1.1.0"
        assert "New features added" in reason


def test_suggest_next_version_breaking_change(mock_git_manager):
    commits = [{"message": "feat!: breaking change", "author": "test"}]
    with patch("gitwise.features.changelog._get_latest_tag", return_value="v1.0.0"):
        version, reason = _suggest_next_version(commits)
        assert version == "v2.0.0"
        assert "Breaking changes detected" in reason


def test_suggest_next_version_fix_only(mock_git_manager):
    commits = [{"message": "fix: a bug", "author": "test"}]
    with patch("gitwise.features.changelog._get_latest_tag", return_value="v1.0.0"):
        version, reason = _suggest_next_version(commits)
        assert version == "v1.0.1"
        assert "Bug fixes and improvements" in reason


@patch("gitwise.features.changelog.load_config", MagicMock(return_value={}))
@patch("gitwise.features.changelog.get_llm_backend", MagicMock(return_value="offline"))
@patch("gitwise.features.changelog.ensure_offline_model_ready", MagicMock())
class TestChangelogFeature:

    def test_execute_changelog_new_version(
        self, mock_git_manager, mock_multiple_commit_dicts, tmp_path
    ):
        feature = ChangelogFeature()
        changelog_file = tmp_path / "CHANGELOG.md"

        mock_git_manager._run_git_command.return_value = MagicMock(
            stdout="v1.0.0", returncode=0
        )
        mock_git_manager.get_commits_between.return_value = mock_multiple_commit_dicts

        with patch(
            "gitwise.features.changelog._get_unreleased_commits_as_dicts",
            return_value=mock_multiple_commit_dicts,
        ), patch(
            "gitwise.features.changelog._suggest_next_version",
            return_value=("v1.1.0", "New features"),
        ), patch(
            "gitwise.features.changelog.typer.prompt"
        ) as mock_prompt, patch(
            "gitwise.features.changelog._generate_changelog_llm_content",
            return_value="Generated LLM Content",
        ), patch(
            "gitwise.features.changelog._write_version_to_changelog"
        ) as mock_write, patch(
            "gitwise.features.changelog.typer.confirm", return_value=True
        ), patch(
            "gitwise.features.changelog._create_version_tag"
        ) as mock_create_tag:

            mock_prompt.side_effect = [1, 1]

            feature.execute_changelog(output_file=str(changelog_file))

            mock_write.assert_called_once()
            call_args = mock_write.call_args
            assert call_args[0][0] == str(changelog_file)
            assert call_args[0][1] == "Generated LLM Content"
            assert call_args[0][2] == "v1.1.0"
            mock_create_tag.assert_called_once_with(
                "v1.1.0", commits_for_message=mock_multiple_commit_dicts
            )

    def test_execute_changelog_auto_update(
        self, mock_git_manager, mock_multiple_commit_dicts, tmp_path
    ):
        feature = ChangelogFeature()
        changelog_file = tmp_path / "CHANGELOG.md"
        changelog_file.write_text(
            "# Changelog\n\n## [Unreleased]\n\n## v1.0.0\n- Old stuff"
        )

        with patch(
            "gitwise.features.changelog._update_unreleased_changelog_section"
        ) as mock_update_unreleased:
            feature.execute_changelog(auto_update=True, output_file=str(changelog_file))
            mock_update_unreleased.assert_called_once()

    def test_execute_changelog_no_commits(self, mock_git_manager):
        feature = ChangelogFeature()
        mock_git_manager.get_commits_between.return_value = []
        with patch(
            "gitwise.features.changelog._get_unreleased_commits_as_dicts",
            return_value=[],
        ):
            with patch(
                "gitwise.features.changelog.components.show_warning"
            ) as mock_show_warning:
                feature.execute_changelog()
                mock_show_warning.assert_any_call(
                    "No new commits found to generate changelog entries."
                )

    def test_setup_commit_hook(self, mock_git_manager, tmp_path):
        git_dir = tmp_path / ".git"
        hooks_dir = git_dir / "hooks"
        hooks_dir.mkdir(parents=True, exist_ok=True)
        mock_git_manager.repo_path = str(tmp_path)

        with patch("gitwise.features.changelog.os.makedirs"), patch(
            "builtins.open", MagicMock()
        ) as mock_open, patch("gitwise.features.changelog.os.chmod") as mock_chmod:

            _setup_commit_hook()

            assert mock_open.call_count > 0

            called_path = None
            for call_arg in mock_open.call_args_list:
                if call_arg[0][0] == str(hooks_dir / "pre-commit"):
                    called_path = call_arg[0][0]
                    break
            assert called_path == str(hooks_dir / "pre-commit")

            mock_chmod.assert_called_once_with(called_path, 0o755)


def test_update_unreleased_changelog_section_writes_content(
    mock_git_manager, mock_multiple_commit_dicts, tmp_path
):
    changelog_path = tmp_path / "CHANGELOG.md"
    changelog_path.write_text("# Changelog\n\n## v0.1.0\n- Initial.")

    with patch(
        "gitwise.features.changelog._get_unreleased_commits_as_dicts",
        return_value=mock_multiple_commit_dicts,
    ):
        _update_unreleased_changelog_section(changelog_path=str(changelog_path))

    content = changelog_path.read_text()
    assert "## [Unreleased]" in content
    assert "### Features" in content
    assert "add new feature" in content
    assert "### Bug Fixes" in content
    assert "resolve critical bug" in content
    assert "### Documentation" in content
    assert "update installation guide" in content
    assert "## v0.1.0" in content
