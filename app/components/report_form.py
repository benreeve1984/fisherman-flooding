from fasthtml.common import *
from app.models.domain import (
    RoadId,
    RoadStatus,
    Confidence,
    ROAD_LABELS,
    STATUS_LABELS,
    STATUS_DESCRIPTIONS,
    CONFIDENCE_LABELS,
)
from app.components.road_card import STATUS_CLASSES


def report_form(road_id: str):
    """
    Modal form for submitting road status reports.

    Uses HTMX for form submission without page reload.
    """
    road_label = ROAD_LABELS.get(RoadId(road_id), road_id)

    # Status options (exclude UNKNOWN - users shouldn't report that)
    status_options = [
        (RoadStatus.CLEAR, STATUS_LABELS[RoadStatus.CLEAR], STATUS_DESCRIPTIONS[RoadStatus.CLEAR]),
        (RoadStatus.CAUTION, STATUS_LABELS[RoadStatus.CAUTION], STATUS_DESCRIPTIONS[RoadStatus.CAUTION]),
        (RoadStatus.HIGH_CLEARANCE, STATUS_LABELS[RoadStatus.HIGH_CLEARANCE], STATUS_DESCRIPTIONS[RoadStatus.HIGH_CLEARANCE]),
        (RoadStatus.CLOSED, STATUS_LABELS[RoadStatus.CLOSED], STATUS_DESCRIPTIONS[RoadStatus.CLOSED]),
    ]

    return Dialog(
        Article(
            Header(
                H3(f"Report: {road_label}"),
                Button(
                    "X",
                    cls="close-button",
                    onclick="this.closest('dialog').close(); document.getElementById('modal-container').innerHTML = '';"
                ),
                cls="dialog-header"
            ),
            Form(
                # Status selection
                Fieldset(
                    Legend("Road Status"),
                    *[
                        Label(
                            Input(
                                type="radio",
                                name="status",
                                value=str(status.value),
                                required=True
                            ),
                            Span(label, cls=f"status-option {STATUS_CLASSES[status]}"),
                            Br(),
                            Small(description, cls="option-description"),
                            cls="radio-label"
                        )
                        for status, label, description in status_options
                    ],
                    cls="status-fieldset"
                ),

                # Confidence selection
                Fieldset(
                    Legend("How do you know?"),
                    *[
                        Label(
                            Input(
                                type="radio",
                                name="confidence",
                                value=conf.value,
                                required=True
                            ),
                            Span(CONFIDENCE_LABELS[conf]),
                            cls="radio-label"
                        )
                        for conf in [Confidence.DROVE_IT, Confidence.SAW_IT, Confidence.HEARD_IT]
                    ],
                    cls="confidence-fieldset"
                ),

                # Optional comment
                Label(
                    "Additional details (optional)",
                    Textarea(
                        name="comment",
                        placeholder="e.g., 'Water over centre line near the dip'",
                        maxlength="280",
                        rows="2"
                    ),
                    cls="comment-label"
                ),

                # Submit button
                Button(
                    "Submit Report",
                    type="submit",
                    cls="submit-button"
                ),

                hx_post=f"/report/{road_id}",
                hx_target="#modal-container",
                hx_swap="innerHTML",
                cls="report-form"
            ),
            cls="report-dialog"
        ),
        open=True,
        id="report-modal"
    )


def submission_result(success: bool, message: str, road_id: str):
    """
    Result display after form submission.

    Triggers refresh of road status on success.
    """
    return Dialog(
        Article(
            Div(
                H3("Thank you!" if success else "Error"),
                P(message),
                cls=f"submission-result {'success' if success else 'error'}"
            ),
            Footer(
                Button(
                    "Close",
                    onclick="this.closest('dialog').close(); document.getElementById('modal-container').innerHTML = '';",
                    cls="close-button-footer"
                ),
            ),
            # Trigger road card refresh on success
            hx_trigger="load" if success else None,
            hx_get=f"/api/road/{road_id}" if success else None,
            hx_target=f"#road-{road_id}" if success else None,
            hx_swap="outerHTML" if success else None,
        ),
        open=True,
        id="result-modal"
    )
