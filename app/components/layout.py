from fasthtml.common import *
from monsterui.all import *


def page_layout(title: str, *content):
    """
    Base page layout with mobile-first design using MonsterUI.

    Uses MonsterUI Theme with custom flood status colors.
    """
    custom_styles = Link(rel="stylesheet", href="/public/styles.css")

    return Html(
        Head(
            Meta(charset="utf-8"),
            Meta(name="viewport", content="width=device-width, initial-scale=1"),
            Meta(name="description", content="Live flood monitoring for Shabbington village"),
            Meta(name="theme-color", content="#1e40af"),
            Title(title),
            *Theme.blue.headers(),
            custom_styles,
            Script(src="https://unpkg.com/htmx.org@1.9.10"),
        ),
        Body(
            *content,
            Footer(
                Container(
                    DivCentered(
                        P("Data from Environment Agency real-time data API (Beta).",
                          cls="text-sm text-muted-foreground"),
                        P(
                            "Community-reported guidance only. ",
                            Strong("Do not drive into floodwater.", cls="text-destructive"),
                            cls="text-sm"
                        ),
                    ),
                    cls="py-6 border-t"
                ),
            ),
            hx_boost="true",
            cls="min-h-screen bg-background"
        ),
        lang="en"
    )


def page_header():
    """Page header with app title and emergency context."""
    return Header(
        DivCentered(
            H1("Flood Pulse", cls="text-3xl font-bold text-primary"),
            P("Shabbington Village Road Status", cls="text-muted-foreground"),
            cls="space-y-1"
        ),
        cls="py-4 text-center"
    )
