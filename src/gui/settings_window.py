"""Settings dialog — native macOS form with NSAlert."""

import AppKit
import objc


METHODS = ["mouse", "key", "both"]
KEYS = ["f13", "f14", "f15"]


class SettingsWindow:
    def __init__(self, settings: dict):
        self.settings = settings
        self.fields = {}

    def show(self) -> dict | None:
        """Show NSAlert with native controls. Returns updated settings or None."""
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Keepalive Settings")
        alert.setInformativeText_("Configure the agent that runs on schedule.")
        alert.addButtonWithTitle_("Save")
        alert.addButtonWithTitle_("Cancel")

        # View layout
        label_w = 60
        field_w = 180
        field_h = 24
        row_h = 30
        margin = 10

        num_rows = 5
        view_h = num_rows * row_h + margin
        view_w = label_w + field_w + 16
        view = AppKit.NSView.alloc().initWithFrame_(((0, 0), (view_w, view_h)))

        # --- Helper: label ---
        def make_label(text, y, w=label_w):
            lbl = AppKit.NSTextField.alloc().initWithFrame_(
                ((0, y), (w, field_h))
            )
            lbl.setStringValue_(text)
            lbl.setBezeled_(False)
            lbl.setDrawsBackground_(False)
            lbl.setEditable_(False)
            lbl.setSelectable_(False)
            lbl.setAlignment_(AppKit.NSRightTextAlignment)
            return lbl

        # --- Helper: text field ---
        def make_text(y, x_offset=label_w + 6, w=field_w):
            tf = AppKit.NSTextField.alloc().initWithFrame_(
                ((x_offset, y), (w, field_h))
            )
            return tf

        # --- Row helper ---
        def row_top(idx):
            return view_h - margin - (idx + 1) * row_h

        # Row 0: From (NSDatePicker, time only)
        y0 = row_top(0)
        view.addSubview_(make_label("From:", y0))
        dp_from = AppKit.NSDatePicker.alloc().initWithFrame_(
            ((label_w + 6, y0), (field_w, field_h))
        )
        dp_from.setDatePickerStyle_(AppKit.NSTextFieldAndStepperDatePickerStyle)
        dp_from.setDatePickerElements_(AppKit.NSHourMinuteDatePickerElementFlag)
        dp_from.setDatePickerMode_(AppKit.NSSingleDateMode)
        dp_from.setDrawsBackground_(True)
        dp_from.setBezeled_(True)
        # Set initial value from HH:MM string
        parts = self.settings.get("schedule_from", "04:00").split(":")
        h, m = int(parts[0]), int(parts[1])
        cal = AppKit.NSCalendar.currentCalendar()
        comps = AppKit.NSDateComponents.alloc().init()
        comps.setHour_(h)
        comps.setMinute_(m)
        dp_date = cal.dateFromComponents_(comps)
        if dp_date:
            dp_from.setDateValue_(dp_date)
        view.addSubview_(dp_from)
        self.fields["from"] = dp_from

        # Row 1: To (NSDatePicker, time only)
        y1 = row_top(1)
        view.addSubview_(make_label("To:", y1))
        dp_to = AppKit.NSDatePicker.alloc().initWithFrame_(
            ((label_w + 6, y1), (field_w, field_h))
        )
        dp_to.setDatePickerStyle_(AppKit.NSTextFieldAndStepperDatePickerStyle)
        dp_to.setDatePickerElements_(AppKit.NSHourMinuteDatePickerElementFlag)
        dp_to.setDatePickerMode_(AppKit.NSSingleDateMode)
        dp_to.setDrawsBackground_(True)
        dp_to.setBezeled_(True)
        parts = self.settings.get("schedule_to", "12:00").split(":")
        h, m = int(parts[0]), int(parts[1])
        comps = AppKit.NSDateComponents.alloc().init()
        comps.setHour_(h)
        comps.setMinute_(m)
        dp_date = cal.dateFromComponents_(comps)
        if dp_date:
            dp_to.setDateValue_(dp_date)
        view.addSubview_(dp_to)
        self.fields["to"] = dp_to

        # Row 2: Idle (NSTextField, seconds)
        y2 = row_top(2)
        view.addSubview_(make_label("Idle (s):", y2, w=label_w + 10))
        idle_field = make_text(y2, x_offset=label_w + 16, w=field_w - 10)
        idle_field.setStringValue_(str(self.settings.get("idle", 180)))
        view.addSubview_(idle_field)
        self.fields["idle"] = idle_field

        # Row 3: Method (NSPopUpButton)
        y3 = row_top(3)
        view.addSubview_(make_label("Method:", y3))
        popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            ((label_w + 6, y3), (field_w, field_h)),
            False,
        )
        popup.addItemsWithTitles_(METHODS)
        current_method = self.settings.get("method", "mouse")
        idx = METHODS.index(current_method) if current_method in METHODS else 0
        popup.selectItemAtIndex_(idx)
        view.addSubview_(popup)
        self.fields["method"] = popup

        # Row 4: Key (NSPopUpButton)
        y4 = row_top(4)
        view.addSubview_(make_label("Key:", y4))
        key_popup = AppKit.NSPopUpButton.alloc().initWithFrame_pullsDown_(
            ((label_w + 6, y4), (field_w, field_h)),
            False,
        )
        key_popup.addItemsWithTitles_(KEYS)
        current_key = self.settings.get("key", "f13")
        idx = KEYS.index(current_key) if current_key in KEYS else 0
        key_popup.selectItemAtIndex_(idx)
        view.addSubview_(key_popup)
        self.fields["key"] = key_popup

        alert.setAccessoryView_(view)
        alert.layout()

        response = alert.runModal()

        if response == 1000:  # Save
            return self._read_values()
        return None

    def _read_values(self) -> dict:
        """Extract values from native controls."""
        cal = AppKit.NSCalendar.currentCalendar()
        unit_flags = AppKit.NSCalendarUnitHour | AppKit.NSCalendarUnitMinute

        dp_from = self.fields["from"]
        comps_from = cal.components_fromDate_(unit_flags, dp_from.dateValue())
        schedule_from = f"{comps_from.hour():02d}:{comps_from.minute():02d}"

        dp_to = self.fields["to"]
        comps_to = cal.components_fromDate_(unit_flags, dp_to.dateValue())
        schedule_to = f"{comps_to.hour():02d}:{comps_to.minute():02d}"

        return {
            "schedule_from": schedule_from,
            "schedule_to": schedule_to,
            "idle": int(self.fields["idle"].stringValue()),
            "method": self.fields["method"].titleOfSelectedItem(),
            "key": self.fields["key"].titleOfSelectedItem(),
        }
