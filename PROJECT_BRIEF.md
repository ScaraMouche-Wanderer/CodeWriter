# CodeWriter — project brief

A native Linux desktop utility for editing and formatting code, previewing typing playback, and controlling automated input in an application window.

**Stack:** Python · GTK4 · GtkSourceView 5 · ydotool · Linux uinput

## Start here

- [User guide](USER_GUIDE.md): install and use the editor.
- [Application entry point](app.py): application startup.
- [Typing engine](core/typing_engine.py): controlled background input.
- [Text tools](core/code_tools.py): reusable transformations.
- [Test suite](tests/): backend, formatting, settings, and interaction logic.

## Implementation map

| Layer | Source | Responsibility |
| :--- | :--- | :--- |
| Native interface | [main_window.py](ui/main_window.py), [editor.py](ui/editor.py) | GTK window and source editor |
| Editing workflow | [tab_manager.py](ui/tab_manager.py), [find_bar.py](ui/find_bar.py) | Tabs and search |
| Input lifecycle | [typing_engine.py](core/typing_engine.py) | Schedule typing and handle pause/cancellation |
| OS integration | [ydotool.py](backend/ydotool.py) | Send input through the Linux backend |
| Transformations | [code_tools.py](core/code_tools.py), [text_processor.py](core/text_processor.py) | Format, extract, and transform text |
| Configuration | [settings.py](core/settings.py), [profiles.py](core/profiles.py) | Persist preferences and speed presets |

## Design decisions worth discussing

- **Use native widgets.** GTK and GtkSourceView provide an editor integrated with the Linux desktop.
- **Separate interface and backend.** The input engine and backend can be reasoned about independently of editor widgets.
- **Keep control during automation.** A countdown, playback preview, pause, and cancellation make input jobs visible and interruptible.
- **Treat input as an OS integration problem.** Wayland/X11 behavior, uinput permissions, keyboard layouts, and window focus affect the result.

## Three-minute demonstration

1. Open a short code snippet in the editor.
2. Apply a text transformation and inspect the change.
3. Preview typing in the simulation player.
4. Use a harmless scratch editor to demonstrate pause and cancellation.

[Watch the recorded playback demo](docs/assets/codewriter_demo.gif).

## Reproduce checks

After following the Linux dependency setup in [USER_GUIDE.md](USER_GUIDE.md):

```bash
python3 -m pytest tests/ -v
```

Desktop dependencies are required for tests that import GTK. Review backend mocks separately from an actual input-delivery test on the target desktop.

## Scope

CodeWriter automates input for user-controlled workflows. Focus changes, desktop permissions, and keyboard layout can affect delivery. Playback demonstrates the planned input; actual delivery requires testing in the intended target window.
