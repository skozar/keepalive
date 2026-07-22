"""Settings dialog — NSAlert with 4 text fields."""

import AppKit
import objc


class SettingsWindow:
    def __init__(self, settings: dict):
        self.settings = settings
        self.fields = {}

    def show(self) -> dict | None:
        """Show NSAlert with accessory form. Returns updated settings or None on cancel."""
        alert = AppKit.NSAlert.alloc().init()
        alert.setMessageText_("Keepalive Settings")
        alert.setInformativeText_("Configure the agent that runs on schedule.")
        alert.addButtonWithTitle_("Save")
        alert.addButtonWithTitle_("Cancel")

        # Create accessory view with labels and text fields
        view_width = 260
        label_width = 70
        field_width = 180
        field_height = 24
        row_height = 30
        margin = 10

        num_rows = 4
        view_height = num_rows * row_height + margin
        view = AppKit.NSView.alloc().initWithFrame_(((0, 0), (view_width, view_height)))

        fields_config = [
            ("Schedule:", "schedule", "04:00-12:00"),
            ("Idle (s):", "idle", "180"),
            ("Method:", "method", "mouse"),
            ("Key:", "key", "f13"),
        ]

        for i, (label_text, key, default) in enumerate(fields_config):
            y = view_height - margin - (i + 1) * row_height

            # Label
            label = AppKit.NSTextField.alloc().initWithFrame_(
                ((0, y), (label_width, field_height))
            )
            label.setStringValue_(label_text)
            label.setBezeled_(False)
            label.setDrawsBackground_(False)
            label.setEditable_(False)
            label.setSelectable_(False)
            label.setAlignment_(AppKit.NSRightTextAlignment)
            view.addSubview_(label)

            # Text field
            field = AppKit.NSTextField.alloc().initWithFrame_(
                ((label_width + 6, y), (field_width, field_height))
            )
            value = str(self.settings.get(key, default))
            field.setStringValue_(value)
            view.addSubview_(field)
            self.fields[key] = field

        alert.setAccessoryView_(view)
        alert.layout()

        response = alert.runModal()

        # NSAlertFirstButtonReturn = 1000, NSAlertSecondButtonReturn = 1001
        if response == 1000:  # Save
            return {
                "schedule": self.fields["schedule"].stringValue(),
                "idle": int(self.fields["idle"].stringValue()),
                "method": self.fields["method"].stringValue(),
                "key": self.fields["key"].stringValue(),
            }
        return None
