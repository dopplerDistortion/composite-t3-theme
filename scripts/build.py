"""Build dist/composite.json from src/theme.json and src/composite.css.

T3 Code holds at most 50,000 characters of theme CSS, so the CSS is minified:
comments and meaningless whitespace go; strings (the icons' data: URIs) and the
space of a descendant selector (`.composer-tiptap :focus-visible`) stay.

    python3 -I scripts/build.py          # write dist/composite.json
    python3 -I scripts/build.py --check  # fail if dist is out of date
"""
import json
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
LIMIT = 50_000
CREDIT = "/*Icons: Streamline Sharp Duo Free, CC BY 4.0*/"


def split_strings(css):
    out, buf, i, n = [], [], 0, len(css)
    while i < n:
        c = css[i]
        if c in "\"'":
            if buf:
                out.append((False, "".join(buf)))
                buf = []
            j = i + 1
            while j < n and css[j] != c:
                j += 2 if css[j] == "\\" else 1
            out.append((True, css[i:j + 1]))
            i = j + 1
        else:
            buf.append(c)
            i += 1
    if buf:
        out.append((False, "".join(buf)))
    return out


def minify_code(s):
    s = re.sub(r"\s+", " ", s)
    s = re.sub(r"\s*([{};,>])\s*", r"\1", s)  # never meaningful around these
    s = re.sub(r":\s+", ":", s)  # a space after ':' only appears in declarations
    s = re.sub(r"\s*!important", "!important", s)
    return s.replace(";}", "}")


def minify(css):
    # Comments first: they hold apostrophes that would read as strings.
    css = re.sub(r"/\*.*?\*/", "", css, flags=re.S)
    code = "".join(t if is_str else minify_code(t) for is_str, t in split_strings(css))
    return CREDIT + code.strip()


def main():
    theme = json.loads((ROOT / "src/theme.json").read_text())
    theme["css"] = minify((ROOT / "src/composite.css").read_text())
    if len(theme["css"]) > LIMIT:
        raise SystemExit(f"theme CSS is {len(theme['css'])} characters; T3 Code's limit is {LIMIT}")
    out = json.dumps(theme, indent=2) + "\n"
    dist = ROOT / "dist/composite.json"
    if "--check" in sys.argv:
        if not dist.exists() or dist.read_text() != out:
            raise SystemExit("dist/composite.json is out of date: run scripts/build.py")
        print("dist is up to date")
        return
    dist.write_text(out)
    print(f"dist/composite.json: {len(theme['css'])} of {LIMIT} characters")


if __name__ == "__main__":
    main()
