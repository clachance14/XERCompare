# XERCompare for Windows

[Download the Windows beta](https://github.com/clachance14/XERCompare/releases/download/v0.3.0/XERCompare-Windows.zip)
or [read the PDF guide](https://github.com/clachance14/XERCompare/releases/download/v0.3.0/XERCompare-Start-Here.pdf).

Right-click **XERCompare-Windows.zip**, choose **Extract All**, and open the
extracted folder. Double-click **XERCompare.exe**. It includes Python and its required libraries;
you do not need to install Python or Primavera P6. This release is for 64-bit Windows.

1. Browse to the older/baseline `.xer` file.
2. Browse to the revised/update `.xer` file.
3. Choose your output folder and click **Compare schedules**.
4. Use **Open Excel**, **Open PDF**, or **Open folder** when the comparison finishes.

Each run creates a new dated folder containing `compare.xlsx` and `compare.pdf`.
Earlier runs are preserved. Cancel stops between processing steps and removes
unfinished reports. The window remains responsive while a comparison runs.

The **Report catalog** shows the 39 worksheet names and previews up to 200 rows
per sheet. Open Excel for all rows, filters, and highlighted revised cells.
Use **Warnings** to review parser and comparison limitations for your files.
Scroll the comparison page on shorter screens to reach the output buttons.

Version 0.3.0 retains measurements with one decimal place and costs with two,
including monetary UDFs. Counts remain whole numbers. Excel keeps the original
numeric precision underneath its display formatting. Regenerate existing reports
with the updated app to apply the new formatting.

The **Example files** folder in the ZIP contains two entirely synthetic XERs for a trial run.
No real project data is included.

## Help and package contents

Open **START HERE.pdf** for the four-page guide: opening the app, running a
comparison, reading the results, trying the examples, and quick troubleshooting.
All distributed documents are PDFs. The main folder contains one app and the guide:

```text
XERCompare.exe
START HERE.pdf
Documents/Licenses.pdf
Example files/base.xer
Example files/revised.xer
```

There is no CLI executable or installer in the shared package. For a trial run,
choose `base.xer` as the older file and `revised.xer` as the update. Expect one
added, one deleted, two modified and one unchanged activity.

For convenient access, right-click the app, select **Show more options** if
shown, then **Send to > Desktop (create shortcut)**. Keep the app folder where
the shortcut points. Send the complete ZIP when sharing with someone else.

## Local operation and limits

XERCompare never needs internet. It reads the selected files locally, writes
reports only in the output folder you choose, and uses `%TEMP%` to unpack its
bundled runtime. It has no upload, telemetry, account, or license-server feature.

It compares stored P6 fields and does not recalculate CPM. Driving Path Change is
labeled as a stored total-float <= 0 approximation. Unavailable DCMA metrics are
N/A with reasons. Only the first project in each XER is compared, with a warning
when additional projects exist. Renamed Activity IDs appear as delete/add.

This release was verified using synthetic and local real inputs on Windows,
including an isolated packaged run without Python on PATH. Testing on a
separate machine with no installed Python remains pending.

## Give feedback

[Report a problem or share your experience](https://github.com/clachance14/XERCompare/issues/new/choose),
or [ask a question](https://github.com/clachance14/XERCompare/discussions).
GitHub feedback is public and requires a GitHub account. Include the app version,
Windows version, and expected versus actual results. Use synthetic examples;
do not post confidential XERs, reports, or identifying screenshots. Feedback is
voluntary and separate from the offline app.

XERCompare is MIT licensed. See `Documents/Licenses.pdf` in the
ZIP, or **About XERCompare → License and third-party notices** inside the app.
