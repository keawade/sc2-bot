import sc2
from sc2 import run_game, maps, Race, Difficulty
from sc2.player import Bot, Computer
from sc2.constants import NEXUS, PYLON, ASSIMILATOR, CYBERNETICSCORE, GATEWAY, STARGATE
from sc2.constants import PROBE, STALKER, ZEALOT, VOIDRAY

import random

# TODO: Expand to separate files

class CredBot(sc2.BotAI):
    def __init__(self):
        self.ITERATIONS_PER_MINUTE = 165
        self.MAX_WORKERS = 50

    async def on_step(self, iteration): # What to do every step
        # Update iteration tracker (timer)
        self.iteration = iteration

        await self.distribute_workers() # in sc2/bot_ai.py
        await self.build_workers()
        await self.build_pylons()
        await self.build_assimilators()
        await self.expand()
        await self.offensive_force_buildings()
        await self.build_offensive_force()
        # TODO: Scout for bases/enemies
        await self.attack()

    # TODO: Prioritize building units over structures in the early game
    # TODO: Identify front/rear of base
    # TODO: Rally units to the front of the base
    # TODO: Garbage collect queued (but not constructing) units?

    async def build_workers(self):
        # TODO: Refine the 16 Probes per Nexus calculation. Should be based on how many mineral nodes and assimilators are available near nexuses.
        # TODO: Check for queued probes as well?
        if len(self.units(NEXUS) * 16) > len(self.units(PROBE)) and len (self.units(PROBE)) < self.MAX_WORKERS:
            for nexus in self.units(NEXUS).ready.noqueue:
                if self.can_afford(PROBE):
                    await self.do(nexus.train(PROBE))

    async def build_pylons(self):
        # TODO: Don't build between the nexus and the resouces!
        # TODO: Check queued unit construction as well as existing supply use
        # TODO: Spread pylons (Need to have forward/side/rear pylons to select!)
        if self.supply_left < 5 and not self.already_pending(PYLON):
            nexuses = self.units(NEXUS).ready
            if nexuses.exists:
                if self.can_afford(PYLON):
                    # TODO: Distribute pylons better
                    await self.build(PYLON, near=nexuses.random)

    async def expand(self):
        # TODO: Keep expanding as mineral nodes expire
        if self.units(NEXUS).amount < self.get_minute(self.iteration) and self.can_afford(NEXUS):
            await self.expand_now()

    async def build_assimilators(self):
        for nexus in self.units(NEXUS).ready:
            if self.units(ASSIMILATOR).amount < self.get_minute(self.iteration) / 2 and self.can_afford(ASSIMILATOR):
                # TODO: Check existing assimilator count?
                # Range 25 was a bit too far. Ended up building in other bases and things got weird when workers got distributed
                geysers = self.state.vespene_geyser.closer_than(15.0, nexus)
                for geyser in geysers:
                    if not self.can_afford(ASSIMILATOR):
                        break
                    worker = self.select_build_worker(geyser.position)
                    if worker is None:
                        break
                    if not self.units(ASSIMILATOR).closer_than(1.0, geyser).exists:
                        await self.do(worker.build(ASSIMILATOR, geyser))

    async def offensive_force_buildings(self):
        # TODO: Add a maximum count of buildings as a function of available mineral nodes
        # TODO: Build a Robotics Facility to build an observer
        # TODO: Avoid building between a Nexus and its resources
        if self.units(PYLON).ready.exists:
            if self.units(GATEWAY).ready.exists and not self.units(CYBERNETICSCORE):
                if self.can_afford(CYBERNETICSCORE) and not self.already_pending(CYBERNETICSCORE):
                    # TODO: Select rear pylons for cybernetics core
                    pylon = self.units(PYLON).ready.random
                    await self.build(CYBERNETICSCORE, near=pylon)

            # Limits gateways to roughly one per minute
            elif len(self.units(GATEWAY)) < self.get_minute(self.iteration) / 2:
                if self.units(GATEWAY).amount < 4 and self.can_afford(GATEWAY) and not self.already_pending(GATEWAY):
                    # TODO: Select forward pylons for gateways
                    pylon = self.units(PYLON).ready.random
                    await self.build(GATEWAY, near=pylon)

            if self.units(CYBERNETICSCORE).ready.exists:
                if len(self.units(STARGATE)) < self.get_minute(self.iteration) / 2:
                    if self.can_afford(STARGATE) and not self.already_pending(STARGATE):
                        # TODO: Select rear or side pylons for stargates
                        pylon = self.units(PYLON).ready.random
                        await self.build(STARGATE, near=pylon)

    async def build_offensive_force(self):
        # TODO: Set martial point
        # TODO: Build zealots?
        for gw in self.units(GATEWAY).ready.noqueue:
            # Prioritize stalkers over voidrays
            if not self.units(STALKER).amount > self.units(VOIDRAY).amount:
                if self.can_afford(STALKER) and self.supply_left > 0:
                    await self.do(gw.train(STALKER))
        
        for sg in self.units(STARGATE).ready.noqueue:
            if self.can_afford(VOIDRAY) and self.supply_left > 0:
                await self.do(sg.train(VOIDRAY))

    async def attack(self):
        # {
        #   UNIT: [FIGHT, DEFEND],
        # }
        aggresive_units = {
            STALKER: [15, 5],
            VOIDRAY: [8, 3],
        }

        for UNIT in aggresive_units:
            if self.units(UNIT).amount > aggresive_units[UNIT][0] and self.units(UNIT).amount > aggresive_units[UNIT][1]:
                for u in self.units(UNIT).idle:
                    await self.do(u.attack(self.find_target(self.state)))

            elif self.units(UNIT).amount > aggresive_units[UNIT][1]:
                if len(self.known_enemy_units) > 0:
                    for u in self.units(UNIT).idle:
                        await self.do(u.attack(random.choice(self.known_enemy_units)))

    def find_target(self, state):
        # TODO: Prioritize buildings if they aren't defended?
        # TODO: Defensive patrol?
        if len(self.known_enemy_units) > 0:
            # TODO: Choose closest
            return random.choice(self.known_enemy_units)
        
        elif len(self.known_enemy_structures) > 0:
            # TODO: Choose closest
            return random.choice(self.known_enemy_structures)

        else:
            # TODO: Don't just run to the top left corner on four start maps
            return self.enemy_start_locations[0]

    def get_minute(self, iteration):
        return iteration / self.ITERATIONS_PER_MINUTE

run_game(maps.get("AbyssalReefLE"), [
    Bot(Race.Protoss, CredBot()),
    Computer(Race.Terran, Difficulty.Hard)
], realtime=False)
