import html
import re

CODE_BLOCK = re.compile(r"```(\w*)\n(.*?)```", re.S)
INLINE_CODE = re.compile(r"`([^`\n]+)`")
BOLD = re.compile(r"\*\*(.+?)\*\*", re.S)
ITALIC = re.compile(r"(?<!\*)\*(?!\s)(.+?)(?<!\s)\*(?!\*)", re.S)
HEADING = re.compile(r"^#{1,6}\s*(.+)$", re.M)


def to_html(text: str) -> str:
    t = html.escape(text, quote=False)
    t = CODE_BLOCK.sub(
        lambda m: f'<pre><code class="language-{m.group(1) or "text"}">{m.group(2).rstrip()}</code></pre>',
        t)
    t = INLINE_CODE.sub(r"<code>\1</code>", t)
    t = HEADING.sub(r"<b>\1</b>", t)
    t = BOLD.sub(r"<b>\1</b>", t)
    t = ITALIC.sub(r"<i>\1</i>", t)
    return t


def split_html(text: str, limit: int = 3800) -> list[str]:
    parts: list[str] = []
    buf = ""
    for block in text.split("\n\n"):
        if len(buf) + len(block) + 2 > limit and buf:
            parts.append(buf)
            buf = block
        else:
            buf = f"{buf}\n\n{block}" if buf else block
    if buf:
        parts.append(buf)
    return parts