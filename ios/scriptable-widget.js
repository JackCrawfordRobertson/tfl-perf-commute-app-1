// Commute Widget for Scriptable (iOS)
// Copy this code into a new script in the Scriptable app

// CHANGE THIS to your Pi's IP address or hostname
const API_URL = "http://192.168.1.163:5001/status";

// TfL Piccadilly blue
const LINE_COLOR = "#003688";

async function createWidget() {
  const widget = new ListWidget();

  // Auto dark/light mode
  const isDark = Device.isUsingDarkAppearance();
  widget.backgroundColor = isDark ? new Color("#1C1C1E") : new Color("#FFFFFF");
  const textColor = isDark ? Color.white() : Color.black();
  const subtleText = isDark ? new Color("#8E8E93") : new Color("#6E6E73");

  try {
    const req = new Request(API_URL);
    req.timeoutInterval = 10;
    const data = await req.loadJSON();

    if (!data.active) {
      // Outside commute hours - show relaxing message
      const status = data.schedule_status.toLowerCase();
      const isWeekend = status.includes("saturday") || status.includes("sunday");

      const headerRow = widget.addStack();
      headerRow.centerAlignContent();

      if (isWeekend) {
        const title = headerRow.addText("Day Off 😌");
        title.font = Font.boldSystemFont(16);
        title.textColor = textColor;
      } else {
        const title = headerRow.addText("No Office 🏠");
        title.font = Font.boldSystemFont(16);
        title.textColor = textColor;
      }

      headerRow.addSpacer();
      const refresh = headerRow.addText("↻");
      refresh.font = Font.systemFont(12);
      refresh.textColor = subtleText;

      widget.addSpacer(8);

      const chill = widget.addText("Nowhere to be.");
      chill.font = Font.systemFont(14);
      chill.textColor = subtleText;

      widget.addSpacer(2);

      const exhale = widget.addText("Exhale.");
      exhale.font = Font.italicSystemFont(14);
      exhale.textColor = subtleText;

      return widget;
    }

    // Get commute data
    const commute = data.commute;

    // Header with refresh icon
    const headerRow = widget.addStack();
    const header = headerRow.addText("🚇 " + data.line);
    header.font = Font.boldSystemFont(14);
    header.textColor = new Color(LINE_COLOR);
    headerRow.addSpacer();
    const refresh = headerRow.addText("↻");
    refresh.font = Font.systemFont(12);
    refresh.textColor = subtleText;

    widget.addSpacer(4);

    // Main countdown
    const mins = commute.minutes_until_leave;

    if (commute.should_have_left) {
      // Should have left already
      const late = widget.addText("Leave now");
      late.font = Font.boldSystemFont(20);
      late.textColor = new Color("#FF9500");
    } else if (mins <= 15) {
      // Getting close
      const countdown = widget.addText(`${mins} min`);
      countdown.font = Font.boldSystemFont(24);
      countdown.textColor = mins <= 5 ? new Color("#FF9500") : new Color("#34C759");

      const label = widget.addText("until leave");
      label.font = Font.systemFont(11);
      label.textColor = subtleText;
    } else {
      // Plenty of time
      const countdown = widget.addText(`${mins} min`);
      countdown.font = Font.boldSystemFont(22);
      countdown.textColor = new Color("#34C759");

      const label = widget.addText("until leave");
      label.font = Font.systemFont(11);
      label.textColor = subtleText;
    }

    widget.addSpacer(6);

    // Schedule info
    const leaveInfo = widget.addText(`Leave: ${commute.leave_home}`);
    leaveInfo.font = Font.systemFont(12);
    leaveInfo.textColor = textColor;

    const trainInfo = widget.addText(`Train: ${commute.target_train}`);
    trainInfo.font = Font.systemFont(12);
    trainInfo.textColor = textColor;

    const arriveInfo = widget.addText(`Arrive: ${commute.arrival_target}`);
    arriveInfo.font = Font.systemFont(12);
    arriveInfo.textColor = subtleText;

  } catch (e) {
    const errorRow = widget.addStack();
    const error = errorRow.addText("Cannot connect");
    error.font = Font.boldSystemFont(14);
    error.textColor = textColor;
    errorRow.addSpacer();
    const refresh = errorRow.addText("↻");
    refresh.font = Font.systemFont(12);
    refresh.textColor = subtleText;

    widget.addSpacer(4);

    const hint = widget.addText("Check Pi is running");
    hint.font = Font.systemFont(11);
    hint.textColor = subtleText;
  }

  return widget;
}

// Run
const widget = await createWidget();

if (config.runsInWidget) {
  Script.setWidget(widget);
} else {
  widget.presentSmall();
}

Script.complete();
