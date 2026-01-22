from fasthtml.common import *
from monsterui.all import *
from app.models.domain import (
    RoadId,
    RoadStatus,
    Confidence,
    ROAD_LABELS,
    STATUS_LABELS,
    STATUS_DESCRIPTIONS,
    CONFIDENCE_LABELS,
)
from app.components.road_card import STATUS_BG_CLASSES, STATUS_TEXT_CLASSES


def status_radio_card(status: RoadStatus, label: str, description: str):
    """A large, tappable radio card for status selection."""
    bg_class = STATUS_BG_CLASSES[status]
    text_class = STATUS_TEXT_CLASSES[status]

    return Label(
        Input(
            type="radio",
            name="status",
            value=str(status.value),
            required=True,
            cls="peer sr-only"
        ),
        Div(
            Div(
                Span(label, cls=f"font-semibold text-base {text_class}"),
                cls="flex items-center gap-2"
            ),
            P(description, cls="text-sm text-muted-foreground mt-1"),
            cls=f"p-4 rounded-lg border-2 border-transparent peer-checked:border-primary {bg_class} cursor-pointer transition-all"
        ),
        cls="block"
    )


def confidence_radio_card(confidence: Confidence, label: str):
    """A tappable radio card for confidence selection."""
    return Label(
        Input(
            type="radio",
            name="confidence",
            value=confidence.value,
            required=True,
            cls="peer sr-only"
        ),
        Div(
            Span(label, cls="font-medium"),
            cls="p-3 rounded-lg border-2 border-muted peer-checked:border-primary peer-checked:bg-primary/10 cursor-pointer transition-all text-center"
        ),
        cls="block"
    )


def report_form(road_id: str):
    """
    Modal form for submitting road status reports.

    Uses MonsterUI Modal with large, accessible touch targets.
    """
    road_label = ROAD_LABELS.get(RoadId(road_id), road_id)

    # Status options (exclude UNKNOWN - users shouldn't report that)
    status_options = [
        (RoadStatus.CLEAR, STATUS_LABELS[RoadStatus.CLEAR], STATUS_DESCRIPTIONS[RoadStatus.CLEAR]),
        (RoadStatus.CAUTION, STATUS_LABELS[RoadStatus.CAUTION], STATUS_DESCRIPTIONS[RoadStatus.CAUTION]),
        (RoadStatus.HIGH_CLEARANCE, STATUS_LABELS[RoadStatus.HIGH_CLEARANCE], STATUS_DESCRIPTIONS[RoadStatus.HIGH_CLEARANCE]),
        (RoadStatus.CLOSED, STATUS_LABELS[RoadStatus.CLOSED], STATUS_DESCRIPTIONS[RoadStatus.CLOSED]),
    ]

    confidence_options = [
        (Confidence.DROVE_IT, CONFIDENCE_LABELS[Confidence.DROVE_IT]),
        (Confidence.SAW_IT, CONFIDENCE_LABELS[Confidence.SAW_IT]),
        (Confidence.HEARD_IT, CONFIDENCE_LABELS[Confidence.HEARD_IT]),
    ]

    return Dialog(
        Div(
            # Header
            DivFullySpaced(
                H2(f"Report: {road_label}", cls="text-xl font-semibold"),
                Button(
                    UkIcon("x", cls="w-5 h-5"),
                    cls="p-2 hover:bg-muted rounded-full",
                    onclick="this.closest('dialog').close(); document.getElementById('modal-container').innerHTML = '';"
                ),
                cls="p-4 border-b"
            ),

            # Form
            Form(
                Div(
                    # Status selection
                    Fieldset(
                        Legend("What's the road status?", cls="text-base font-semibold mb-3"),
                        Div(
                            *[
                                status_radio_card(status, label, description)
                                for status, label, description in status_options
                            ],
                            cls="space-y-2"
                        ),
                        cls="mb-6"
                    ),

                    # Confidence selection
                    Fieldset(
                        Legend("How do you know?", cls="text-base font-semibold mb-3"),
                        Grid(
                            *[
                                confidence_radio_card(conf, label)
                                for conf, label in confidence_options
                            ],
                            cols=1,
                            cols_sm=3,
                            cls="gap-2"
                        ),
                        cls="mb-6"
                    ),

                    # Optional comment
                    Div(
                        Label(
                            "Additional details (optional)",
                            cls="text-sm font-medium mb-2 block"
                        ),
                        TextArea(
                            name="comment",
                            placeholder="e.g., 'Water over centre line near the dip'",
                            maxlength="280",
                            rows="2",
                            cls="w-full p-3 rounded-lg border border-muted focus:border-primary focus:ring-1 focus:ring-primary"
                        ),
                        cls="mb-6"
                    ),

                    # Submit button
                    Button(
                        "Submit Report",
                        type="submit",
                        cls=ButtonT.primary + " w-full py-4 text-lg font-semibold"
                    ),

                    cls="p-4"
                ),

                hx_post=f"/report/{road_id}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
            ),
            cls="bg-background rounded-xl max-w-lg w-full mx-4 max-h-[90vh] overflow-y-auto"
        ),
        open=True,
        id="report-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    )


def submission_result(success: bool, message: str, road_id: str):
    """
    Result display after form submission.

    Triggers refresh of road status on success.
    """
    icon = UkIcon("check-circle", cls="w-12 h-12 text-green-500") if success else UkIcon("alert-circle", cls="w-12 h-12 text-red-500")
    title = "Thank you!" if success else "Error"
    title_cls = "text-green-700" if success else "text-red-700"

    return Dialog(
        Div(
            DivCentered(
                icon,
                H3(title, cls=f"text-xl font-semibold {title_cls}"),
                P(message, cls="text-muted-foreground text-center"),
                Button(
                    "Close",
                    onclick="this.closest('dialog').close(); document.getElementById('modal-container').innerHTML = '';",
                    cls=ButtonT.default + " w-full mt-4 py-3"
                ),
                cls="p-6 space-y-4"
            ),
            # Trigger road card refresh on success
            hx_trigger="load" if success else None,
            hx_get=f"/api/road/{road_id}" if success else None,
            hx_target=f"#road-{road_id}" if success else None,
            hx_swap="outerHTML" if success else None,
            cls="bg-background rounded-xl max-w-sm w-full mx-4"
        ),
        open=True,
        id="result-modal",
        cls="fixed inset-0 z-50 flex items-center justify-center bg-black/50 backdrop-blur-sm"
    )
