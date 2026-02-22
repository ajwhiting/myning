from myning.utilities.ui import Colors


class Formatter:
    @staticmethod
    def abbreviate(n: int | float) -> str:
        """Format large numbers with a suffix for compact display (e.g. 1_500_000 → '1.5M')."""
        for threshold, suffix in [
            (1_000_000_000_000_000, "P"),
            (1_000_000_000_000, "T"),
            (1_000_000_000, "B"),
            (1_000_000, "M"),
            (1_000, "K"),
        ]:
            if n >= threshold:
                return f"{n / threshold:.1f}{suffix}"
        return str(int(n))

    @staticmethod
    def gold(g: int):
        return Colors.GOLD(f"{g:,}g")

    @staticmethod
    def xp(x: int):
        return Colors.XP(f"{Formatter.abbreviate(x)} xp")

    @staticmethod
    def soul_credits(sc: float):
        return Colors.SOUL_CREDITS(f"{sc:.2f} soul credits")

    @staticmethod
    def research_points(rp: float):
        return Colors.RESEARCH_POINTS(f"{rp:.2f} research points")

    @staticmethod
    def level(lvl: int):
        return Colors.LEVEL(lvl)

    @staticmethod
    def locked(s: str):
        return Colors.LOCKED(s)

    @staticmethod
    def water(w: int):
        return Colors.WATER(f"{w} water")

    @staticmethod
    def percentage(p: float):
        p *= 100
        return f"{p:.0f}%" if p.is_integer else f"{p:.2f}%"

    @staticmethod
    def title(t: str):
        return t.replace("_", " ").title()

    @staticmethod
    def keybind(k: str):
        return f"[bold dodger_blue1]{k}[/]"
