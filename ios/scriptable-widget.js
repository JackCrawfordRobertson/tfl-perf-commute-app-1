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
      // Outside commute hours
      const headerRow = widget.addStack();
      const title = headerRow.addText("No Commute");
      title.font = Font.boldSystemFont(16);
      title.textColor = textColor;
      headerRow.addSpacer();
      const refresh = headerRow.addText("↻");
      refresh.font = Font.systemFont(12);
      refresh.textColor = subtleText;

      widget.addSpacer(4);

      const status = widget.addText(data.schedule_status);
      status.font = Font.systemFont(12);
      status.textColor = subtleText;

      return widget;
    }

    // Header with refresh icon
    const headerRow = widget.addStack();
    const header = headerRow.addText(data.line + " Line");
    header.font = Font.boldSystemFont(14);
    header.textColor = new Color(LINE_COLOR);
    headerRow.addSpacer();
    const refresh = headerRow.addText("↻");
    refresh.font = Font.systemFont(12);
    refresh.textColor = subtleText;

    widget.addSpacer(6);

    if (data.best_train) {
      const best = data.best_train;
      const mins = best.countdown_minutes;
      const secs = best.countdown_seconds % 60;

      if (best.countdown_seconds <= 0) {
        // LEAVE NOW
        const leaveNow = widget.addText("LEAVE NOW!");
        leaveNow.font = Font.boldSystemFont(22);
        leaveNow.textColor = new Color("#ff6b6b");

      } else if (mins <= 10) {
        // Countdown mode
        const countdown = widget.addText(`${mins}m ${secs}s`);
        countdown.font = Font.boldSystemFont(28);
        countdown.textColor = new Color("#ffd93d");

        const label = widget.addText("until leave");
        label.font = Font.systemFont(11);
        label.textColor = subtleText;

      } else {
        // Plenty of time
        const countdown = widget.addText(`${mins} min`);
        countdown.font = Font.boldSystemFont(24);
        countdown.textColor = new Color("#34C759");

        const label = widget.addText("until leave");
        label.font = Font.systemFont(11);
        label.textColor = subtleText;
      }

      widget.addSpacer(6);

      // Train info
      const trainInfo = widget.addText(`Train: ${best.train_departs}`);
      trainInfo.font = Font.systemFont(12);
      trainInfo.textColor = textColor;

      const arriveInfo = widget.addText(`Arrive: ${best.arrival_at_work}`);
      arriveInfo.font = Font.systemFont(12);
      arriveInfo.textColor = textColor;

    } else {
      const noTrain = widget.addText("No suitable train");
      noTrain.font = Font.systemFont(14);
      noTrain.textColor = new Color("#E32017");

      widget.addSpacer(4);

      const late = widget.addText(`All trains arrive after ${data.work_start}`);
      late.font = Font.systemFont(11);
      late.textColor = subtleText;
    }

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
