# ClassIsland Status Indicator Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add a live ClassIsland connection dot to the top-right of the RandPicker picker window while preserving the window dimensions.

**Architecture:** Reuse the existing `ClassIslandIntegration` QObject and its `connectivityUpdated` signal. Expose that singleton through the picker QML context, then render an absolute-positioned dot whose color is derived from the current status.

**Tech Stack:** Python 3.12+, PySide6, RinUI, Qt Quick/QML, pytest.

## Global Constraints

- Keep the picker window's existing `width` and `height` bindings unchanged.
- Use green only for `Connected`; use red for all other states.
- Do not add polling or new production dependencies.
- Preserve unrelated working-tree changes.

---

### Task 1: Wire and render the ClassIsland status indicator

**Files:**
- Modify: `core/widget.py`
- Modify: `src/widget.qml`
- Test: existing `tests/` suite and QML source inspection

**Interfaces:**
- Consumes: `ClassIslandIntegration.instance()`, `get_connectivity_status()`, and `connectivityUpdated(str)`.
- Produces: a `ClassIslandService` QML context property and a `classIslandConnected` QML property driving the status dot color.

- [ ] **Step 1: Expose the integration QObject to the picker engine**

In `core/widget.py`, import `ClassIslandIntegration` and register its singleton beside the existing context properties:

```python
from .integration.classisland import ClassIslandIntegration

self.engine.rootContext().setContextProperty(
    "ClassIslandService", ClassIslandIntegration.instance()
)
```

- [ ] **Step 2: Add the QML state property and initial status read**

Near the existing widget properties in `src/widget.qml`, add:

```qml
property bool classIslandConnected: ClassIslandService ? ClassIslandService.get_connectivity_status() === "Connected" : false
```

This defaults to red when the service is unavailable.

- [ ] **Step 3: Subscribe to status changes**

Add a `Connections` object under the window root:

```qml
Connections {
    function onConnectivityUpdated(status) {
        widget.classIslandConnected = status === "Connected";
    }

    target: ClassIslandService
}
```

- [ ] **Step 4: Render the fixed-position status dot**

Add a child of `scaledContent` after the layout so it is visually above the buttons and does not affect implicit sizing:

```qml
Rectangle {
    id: classIslandStatusDot

    anchors {
        right: parent.right
        rightMargin: 5
        top: parent.top
        topMargin: 5
    }
    color: widget.classIslandConnected ? "#2eaf5d" : "#d13438"
    height: 7
    radius: width / 2
    width: 7
    z: 2
}
```

Keep the existing `width: Math.round(scaledContent.width * widgetScale)` and `height: Math.round(scaledContent.height * widgetScale)` bindings unchanged.

- [ ] **Step 5: Run focused verification**

Run:

```bash
pytest -q
git diff --check
```

Expected: all existing tests pass, `git diff --check` produces no output, and the QML file still contains the original width and height bindings.

- [ ] **Step 6: Review the final diff**

Run:

```bash
git diff -- core/widget.py src/widget.qml
```

Confirm the only behavior added is the ClassIsland status binding and fixed-size visual dot.
