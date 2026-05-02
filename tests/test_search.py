"""Tests for ddgr_skill.search module."""

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from ddgr_skill.exceptions import DdgrNotFoundError, DdgrSearchError
from ddgr_skill.search import (
     _build_ddgr_command,
     find_ddgr_binary,
     search,
)


class TestFindDdgrBinary:
    def test_finds_ddgr_binary(self):
        with patch("ddgr_skill.search.which", return_value="/usr/local/bin/ddgr"):
            result = find_ddgr_binary()
            assert result == Path("/usr/local/bin/ddgr")

    def test_raises_when_not_found(self):
        with patch("ddgr_skill.search.which", return_value=None):
            try:
                find_ddgr_binary()
                raise AssertionError("Expected DdgrNotFoundError")
            except DdgrNotFoundError as exc:
                assert "ddgr not found" in str(exc)


class TestBuildDdgrCommand:
    def test_minimal_command(self):
        cmd = _build_ddgr_command(Path("/usr/bin/ddgr"), "python", 10)
        assert cmd == ["/usr/bin/ddgr", "--json", "--np", "--num", "10", "python"]

    def test_command_with_all_options(self):
        cmd = _build_ddgr_command(
            Path("/usr/bin/ddgr"),
            "python",
            5,
            time_span="w",
            site="github.com",
            region="wt-wt",
            expand_urls=True,
         )
        assert cmd == [
            "/usr/bin/ddgr",
            "--json",
            "--np",
            "--num",
            "5",
            "-t",
            "w",
            "-w",
            "github.com",
            "-r",
            "wt-wt",
            "-x",
            "python",
         ]

    def test_command_without_optional_flags(self):
        cmd = _build_ddgr_command(Path("/usr/bin/ddgr"), "test", 3)
        assert "-t" not in cmd
        assert "-w" not in cmd
        assert "-r" not in cmd
        assert "-x" not in cmd


class TestSearch:
    def _mock_process_result(self, stdout_data, returncode=0, stderr=""):
        mock_result = MagicMock()
        mock_result.stdout = json.dumps(stdout_data) if isinstance(stdout_data, list) else stdout_data
        mock_result.stderr = stderr
        mock_result.returncode = returncode
        return mock_result

    def test_search_success(self, sample_search_results):
        mock_result = self._mock_process_result(sample_search_results)
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result),
         ):
            results = search("python")
            assert results == sample_search_results

    def test_search_empty_results(self):
        mock_result = self._mock_process_result([])
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result),
         ):
            results = search("nonexistent query xyz")
            assert results == []

    def test_search_invalid_json(self):
        mock_result = self._mock_process_result("not json", returncode=0)
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result),
         ):
            try:
                search("test")
                raise AssertionError("Expected DdgrSearchError")
            except DdgrSearchError as exc:
                assert "invalid JSON" in str(exc)

    def test_search_subprocess_failure(self):
        mock_result = self._mock_process_result("", returncode=1, stderr="Error: query failed")
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result),
         ):
            try:
                search("test")
                raise AssertionError("Expected DdgrSearchError")
            except DdgrSearchError as exc:
                assert "exit code 1" in str(exc)

    def test_search_num_clamped_to_25(self):
        mock_result = self._mock_process_result([])
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
         ):
            search("test", num_results=100)
            call_args = mock_run.call_args[0][0]
            assert "--num" in call_args
            num_index = call_args.index("--num")
            assert call_args[num_index + 1] == "25"

    def test_search_invalid_time_span(self):
        with patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"):
            try:
                search("test", time_span="x")
                raise AssertionError("Expected ValueError")
            except ValueError as exc:
                assert "Invalid time_span" in str(exc)

    def test_search_with_time_span(self):
        mock_result = self._mock_process_result([])
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
         ):
            search("test", time_span="d")
            call_args = mock_run.call_args[0][0]
            assert "-t" in call_args
            assert call_args[call_args.index("-t") + 1] == "d"

    def test_search_with_site(self):
        mock_result = self._mock_process_result([])
        with (
            patch("ddgr_skill.search.which", return_value="/usr/bin/ddgr"),
            patch("subprocess.run", return_value=mock_result) as mock_run,
         ):
            search("test", site="github.com")
            call_args = mock_run.call_args[0][0]
            assert "-w" in call_args
            assert call_args[call_args.index("-w") + 1] == "github.com"

    def test_search_custom_ddgr_path(self):
        mock_result = self._mock_process_result([])
        with patch("subprocess.run", return_value=mock_result) as mock_run:
            search("test", ddgr_path=Path("/custom/ddgr"))
            call_args = mock_run.call_args[0][0]
            assert call_args[0] == "/custom/ddgr"
