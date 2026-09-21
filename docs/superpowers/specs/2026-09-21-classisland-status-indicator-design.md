# ClassIsland Connection Status Indicator

## Goal

Show the current RandPicker-to-ClassIsland connection state as a small status dot in the top-right corner of the main picker window without changing that window's dimensions.

## Design

The picker window will consume the existing `ClassIslandIntegration` QObject. `core/widget.py` will expose the singleton integration object to the picker QML context. `src/widget.qml` will read the initial value through `get_connectivity_status()` and subscribe to `connectivityUpdated` so the dot changes as the IPC client connects, disconnects, or stops.

The dot will be an absolute-positioned visual child of `scaledContent`. It will not participate in `mainLayout`, so the existing implicit width and height calculations remain unchanged. The dot will use green only for `Connected`; `NotConnected`, `NotRunning`, and `NotAvailable` will all use red. A small border will keep the dot visible against both light and dark backgrounds.

## Data Flow

`ClassIslandIntegration._set_connectivity()` emits `connectivityUpdated(status)`. The QML `Connections` object updates a local `classIslandConnected` property. The dot's color is bound to that property, with a red default when the integration object is unavailable or the status is anything other than `Connected`.

## Error Handling

If ClassIsland IPC assemblies are unavailable, the fallback integration reports `NotAvailable`; the dot therefore remains red. If no integration object is exposed, the QML fallback status is also red. No connection attempt or polling is added by the UI.

## Verification

Run the existing Python test suite and inspect the QML changes to confirm that only the context property and visual overlay are added. Verify that `src/widget.qml` still derives the window `width` and `height` from the unchanged `scaledContent` dimensions.
