from myning.objects.player import Player
from myning.objects.stats import Stats
from myning.utilities.file_manager import FileManager


def run():
    Player.initialize()
    Stats.initialize()
    player = Player()
    stats = Stats()

    for mine in player.mines_completed:
        if mine.boss and mine.boss.name not in stats.defeated_bosses:
            stats.record_boss_defeat(mine.boss.name)

    FileManager.save(stats)

    print("Migration complete. Bestiary backfilled from completed mines.")
