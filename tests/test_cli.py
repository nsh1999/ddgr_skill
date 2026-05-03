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
            patch("ddgr_skill.output.format_search_results_json", return_value="[]"),
            patch("sys.stdout"),
         ):
            result = main(["search", "test"])
            assert result == 0

    def test_fetch_with_output_file(self):
        mock_result = {"title": "Page", "url": "https://example.com", "content": "Body"}
        with (
            patch("ddgr_skill.fetcher.fetch_as_markdown", return_value=mock_result),
            patch("ddgr_skill.output.save_to_file") as mock_save,
         ):
            main(["fetch", "https://example.com", "--output", "/tmp/test.md"])
            mock_save.assert_called_once()

    def test_lookup_success(self):
        mock_search = [{"title": "Page", "url": "https://example.com", "abstract": "Abs"}]
        mock_lookup = [{"title": "Page", "url": "https://example.com", "content": "Body"}]
        with (
            patch("ddgr_skill.cli.search", return_value=mock_search),
            patch("ddgr_skill.fetcher.fetch_with_fallback", return_value=(mock_lookup, False)),
            patch("ddgr_skill.output.format_lookup_results_markdown", return_value="combined"),
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

    def test_search_fetch_flag(self):
        parser = build_parser()
        args = parser.parse_args(["search", "python", "--fetch"])
        assert args.command == "search"
        assert args.query == "python"
        assert args.fetch is True

    def test_search_fetch_with_format(self):
        parser = build_parser()
        args = parser.parse_args(
             ["search", "python", "--fetch", "--format", "markdown"]
          )
        assert args.fetch is True
        assert args.format == "markdown"

    def test_search_fetch_returns_fetched_content(self):
        mock_search = [{"title": "Page", "url": "https://example.com", "abstract": "Abs"}]
        mock_fetched = [{"title": "Page", "url": "https://example.com", "content": "Body"}]
        with (
            patch("ddgr_skill.cli.search", return_value=mock_search),
            patch(
                "ddgr_skill.fetcher.fetch_with_fallback",
                return_value=(mock_fetched, False),
            ),
            patch(
                "ddgr_skill.output.format_lookup_results_json",
                return_value="fetched_json",
            ),
            patch("sys.stdout"),
        ):
            result = main(["search", "test", "--fetch"])
            assert result == 0

    def test_search_fetch_no_results(self):
        with (
            patch("ddgr_skill.cli.search", return_value=[]),
            patch("sys.stdout") as mock_stdout,
          ):
            result = main(["search", "test", "--fetch"])
            assert result == 0
            mock_stdout.write.assert_called()


    def test_lookup_all_failed_shows_abstracts(self):
        """When all fetches fail, shows search abstracts as fallback."""
        mock_search = [{"title": "Page", "url": "https://example.com", "abstract": "Abs"}]
        with (
            patch("ddgr_skill.cli.search", return_value=mock_search),
            patch("ddgr_skill.fetcher.fetch_with_fallback", return_value=([], True)),
            patch("sys.stdout") as mock_stdout,
        ):
            main(["lookup", "test"])
            assert mock_stdout.write.call_count >= 2

    def test_lookup_searches_extra_results(self):
        """Lookup searches 3x the target count for fallback URLs."""
        with patch("ddgr_skill.cli.search") as mock_search:
            with patch(
                "ddgr_skill.fetcher.fetch_with_fallback",
                return_value=(
                    [{"title": "P", "url": "https://a.com", "content": "C" * 200}],
                    False,
                ),
            ):
                with patch(
                    "ddgr_skill.output.format_lookup_results_markdown",
                    return_value="out",
                ):
                    with patch("sys.stdout"):
                        main(["lookup", "test", "--num", "5"])
                        mock_search.assert_called_once()
                        assert mock_search.call_args[1]["num_results"] == 15


    def test_lookup_all_failed_json_format(self):
        """When all fetches fail with json format, still shows abstracts."""
        mock_search = [{"title": "Page", "url": "https://example.com", "abstract": "Abs"}]
        with (
            patch("ddgr_skill.cli.search", return_value=mock_search),
            patch("ddgr_skill.fetcher.fetch_with_fallback", return_value=([], True)),
            patch("sys.stdout") as mock_stdout,
        ):
            main(["lookup", "test", "--format", "json"])
            assert mock_stdout.write.call_count >= 2
