from cli.state_map import STATE_TO_PHASE

class CLIRenderer:
    def __init__(self, job):
        self.job = job
        self._last_phase = None

    def on_state_change(self, state):
        phase = STATE_TO_PHASE.get(state)
        if phase and phase != self._last_phase:
            print(phase.value)
            self._last_phase = phase

    def request_user_selection(self, candidates):
        print("\nMultiple official versions found.")
        print("Select the one you want:\n")
    
        shown = candidates[:5]
    
        for idx, c in enumerate(shown, start=1):
            print(f"{idx}. {c['trackName']}")
            print(f"   Artist : {c['artistName']}")
            print(f"   Album  : {c['collectionName']}")
            print(f"   Year   : {c.get('releaseDate', '')[:4]}")
            print()
    
        print(f"{len(shown) + 1}. Cancel import")
    
        try:
            choice = int(input("> ").strip())
        except ValueError:
            return None
    
        if choice == len(shown) + 1:
            return None
    
        if 1 <= choice <= len(shown):
            return choice - 1
    
        return None
        
    
    def info(self, message: str):
        print(f"ℹ️  {message}")

    def warn(self, message: str):
        print(f"⚠️  {message}")

    def error(self, message: str):
        print(f"❌ {message}")
        
    def request_intent_selection(self, candidates):
        print("\nWhich song did you mean?\n")
    
        for idx, c in enumerate(candidates, start=1):
            artists = ", ".join(a["name"] for a in c.get("artists", []))
            print(f"{idx}. {c.get('title')}")
            print(f"   Artist : {artists}")
            if c.get("album"):
                print(f"   Album  : {c['album'].get('name')}")
            print()
    
        print(f"{len(candidates) + 1}. Cancel import")
    
        try:
            choice = int(input("> ").strip())
        except ValueError:
            return None
    
        if choice == len(candidates) + 1:
            return None
    
        if 1 <= choice <= len(candidates):
            return choice - 1
    
        return None


