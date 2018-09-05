import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PROBE, PYLON

class DiagnosticBot(sc2.BotAI):
    def __init__(self):
        self.PYLON_COUNT = 0

    async def on_step(self, iteration):
        nexuses = self.units(NEXUS)
        pylons = self.units(PYLON)

        if pylons.amount > self.PYLON_COUNT:
            self.PYLON_COUNT = pylons.amount
            
            for nexus in nexuses:
                await chat_send("Nexus: " + nexus)

            for pylon in pylons:
                await chat_send("Pylon: " + pylon)

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, DiagnosticBot()),
    Computer(Race.Terran, Difficulty.Easy)
], realtime=True)
