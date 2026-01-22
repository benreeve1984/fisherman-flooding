from fasthtml.common import *


def page_layout(title: str, *content):
    """
    Base page layout with mobile-first design.

    Uses Pico CSS as foundation with custom overrides.
    """
    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="description", content="Live flood monitoring for Shabbington village"),
            Meta(name="theme-color", content="#1e40af"),
            Title(title),
            Link(rel="stylesheet", href="https://cdn.jsdelivr.net/npm/@picocss/pico@2/css/pico.min.css"),
            Link(rel="stylesheet", href="/public/styles.css"),
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            *content,
            Footer(
                Div(
                    P("Data from Environment Agency real-time data API (Beta).",
                      cls="attribution"),
                    P("Community-reported guidance only. ",
                      Strong("Do not drive into floodwater."),
                      cls="disclaimer"),
                    cls="footer-content"
                ),
                cls="page-footer"
            ),
            hx_boost="true"
        ),
        lang="en"
    )


def page_header():
    """Page header with app title."""
    return Header(
        H1("Flood Pulse"),
        P("Shabbington Village", cls="subtitle"),
        cls="page-header"
    )
