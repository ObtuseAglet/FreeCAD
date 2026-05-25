# SPDX-License-Identifier: LGPL-2.1-or-later

import FreeCAD
import FreeCADGui
from PySide.QtCore import QT_TRANSLATE_NOOP


class CodexWorkbench(FreeCADGui.Workbench):
    """Workbench that integrates Codex CLI into FreeCAD."""

    Icon = """
/* XPM */
static const char *codex_workbench_icon[] = {
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

    MenuText = QT_TRANSLATE_NOOP("Workbench", "Codex")
    ToolTip = QT_TRANSLATE_NOOP(
        "Workbench", "Generate and run FreeCAD Python scripts with Codex CLI."
    )

    def Initialize(self):
        import CodexCommands

        commands = CodexCommands.register_commands()
        self.appendToolbar(QT_TRANSLATE_NOOP("Workbench", "Codex"), commands)
        self.appendMenu([QT_TRANSLATE_NOOP("Workbench", "&Codex")], commands)
        FreeCAD.Console.PrintLog("Loading Codex workbench, done.\n")

    def Activated(self):
        FreeCAD.Console.PrintLog("Codex workbench activated.\n")

    def Deactivated(self):
        FreeCAD.Console.PrintLog("Codex workbench deactivated.\n")

    def GetClassName(self):
        return "Gui::PythonWorkbench"


FreeCADGui.addWorkbench(CodexWorkbench())
