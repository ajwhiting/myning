class BlacksmithItem:
    def __init__(self, name: str, main_affect: int, value: int) -> None:
        self.name = name
        self.main_affect = main_affect
        self.value = value


TIERS = [
    BlacksmithItem("Soldier", 15, 50),
    BlacksmithItem("Commander", 20, 250),
    BlacksmithItem("General", 30, 500),
    BlacksmithItem("Samurai", 40, 1_000),
    BlacksmithItem("Ninja", 50, 2_000),
    BlacksmithItem("Jedi", 75, 5_000),
    BlacksmithItem("Blademaster", 100, 10_000),
    BlacksmithItem("Spartan", 150, 40_000),
    BlacksmithItem("Hero", 250, 200_000),
]
