import csv
import io
import sys
import xml.etree.ElementTree as ET

import pytest

import xml_to_csv


WP_NS = "http://wordpress.org/export/1.2/"
CONTENT_NS = "http://purl.org/rss/1.0/modules/content/"


def _feed(items):
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss
    xmlns:wp="{WP_NS}"
    xmlns:content="{CONTENT_NS}">
  <channel>
    {items}
  </channel>
</rss>
"""


def _item(
    title="Example Post",
    post_type="post",
    slug="example-post",
    content="<p>Hello</p>",
    date="2026-07-23 10:20:30",
    status="publish",
    link="https://example.test/example-post",
    taxonomy="",
):
    return f"""
<item>
  <title>{title}</title>
  <link>{link}</link>
  <wp:post_type>{post_type}</wp:post_type>
  <wp:post_name>{slug}</wp:post_name>
  <content:encoded><![CDATA[{content}]]></content:encoded>
  <wp:post_date>{date}</wp:post_date>
  <wp:status>{status}</wp:status>
  {taxonomy}
</item>
"""


def _process(path):
    stream = io.StringIO()
    fieldnames = [
        "Title",
        "Slug",
        "Content",
        "Date",
        "URL",
        "Status",
        "Category",
        "Tags",
    ]
    writer = csv.DictWriter(stream, fieldnames=fieldnames)
    writer.writeheader()
    skipped = xml_to_csv.process_xml_file(path, writer)
    stream.seek(0)
    return skipped, list(csv.DictReader(stream))


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("<p>Hello <strong>world</strong></p>", "Hello world"),
        ("[gallery ids='1,2'] Caption [/gallery]", "Caption"),
        ("Keep [Note] and [Update: today]", "Keep [Note] and [Update: today]"),
        ("A&nbsp;&amp; B\n\t C", "A & B C"),
        ("&lt;b&gt;escaped markup&lt;/b&gt;", "<b>escaped markup</b>"),
        ("", ""),
    ],
)
def test_clean_content_strips_markup_shortcodes_and_normalizes_text(raw, expected):
    assert xml_to_csv.clean_content(raw) == expected


def test_process_xml_file_extracts_posts_taxonomy_and_dates(tmp_path):
    path = tmp_path / "export.xml"
    taxonomy = """
      <category domain="category"><![CDATA[News]]></category>
      <category domain="category"><![CDATA[Golf]]></category>
      <category domain="post_tag"><![CDATA[Thailand]]></category>
      <category domain="other"><![CDATA[Ignored]]></category>
    """
    path.write_text(
        _feed(
            _item(
                content="<p>Lead &amp; story</p>[caption]Photo[/caption]",
                taxonomy=taxonomy,
            )
            + _item(title="A Page", post_type="page")
            + _item(
                title="Odd Date",
                slug="odd-date",
                content="Plain",
                date="July 2026",
                link="",
                status="draft",
            )
        ),
        encoding="utf-8",
    )

    skipped, rows = _process(path)

    assert skipped == 0
    assert rows == [
        {
            "Title": "Example Post",
            "Slug": "example-post",
            "Content": "Lead & story Photo",
            "Date": "2026-07-23",
            "URL": "https://example.test/example-post",
            "Status": "publish",
            "Category": "News, Golf",
            "Tags": "Thailand",
        },
        {
            "Title": "Odd Date",
            "Slug": "odd-date",
            "Content": "Plain",
            "Date": "July 2026",
            "URL": "",
            "Status": "draft",
            "Category": "",
            "Tags": "",
        },
    ]


def test_process_xml_file_handles_missing_optional_elements(tmp_path):
    path = tmp_path / "minimal.xml"
    path.write_text(
        _feed(
            """
            <item>
              <wp:post_type>post</wp:post_type>
            </item>
            """
        ),
        encoding="utf-8",
    )

    skipped, rows = _process(path)

    assert skipped == 0
    assert rows == [
        {
            "Title": "",
            "Slug": "",
            "Content": "",
            "Date": "",
            "URL": "",
            "Status": "",
            "Category": "",
            "Tags": "",
        }
    ]


def test_process_xml_file_warns_when_channel_is_missing(tmp_path, capsys):
    path = tmp_path / "no-channel.xml"
    path.write_text("<rss><not-channel /></rss>", encoding="utf-8")

    skipped, rows = _process(path)

    assert skipped == 0
    assert rows == []
    assert "Warning: No channel element found" in capsys.readouterr().out


def test_process_xml_file_counts_a_bad_item_and_continues(tmp_path, capsys):
    path = tmp_path / "export.xml"
    path.write_text(
        _feed(_item(title="First") + _item(title="Second")),
        encoding="utf-8",
    )

    class FlakyWriter:
        def __init__(self):
            self.rows = []
            self.calls = 0

        def writerow(self, row):
            self.calls += 1
            if self.calls == 1:
                raise OSError("disk hiccup")
            self.rows.append(row)

    writer = FlakyWriter()
    skipped = xml_to_csv.process_xml_file(path, writer)

    assert skipped == 1
    assert [row["Title"] for row in writer.rows] == ["Second"]
    assert "skipping item 'First'" in capsys.readouterr().err


def test_process_xml_file_raises_for_malformed_xml(tmp_path):
    path = tmp_path / "broken.xml"
    path.write_text("<rss>", encoding="utf-8")
    with pytest.raises(ET.ParseError):
        _process(path)


def test_main_processes_xml_files_in_sorted_order_and_writes_atomic_csv(
    tmp_path, monkeypatch, capsys
):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "b.XML").write_text(
        _feed(_item(title="Second", slug="second")), encoding="utf-8"
    )
    (input_dir / "a.xml").write_text(
        _feed(_item(title="First", slug="first")), encoding="utf-8"
    )
    (input_dir / "ignore.txt").write_text("not xml", encoding="utf-8")
    output = tmp_path / "result.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "xml_to_csv.py",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output),
        ],
    )

    assert xml_to_csv.main() is None

    with output.open(newline="", encoding="utf-8") as handle:
        rows = list(csv.DictReader(handle))
    assert [row["Title"] for row in rows] == ["First", "Second"]
    assert not list(tmp_path.glob("*.csv.tmp"))
    captured = capsys.readouterr()
    assert "Processing complete. Output saved to" in captured.out
    assert captured.err == ""


@pytest.mark.parametrize("make_input", ["missing", "empty"])
def test_main_exits_loudly_for_missing_directory_or_no_xml(
    tmp_path, monkeypatch, capsys, make_input
):
    input_dir = tmp_path / "input"
    if make_input == "empty":
        input_dir.mkdir()
        (input_dir / "notes.txt").write_text("nothing", encoding="utf-8")
    monkeypatch.setattr(
        sys,
        "argv",
        ["xml_to_csv.py", "--input-dir", str(input_dir)],
    )

    with pytest.raises(SystemExit) as exc:
        xml_to_csv.main()

    assert exc.value.code == 1
    error = capsys.readouterr().err
    expected = "does not exist" if make_input == "missing" else "No XML files found"
    assert expected in error


def test_main_keeps_good_rows_but_returns_failure_when_one_file_is_bad(
    tmp_path, monkeypatch, capsys
):
    input_dir = tmp_path / "input"
    input_dir.mkdir()
    (input_dir / "a-broken.xml").write_text("<rss>", encoding="utf-8")
    (input_dir / "b-good.xml").write_text(
        _feed(_item(title="Good Post")), encoding="utf-8"
    )
    output = tmp_path / "result.csv"
    monkeypatch.setattr(
        sys,
        "argv",
        [
            "xml_to_csv.py",
            "--input-dir",
            str(input_dir),
            "--output-file",
            str(output),
        ],
    )

    with pytest.raises(SystemExit) as exc:
        xml_to_csv.main()

    assert exc.value.code == 1
    with output.open(newline="", encoding="utf-8") as handle:
        assert [row["Title"] for row in csv.DictReader(handle)] == ["Good Post"]
    assert "skipping a-broken.xml" in capsys.readouterr().err
