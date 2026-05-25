# SPDX-License-Identifier: LGPL-2.1-or-later

set(Codex_SRCS
    __init__.py
    Init.py
    InitGui.py
    CodexCommands.py
)

source_group("" FILES ${Codex_SRCS})

add_custom_target(Codex ALL
    SOURCES ${Codex_SRCS}
)

fc_copy_sources(Codex "${CMAKE_BINARY_DIR}/Mod/Codex" ${Codex_SRCS})

install(
    FILES
        ${Codex_SRCS}
    DESTINATION
        Mod/Codex
)
