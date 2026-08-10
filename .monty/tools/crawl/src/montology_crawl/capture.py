"""Captured components: the site's own sections, faithfully, as React.

THE REFINED RULING. The old one said "the agent writes the React, not a
converter" — true for DESIGN, and it stays true: idiomatic, tokenized
components (status `built`) are the agent's work. But a brand book needs
the evidence renderable NOW, and a faithful capture is a mechanical fact,
not a design decision. So the library holds two tiers:

  * **captured** — this converter's output: the section as the site served
    it, class-for-className, styles intact, URLs made absolute. Renders
    immediately; exempt from the tokens/no-hex laws (it is evidence).
  * **built** — the agent's rebuild inside the measured system (tokens,
    no literal hex, the lint gate). Deliverables come from here.

Scripts and event handlers are stripped — a capture renders, it never
executes the site's code.
"""

from __future__ import annotations

import re
from html.parser import HTMLParser
from urllib.parse import urljoin

VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input",
        "link", "meta", "source", "track", "wbr"}
DROP = {"script", "noscript", "iframe", "template"}

# HTML attribute -> JSX prop, beyond the mechanical kebab->camel cases
ATTR_MAP = {"class": "className", "for": "htmlFor", "tabindex": "tabIndex",
            "srcset": "srcSet", "autocomplete": "autoComplete",
            "autoplay": "autoPlay", "crossorigin": "crossOrigin",
            "spellcheck": "spellCheck", "contenteditable": "contentEditable",
            "maxlength": "maxLength", "minlength": "minLength",
            "readonly": "readOnly", "colspan": "colSpan", "rowspan": "rowSpan",
            "xlink:href": "xlinkHref", "datetime": "dateTime",
            "novalidate": "noValidate", "playsinline": "playsInline"}
URL_ATTRS = {"src", "href", "poster", "data-src"}


def _prop_name(name: str) -> str | None:
    low = name.lower()
    if low.startswith("on"):        # onclick etc. — captures never execute
        return None
    if low == "loading":            # lazy never loads without the site's JS
        return None
    if low in ATTR_MAP:
        return ATTR_MAP[low]
    if low.startswith(("data-", "aria-")):
        return low
    if "-" in low:                  # stroke-width -> strokeWidth (svg et al)
        head, *rest = low.split("-")
        return head + "".join(w.title() for w in rest)
    return low


def _style_object(css: str) -> str:
    pairs = []
    for decl in css.split(";"):
        if ":" not in decl:
            continue
        prop, _, value = decl.partition(":")
        prop, value = prop.strip(), value.strip().replace('"', "'")
        if not prop or not value:
            continue
        if prop.startswith("--"):
            key = f'"{prop}"'
        else:
            head, *rest = prop.lstrip("-").split("-")
            key = head + "".join(w.title() for w in rest)
        pairs.append(f'{key}: "{value}"')
    return "{{" + ", ".join(pairs) + "}}"


class _JSX(HTMLParser):
    """Emits JSX and BALANCES it: audited sections are size-capped, so real
    captures end mid-element — the stack closes what the truncation left
    open, and stray text `<` (a cut-off tag) is escaped, because JSX reads
    a bare `<` in text as a tag start."""

    def __init__(self, base_url: str):
        super().__init__(convert_charrefs=False)
        self.base = base_url
        self.out: list[str] = []
        self.dropping = 0
        self.stack: list[str] = []

    @staticmethod
    def _delazy(attrs):
        """Lazy-load patterns resolve at capture time: the real URL rides in
        data-src/data-srcset while src holds a placeholder — and the site's
        JS (stripped) would have swapped them. We swap instead."""
        d = dict(attrs)
        for lazy, real in (("data-src", "src"), ("data-srcset", "srcset")):
            if d.get(lazy) and (not d.get(real) or d[real].startswith("data:")):
                d[real] = d[lazy]
        return list(d.items())

    def handle_starttag(self, tag, attrs):
        if tag in DROP:
            if tag not in VOID:
                self.dropping += 1
            return
        if self.dropping:
            return
        attrs = self._delazy(attrs)
        if tag in VOID:
            self.out.append(self._open(tag, attrs) + "/>")
        else:
            self.stack.append(tag)
            self.out.append(self._open(tag, attrs) + ">")

    def handle_startendtag(self, tag, attrs):
        if tag in DROP or self.dropping:
            return
        self.out.append(self._open(tag, attrs) + "/>")

    def handle_endtag(self, tag):
        if tag in DROP:
            if tag not in VOID and self.dropping:
                self.dropping -= 1
            return
        if self.dropping or tag in VOID:
            return
        if tag not in self.stack:
            return  # a stray close (its open was truncated away) — skip
        while self.stack:
            open_tag = self.stack.pop()
            self.out.append(f"</{open_tag}>")
            if open_tag == tag:
                break

    def close(self):
        super().close()
        while self.stack:  # whatever the size cap cut off, close it
            self.out.append(f"</{self.stack.pop()}>")

    def handle_data(self, data):
        if self.dropping:
            return
        self.out.append(data.replace("{", "&#123;").replace("}", "&#125;")
                        .replace("<", "&lt;").replace(">", "&gt;"))

    def handle_entityref(self, name):
        if not self.dropping:
            self.out.append(f"&{name};")

    def handle_charref(self, name):
        if not self.dropping:
            self.out.append(f"&#{name};")

    def _open(self, tag, attrs) -> str:
        parts = [f"<{tag}"]
        for name, value in attrs:
            prop = _prop_name(name)
            if prop is None:
                continue
            if value is None:
                parts.append(prop)
            elif prop == "style":
                parts.append(f"style={_style_object(value)}")
            else:
                low = name.lower()
                if low in URL_ATTRS and self.base and value \
                        and not value.startswith(("data:", "#", "mailto:", "tel:")):
                    value = urljoin(self.base, value)
                elif low in ("srcset", "data-srcset") and self.base and value:
                    value = ", ".join(
                        " ".join([urljoin(self.base, part.split()[0])] + part.split()[1:])
                        for part in value.split(",") if part.strip()
                    )
                parts.append(f'{prop}="{value.replace(chr(34), "&quot;")}"')
        return " ".join(parts)


def html_to_jsx(html: str, base_url: str = "") -> str:
    parser = _JSX(base_url)
    parser.feed(html)
    parser.close()
    return "".join(parser.out).strip()


def component_name(candidate: str) -> str:
    words = re.split(r"[^a-zA-Z0-9]+", candidate)
    name = "".join(w.title() for w in words if w)
    return name if name and name[0].isalpha() else f"Captured{name}"


def capture_component(candidate: str, source_html: str, base_url: str = "") -> str:
    """One captured section as a complete .tsx module."""
    name = component_name(candidate)
    jsx = html_to_jsx(source_html, base_url)
    return (
        f"// CAPTURED from {base_url or 'the crawled site'} — monty brand scaffold.\n"
        f"// Faithful evidence, not design: rebuild idiomatically (tokens, no\n"
        f"// literal hex) before shipping it in a deliverable.\n"
        f"export function {name}() {{\n"
        f"  return (\n    <>{jsx}</>\n  );\n"
        f"}}\n"
    )
