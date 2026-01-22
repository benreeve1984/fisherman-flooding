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
            Span(label, cls=f"font-semibold {text_class}"),
            P(description, cls="text-xs text-muted-foreground"),
            cls=f"p-3 rounded-lg border-2 border-transparent peer-checked:border-primary peer-checked:ring-2 peer-checked:ring-primary/20 {bg_class} cursor-pointer"
        ),
        cls="block"
    )


def confidence_radio_card(confidence: Confidence, label: str):
    """A tappable radio card for confidence selection."""
    input_id = f"confidence-{confidence.value}"
    # Use onclick on label for reliable iOS support
    click_handler = f"document.querySelectorAll('.confidence-card').forEach(c => c.classList.remove('selected')); document.getElementById('card-{confidence.value}').classList.add('selected');"
    return Label(
        Input(
            type="radio",
            name="confidence",
            value=confidence.value,
            id=input_id,
            required=True,
            cls="hidden",
        ),
        Div(
            Span(label, cls="text-sm font-medium"),
            id=f"card-{confidence.value}",
            cls="confidence-card p-3 rounded-lg border-2 border-muted bg-muted/30 cursor-pointer text-center transition-all"
        ),
        onclick=click_handler,
        cls="block"
    )


def report_form(road_id: str):
    """
    Modal form for submitting road status reports.

    Uses a div-based modal overlay for reliable mobile display.
    """
    road_label = ROAD_LABELS.get(RoadId(road_id), road_id)

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

    close_script = "document.getElementById('modal-container').innerHTML = '';"

    return Div(
        # Backdrop
        Div(
            onclick=close_script,
            cls="fixed inset-0 bg-black/50"
        ),
        # Modal content
        Div(
            # Header
            Div(
                H2(f"Report: {road_label}", cls="text-lg font-semibold"),
                Button(
                    "✕",
                    type="button",
                    onclick=close_script,
                    cls="p-1 text-xl leading-none hover:bg-muted rounded"
                ),
                cls="flex justify-between items-center p-4 border-b"
            ),
            # Form
            Form(
                Div(
                    # Status selection
                    Fieldset(
                        Legend("What's the road status?", cls="font-semibold mb-2"),
                        Div(
                            *[status_radio_card(s, l, d) for s, l, d in status_options],
                            cls="space-y-2"
                        ),
                        cls="mb-4"
                    ),
                    # Confidence selection
                    Fieldset(
                        Legend("How do you know?", cls="font-semibold mb-2"),
                        Div(
                            *[confidence_radio_card(c, l) for c, l in confidence_options],
                            cls="grid grid-cols-1 gap-2"
                        ),
                        cls="mb-4"
                    ),
                    # Optional comment
                    Div(
                        Label("Details (optional)", cls="text-sm font-medium block mb-1"),
                        Textarea(
                            name="comment",
                            placeholder="e.g., 'Water over road near the dip'",
                            maxlength="280",
                            rows="2",
                            cls="w-full p-2 rounded border border-muted text-sm"
                        ),
                        cls="mb-4"
                    ),
                    # Submit
                    Button(
                        "Submit Report",
                        type="submit",
                        cls=ButtonT.primary + " w-full py-3 font-semibold"
                    ),
                    cls="p-4"
                ),
                hx_post=f"/report/{road_id}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
            ),
            cls="bg-white dark:bg-gray-900 rounded-t-2xl w-full max-h-[85vh] overflow-y-auto fixed bottom-0 left-0 right-0 shadow-2xl"
        ),
        cls="fixed inset-0 z-50",
        id="report-modal"
    )


def submission_result(success: bool, message: str, road_id: str):
    """Result display after form submission."""
    close_script = "document.getElementById('modal-container').innerHTML = '';"
    icon = "✓" if success else "✗"
    icon_cls = "text-green-500" if success else "text-red-500"
    title = "Thank you!" if success else "Error"
    title_cls = "text-green-700" if success else "text-red-700"

    return Div(
        # Backdrop
        Div(onclick=close_script, cls="fixed inset-0 bg-black/50"),
        # Result content - smaller and properly centered
        Div(
            Span(icon, cls=f"text-3xl {icon_cls}"),
            H3(title, cls=f"text-lg font-semibold {title_cls} mt-1"),
            P(message, cls="text-muted-foreground text-center text-xs mt-1"),
            Button(
                "Close",
                type="button",
                onclick=close_script,
                cls=ButtonT.default + " w-full mt-3 py-2"
            ),
            # Trigger road card refresh on success
            hx_trigger="load" if success else None,
            hx_get=f"/api/road/{road_id}" if success else None,
            hx_target=f"#road-{road_id}" if success else None,
            hx_swap="outerHTML" if success else None,
            cls="bg-white dark:bg-gray-900 rounded-xl p-4 w-64 shadow-2xl fixed top-1/2 left-1/2 -translate-x-1/2 -translate-y-1/2 text-center"
        ),
        cls="fixed inset-0 z-50",
        id="result-modal"
    )
