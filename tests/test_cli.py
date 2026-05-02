"""Tests for ddgr_skill.cli module."""

from unittest.mock import MagicMock, patch

from ddgr_skill.cli import build_parser, main


class TestBuildParser:
    def test_parser_has_subcommands(self):
        parser = build_parser()
        assert parser._subparsers is not None

    def test_search_args_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["search", "python", "--num", "5"])
        assert args.command == "search"
        assert args.query == "python"
        assert args.num == 5

    def test_fetch_args_parsed(self):
        parser = build_parser()
        args = parser.parse_args(["fetch", "https://example.com", "--format", "json"])
        assert args.command == "fetch"
        assert args.url == "https://example.com"
        assert args.format == "json"

    def test_lookup_args_parsed(self):
        parser = build_parser()
        args = parser.parse_args(
            ["lookup", "python", "--num", "3", "--format", "json"]
         )
        assert args.command == "lookup"
        assert args.query == "python"
        assert args.num == 3
        assert args.format == "json"

    def test_no_command_shows_help(self):
        parser = build_parser()
        args = parser.parse_args([])
        assert not hasattr(args, "handler")


class TestMain:
    def test_no_command_returns_0(self):
        with patch("sys.stdout") as mock_stdout:
            result = main([])
            assert result == 0

    def test_search_error_returns_1(self):
        from ddgr_skill.exceptions import DdgrNotFoundError

        with (
            patch("ddgr_skill.cli.search", side_effect=DdgrNotFoundError("no ddgr")),
            patch("sys.stderr"),
         ):
            result = main(["search", "test"])
            assert result == 1

    def test_search_success_returns_0(self):
        with (
            patch("ddgr_skill.cli.search", return_value=[]),
            patch("ddgr_skill.cli.format_search_results_json", return_value="[]"),
            patch("sys.stdout"),
         ):
            result = main(["search", "test"])
            assert result == 0

    def test_fetch_with_output_file(self):
        mock_result = {"title": "Page", "url": "https://example.com", "content": "Body"}
        with (
            patch("ddgr_skill.cli.fetch_as_markdown", return_value=mock_result),
            patch("ddgr_skill.cli.save_to_file") as mock_save,
         ):
            main(["fetch", "https://example.com", "--output", "/tmp/test.md"])
            mock_save.assert_called_once()

    def test_lookup_success(self):
        mock_search = [{"title": "Page", "url": "https://example.com", "abstract": "Abs"}]
        mock_lookup = [{"title": "Page", "url": "https://example.com", "content": "Body"}]
        with (
            patch("ddgr_skill.cli.search", return_value=mock_search),
            patch("ddgr_skill.cli.fetch_urls_concurrent", return_value=mock_lookup),
            patch("ddgr_skill.cli.format_lookup_results_markdown", return_value="combined"),
            patch("sys.stdout"),
         ):
            result = main(["lookup", "test"])
            assert result == 0

    def test_lookup_no_results(self):
        with (
            patch("ddgr_skill.cli.search", return_value=[]),
            patch("sys.stdout") as mock_stdout,
         ):
            main(["lookup", "test"])
            mock_stdout.write.assert_called()
