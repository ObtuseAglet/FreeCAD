# SPDX-License-Identifier: LGPL-2.1-or-later

import os
import re
import subprocess

import FreeCAD as App
import FreeCADGui as Gui
from PySide import QtCore, QtGui
from PySide.QtCore import QT_TRANSLATE_NOOP

_PREFS_PATH = "User parameter:BaseApp/Preferences/Mod/Codex"
_CODE_BLOCK_PATTERN = re.compile(r"```(?:python)?\s*(.*?)```", re.IGNORECASE | re.DOTALL)

_DEFAULT_PROMPT = (
    "Create a simple parametric mechanical part with named dimensions and "
    "reasonable defaults."
)

_PROMPT_TEMPLATE = """
You are generating Python code for FreeCAD.
Return executable Python only. Do not include Markdown fences or explanations.

Rules:
- Use `doc = App.ActiveDocument or App.newDocument("CodexModel")`.
- Build parametric objects where practical.
- Keep names descriptive.
- Recompute at the end.
- Never call exit(), quit(), or GUI-blocking loops.

User request:
{user_prompt}

Additional context:
{selection_context}
"""

_COMMAND_ID = "Codex_GenerateAndRun"
_COMMANDS = [_COMMAND_ID]

_CODEX_ICON_XPM = """
/* XPM */
static const char *codex_generate_icon[] = {
"16 16 4 1",
"  c None",
". c #111111",
"+ c #00A67E",
"@ c #5AD4B0",
"                ",
"    ......      ",
"   .++++++.     ",
"  .++@@@@++.    ",
"  .++@..@++.    ",
"  .++@..@++.    ",
"  .++@@@@++.    ",
"  .++++++..     ",
"  .++....       ",
"  .++.....      ",
"  .++@@@++.     ",
"  .++@.@++.     ",
"  .++@@@++.     ",
"   .++++..      ",
"    ......      ",
"                "};
"""


def _prefs():
    return App.ParamGet(_PREFS_PATH)


def _read_settings():
    pref = _prefs()
    cli_path = pref.GetString("CliPath", "").strip()
    if not cli_path:
        cli_path = os.environ.get("FREECAD_CODEX_CLI", "").strip() or "codex"

    model = pref.GetString("Model", "").strip()
    timeout_seconds = pref.GetInt("TimeoutSeconds", 180)
    if timeout_seconds < 30:
        timeout_seconds = 30
    dry_run = pref.GetBool("DryRun", False)

    return {
        "cli_path": cli_path,
        "model": model,
        "timeout_seconds": timeout_seconds,
        "dry_run": dry_run,
    }


def _selection_context():
    selection = Gui.Selection.getSelection()
    if not selection:
        return "No selected objects."

    lines = []
    for obj in selection[:10]:
        lines.append(
            "- Name: {name}, Label: {label}, Type: {type_id}".format(
                name=getattr(obj, "Name", "<unknown>"),
                label=getattr(obj, "Label", "<unknown>"),
                type_id=getattr(obj, "TypeId", "<unknown>"),
            )
        )
    if len(selection) > 10:
        lines.append("- ... and {count} more selected objects".format(count=len(selection) - 10))

    return "\n".join(lines)


def _extract_python(text):
    cleaned = text.strip()
    if not cleaned:
        return ""

    match = _CODE_BLOCK_PATTERN.search(cleaned)
    if match:
        return match.group(1).strip()

    return cleaned


class _PromptDialog(QtGui.QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Codex Prompt")
        self.resize(760, 460)

        layout = QtGui.QVBoxLayout(self)
        intro = QtGui.QLabel(
            "Describe what Codex should build in the active FreeCAD document. "
            "Detailed constraints improve the generated model."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.prompt_edit = QtGui.QTextEdit(self)
        self.prompt_edit.setAcceptRichText(False)
        self.prompt_edit.setPlainText(_DEFAULT_PROMPT)
        layout.addWidget(self.prompt_edit)

        self.use_selection_box = QtGui.QCheckBox("Include current selection as context", self)
        self.use_selection_box.setChecked(True)
        layout.addWidget(self.use_selection_box)

        buttons = QtGui.QDialogButtonBox(
            QtGui.QDialogButtonBox.Ok | QtGui.QDialogButtonBox.Cancel, self
        )
        buttons.button(QtGui.QDialogButtonBox.Ok).setText("Generate")
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def prompt_text(self):
        return self.prompt_edit.toPlainText().strip()

    def use_selection_context(self):
        return self.use_selection_box.isChecked()


class _CodePreviewDialog(QtGui.QDialog):
    def __init__(self, generated_code, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Codex Generated Script")
        self.resize(860, 640)

        layout = QtGui.QVBoxLayout(self)
        intro = QtGui.QLabel(
            "Review or edit the generated script before running it in the active document."
        )
        intro.setWordWrap(True)
        layout.addWidget(intro)

        self.code_edit = QtGui.QTextEdit(self)
        self.code_edit.setAcceptRichText(False)
        self.code_edit.setPlainText(generated_code)
        self.code_edit.setLineWrapMode(QtGui.QTextEdit.NoWrap)
        self.code_edit.setFont(QtGui.QFont("Courier New"))
        layout.addWidget(self.code_edit)

        buttons = QtGui.QDialogButtonBox(QtGui.QDialogButtonBox.Cancel, self)
        run_button = buttons.addButton("Run in Document", QtGui.QDialogButtonBox.AcceptRole)
        run_button.setDefault(True)
        buttons.accepted.connect(self.accept)
        buttons.rejected.connect(self.reject)
        layout.addWidget(buttons)

    def code(self):
        return self.code_edit.toPlainText().strip()


def _build_codex_prompt(user_prompt, include_selection):
    selection_context = _selection_context() if include_selection else "Selection context disabled."
    return _PROMPT_TEMPLATE.format(
        user_prompt=user_prompt,
        selection_context=selection_context,
    ).strip()


def _run_codex(prompt_text, settings):
    command = [
        settings["cli_path"],
        "exec",
        "--skip-git-repo-check",
        "--sandbox",
        "read-only",
        "-",
    ]
    if settings["model"]:
        command.extend(["--model", settings["model"]])

    completed = subprocess.run(
        command,
        input=prompt_text,
        capture_output=True,
        text=True,
        timeout=settings["timeout_seconds"],
        check=False,
    )

    if completed.returncode != 0:
        error_text = completed.stderr.strip() or completed.stdout.strip() or "Unknown error."
        raise RuntimeError(error_text)

    output = completed.stdout.strip()
    if not output:
        raise RuntimeError("Codex returned an empty response.")

    return output


def _ensure_document():
    doc = App.ActiveDocument
    if doc is None:
        doc = App.newDocument("CodexModel")
    return doc


def _execute_generated_script(script_text):
    doc = _ensure_document()

    globals_dict = {
        "__name__": "__codex_generated__",
        "App": App,
        "FreeCAD": App,
        "Gui": Gui,
        "FreeCADGui": Gui,
        "doc": doc,
    }

    doc.openTransaction("Codex generated model")
    try:
        code_obj = compile(script_text, "<codex-generated>", "exec")
        exec(code_obj, globals_dict, globals_dict)
        doc.recompute()
        doc.commitTransaction()
    except Exception:
        doc.abortTransaction()
        raise


def _show_error(title, message):
    App.Console.PrintError("{0}\n".format(message))
    QtGui.QMessageBox.critical(QtGui.QApplication.activeWindow(), title, message)


class _CodexGenerateCommand:
    def GetResources(self):
        return {
            "Pixmap": _CODEX_ICON_XPM,
            "MenuText": QT_TRANSLATE_NOOP("Codex_GenerateAndRun", "Generate 3D with Codex"),
            "ToolTip": QT_TRANSLATE_NOOP(
                "Codex_GenerateAndRun",
                "Prompt Codex CLI for a FreeCAD Python script, review it, then run it.",
            ),
            "CmdType": "ForEdit",
        }

    def IsActive(self):
        return App.GuiUp

    def Activated(self):
        settings = _read_settings()

        prompt_dialog = _PromptDialog(QtGui.QApplication.activeWindow())
        if prompt_dialog.exec_() != QtGui.QDialog.Accepted:
            return

        user_prompt = prompt_dialog.prompt_text()
        if not user_prompt:
            _show_error("Codex", "Prompt is empty. Please describe what to generate.")
            return

        full_prompt = _build_codex_prompt(user_prompt, prompt_dialog.use_selection_context())

        QtGui.QApplication.setOverrideCursor(QtGui.QCursor(QtCore.Qt.WaitCursor))
        try:
            raw_output = _run_codex(full_prompt, settings)
        except subprocess.TimeoutExpired:
            _show_error(
                "Codex",
                "Codex request timed out after {0} seconds.".format(settings["timeout_seconds"]),
            )
            return
        except FileNotFoundError:
            _show_error(
                "Codex",
                "Codex CLI was not found at '{0}'. Set FREECAD_CODEX_CLI or "
                "Preferences/Mod/Codex/CliPath.".format(settings["cli_path"]),
            )
            return
        except Exception as exc:
            _show_error("Codex", "Codex request failed:\n{0}".format(str(exc)))
            return
        finally:
            QtGui.QApplication.restoreOverrideCursor()

        script_text = _extract_python(raw_output)
        if not script_text:
            _show_error("Codex", "Codex did not return executable Python code.")
            return

        preview = _CodePreviewDialog(script_text, QtGui.QApplication.activeWindow())
        if preview.exec_() != QtGui.QDialog.Accepted:
            return

        final_script = preview.code()
        if not final_script:
            _show_error("Codex", "Script is empty after review.")
            return

        if settings["dry_run"]:
            App.Console.PrintMessage("Codex dry-run enabled. Script was not executed.\n")
            return

        try:
            _execute_generated_script(final_script)
        except Exception as exc:
            _show_error("Codex", "Generated script failed:\n{0}".format(str(exc)))
            return

        App.Console.PrintMessage("Codex script executed successfully.\n")
        QtGui.QMessageBox.information(
            QtGui.QApplication.activeWindow(),
            "Codex",
            "Generated script executed successfully.",
        )


def register_commands():
    commands = Gui.listCommands()
    if _COMMAND_ID not in commands:
        Gui.addCommand(_COMMAND_ID, _CodexGenerateCommand())
    return list(_COMMANDS)
