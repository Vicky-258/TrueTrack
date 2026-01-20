from cli.state_map import STATE_TO_PHASE


# =====================================================
# Interactive CLI Renderer
# =====================================================

class CLIRenderer:
    """
    Human-facing renderer for the interactive CLI.
    Responsible for:
    - phase display
    - user intent selection
    - metadata disambiguation
    """

    def __init__(self, job):
        self.job = job
        self._last_phase = None

    # -------------------------
    # Phase rendering
    # -------------------------

    def on_state_change(self, state):
        phase = STATE_TO_PHASE.get(state)
        if phase and phase != self._last_phase:
            print(phase.value)
            self._last_phase = phase

    # -------------------------
    # Identity (YouTube intent)
    # -------------------------

    def request_intent_selection(self, candidates):
        print("\nWhich song did you mean?\n")

        for idx, c in enumerate(candidates, start=1):
            artists = ", ".join(c.get("artists", []))
            print(f"{idx}. {c.get('title')}")
            if artists:
                print(f"   Artist : {artists}")
            if c.get("album"):
                print(f"   Album  : {c['album']}")
            print()

        print(f"{len(candidates) + 1}. Cancel import")

        return self._read_choice(len(candidates))

    # -------------------------
    # Metadata (iTunes)
    # -------------------------

    def request_metadata_selection(self, candidates):
        print("\nMultiple official versions found.")
        print("Select the one you want:\n")

        shown = candidates[:5]

        for idx, c in enumerate(shown, start=1):
            print(f"{idx}. {c['trackName']}")
            print(f"   Artist : {c['artistName']}")
            print(f"   Album  : {c['collectionName']}")
            year = c.get("releaseDate", "")[:4]
            if year:
                print(f"   Year   : {year}")
            print()

        print(f"{len(shown) + 1}. Cancel import")

        return self._read_choice(len(shown))

    # -------------------------
    # Messaging
    # -------------------------

    def info(self, message: str):
        print(f"ℹ️  {message}")

    def warn(self, message: str):
        print(f"⚠️  {message}")

    def error(self, message: str):
        print(f"❌ {message}")

    # -------------------------
    # Internal helper
    # -------------------------

    def _read_choice(self, max_valid: int):
        try:
            choice = int(input("> ").strip())
        except ValueError:
            return None

        if choice == max_valid + 1:
            return None

        if 1 <= choice <= max_valid:
            return choice - 1

        return None

