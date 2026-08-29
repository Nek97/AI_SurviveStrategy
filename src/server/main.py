import asyncio
import json
import random
import numpy as np
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from pydantic import BaseModel

from src.engine.ecs import Registry
from src.components.components import Transform, Genetics, LifeCycle, Kinship, ActionState, Velocity, IsFood, Inventory, Knowledge
from src.components.components import Transform, Genetics, LifeCycle, Kinship, ActionState, Velocity, IsFood, Inventory, Knowledge
from src.systems.systems import EnvironmentSystem, MovementSystem, VisionSystem, InteractionSystem, DayNightSystem
from src.engine.config import ALLEGORICAL_GROUPS

app = FastAPI()

import os
os.makedirs("src/web", exist_ok=True)
app.mount("/static", StaticFiles(directory="src/web"), name="static")

@app.get("/")
def get_index():
    return FileResponse("src/web/index.html")

class Simulation:
    def __init__(self):
        self.registry = Registry()
        self.running = False
        
        self.env_system = EnvironmentSystem()
        self.move_system = MovementSystem()
        self.vision_system = VisionSystem()
        self.interact_system = InteractionSystem()
        self.interact_system.env_system = self.env_system
        self.day_night_system = DayNightSystem()
        self.day_night_system.env_system = self.env_system
        
        self.clients = []
        self.history = {}
        self.groups_info = {}
        
        self.speed_modifier = 1.0

    def spawn_group(self, group_id: int, count: int, dna: list, color: tuple, shape: str):
        self.groups_info[group_id] = color
        dna_arr = np.array(dna)
        
        # Center of the colony
        center_x = random.uniform(100, 700)
        center_y = random.uniform(100, 500)
        
        # We assume count is 20 for default.
        # Ages: 5 grandparents (age 2), 7 parents (age 3), 8 children (age 1)
        
        grandparents = []
        parents = []
        children = []
        
        for i in range(count):
            e = self.registry.create_entity()
            self.registry.add_component(e, Transform(center_x + random.uniform(-40, 40), center_y + random.uniform(-40, 40)))
            self.registry.add_component(e, Velocity(0.0, 0.0))
            self.registry.add_component(e, Genetics(group_id, color, shape, dna_arr))
            
            lifecycle = LifeCycle()
            if i < 5:
                lifecycle.age_level = 2
                lifecycle.ticks_alive = 4000
                grandparents.append(e)
            elif i < 12:
                lifecycle.age_level = 3
                lifecycle.ticks_alive = 500
                parents.append(e)
            else:
                lifecycle.age_level = 1
                lifecycle.ticks_alive = 0
                children.append(e)
                
            self.registry.add_component(e, lifecycle)
            self.registry.add_component(e, ActionState())
            self.registry.add_component(e, Inventory())
            self.registry.add_component(e, Knowledge())
            
        # Assign kinship (children to random parents)
        for c in children:
            if parents:
                parent = random.choice(parents)
                self.registry.add_component(c, Kinship(parents=[parent]))
            else:
                self.registry.add_component(c, Kinship())
        
        for a in grandparents + parents:
            self.registry.add_component(a, Kinship())

    async def broadcast_state(self):
        state = self._serialize_state()
        for client in self.clients:
            try:
                await client.send_text(state)
            except:
                self.clients.remove(client)

    async def run_loop(self):
        self.running = True
        dt = 0.1 
        
        if len(self.registry.get_entities_with(IsFood)) == 0:
            self.day_night_system.spawn_food(self.registry, 100)
        
        while self.running:
            self.step_logic(dt)
            await self.broadcast_state()
            
            if self.env_system.stop_requested:
                self.running = False
                self.env_system.stop_requested = False
                await self.broadcast_history()
                break
                
            sleep_time = dt / self.speed_modifier
            await asyncio.sleep(sleep_time)

    def step_logic(self, dt):
        prev_day = self.day_night_system.days_passed
        self.vision_system.update(self.registry, dt)
        self.move_system.update(self.registry, dt)
        self.interact_system.update(self.registry, dt)
        self.env_system.update(self.registry, dt)
        self.day_night_system.update(self.registry, dt)
        
        if self.day_night_system.days_passed > prev_day:
            self.record_history()

    async def fast_forward(self, days: int):
        target_day = self.day_night_system.days_passed + days
        dt = 0.1
        while self.day_night_system.days_passed < target_day:
            self.step_logic(dt)
            if self.env_system.stop_requested:
                self.running = False
                self.env_system.stop_requested = False
                break
        self.record_history()
        await self.broadcast_state()

    def record_history(self):
        counts = {}
        total_altruism = 0
        total_agents = 0
        
        traits = []
        
        for e in self.registry.get_entities_with(Genetics, LifeCycle):
            g = self.registry.get_component(e, Genetics)
            l = self.registry.get_component(e, LifeCycle)
            if not l.is_dead:
                counts[g.group_id] = counts.get(g.group_id, 0) + 1
                total_altruism += g.altruism
                total_agents += 1
                traits.append({
                    "speed": g.speed,
                    "sense": g.sense,
                    "size": g.size,
                    "altruism": g.altruism,
                    "group": g.group_id
                })
                
        avg_altruism = total_altruism / total_agents if total_agents > 0 else 0
        
        self.history[self.day_night_system.days_passed] = {
            "counts": counts,
            "avg_altruism": avg_altruism,
            "deaths_starvation": self.env_system.deaths_by_starvation,
            "deaths_fight": self.env_system.deaths_by_fight,
            "traits": traits
        }
        
        self.env_system.deaths_by_starvation = 0
        self.env_system.deaths_by_fight = 0

    def get_history_payload(self):
        return json.dumps({
            "type": "HISTORY",
            "history": self.history,
            "groups": self.groups_info,
            "winner": getattr(self.env_system, 'winner', None)
        })
        
    async def broadcast_history(self):
        payload = self.get_history_payload()
        for client in self.clients:
            try:
                await client.send_text(payload)
            except:
                pass

    def _serialize_state(self):
        agents_data = []
        for e in self.registry.get_entities_with(Transform, Velocity, Genetics, LifeCycle, ActionState):
            t = self.registry.get_component(e, Transform)
            v = self.registry.get_component(e, Velocity)
            g = self.registry.get_component(e, Genetics)
            l = self.registry.get_component(e, LifeCycle)
            a = self.registry.get_component(e, ActionState)
            
            if l.is_dead: continue
                
            agents_data.append({
                "id": e, "x": t.x, "y": t.y, "vx": v.vx, "vy": v.vy,
                "color": f"rgb({g.color[0]},{g.color[1]},{g.color[2]})",
                "shape": g.shape, "age": l.age_level,
                "face": a.face_mood,
                "size": g.size
            })
            
        foods_data = []
        for e in self.registry.get_entities_with(Transform, IsFood):
            t = self.registry.get_component(e, Transform)
            f = self.registry.get_component(e, IsFood)
            foods_data.append({"x": t.x, "y": t.y, "type": f.food_type})
            
            
        return json.dumps({
            "type": "STATE",
            "day": self.day_night_system.days_passed,
            "scenario": self.env_system.scenario,
            "agents": agents_data,
            "foods": foods_data
        })

sim = Simulation()

@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    await websocket.accept()
    sim.clients.append(websocket)
    try:
        await websocket.send_text(sim._serialize_state())
        
        while True:
            data = await websocket.receive_text()
            cmd = json.loads(data)
            if cmd["type"] == "START":
                if not sim.running:
                    asyncio.create_task(sim.run_loop())
            elif cmd["type"] == "STOP":
                sim.running = False
                await websocket.send_text(sim.get_history_payload())
            elif cmd["type"] == "ADD_GROUP":
                cfg = cmd["config"]
                sim.spawn_group(cfg["id"], cfg["count"], cfg["dna"], tuple(cfg["color"]), cfg["shape"])
                await sim.broadcast_state() 
            elif cmd["type"] == "SET_SCENARIO":
                sim.env_system._update_scenario(cmd["scenario"])
            elif cmd["type"] == "SET_SPEED":
                sim.speed_modifier = float(cmd["speed"])
            elif cmd["type"] == "SET_GLOBAL_CFG":
                cfg = cmd["config"]
                if "food_multiplier" in cfg:
                    sim.env_system.food_multiplier = float(cfg["food_multiplier"])
                if "mutation_rate" in cfg:
                    sim.env_system.mutation_rate = float(cfg["mutation_rate"])
                if "cost_of_fighting" in cfg:
                    sim.env_system.cost_of_fighting = float(cfg["cost_of_fighting"])
                if "utopia_mode" in cfg:
                    sim.env_system.utopia_mode = bool(cfg["utopia_mode"])
            elif cmd["type"] == "SET_STOP_CONDITIONS":
                cfg = cmd["config"]
                if "one_race" in cfg: sim.env_system.stop_conditions["one_race"] = bool(cfg["one_race"])
                if "extinction" in cfg: sim.env_system.stop_conditions["extinction"] = bool(cfg["extinction"])
                if "pop_50" in cfg: sim.env_system.stop_conditions["pop_50"] = bool(cfg["pop_50"])
                if "day_100" in cfg: sim.env_system.stop_conditions["day_100"] = bool(cfg["day_100"])

            elif cmd["type"] == "LOAD_SCENARIO":
                sim.running = False
                sim.registry = Registry()
                sim.history = {}
                sim.groups_info = {}
                sim.day_night_system.days_passed = 0
                sim.day_night_system.current_tick = 0
                sim.env_system.winner = None
                
                if cmd["scenario"] == "bears_vs_fists":
                    # Share-Bears
                    sim.spawn_group(1, 20, [0.9, 0.4, 0.8, 0.5, 0.5], (0, 0, 255), "D20")
                    # Iron-Fists
                    sim.spawn_group(2, 20, [0.1, 0.6, 0.8, 0.5, 0.5], (255, 0, 0), "D4")
                elif cmd["scenario"] == "all_vs_all":
                    sim.spawn_group(1, 15, [0.9, 0.4, 0.8, 0.5, 0.5], (0, 0, 255), "D20")
                    sim.spawn_group(2, 15, [0.5, 0.9, 0.8, 0.5, 0.5], (0, 255, 0), "D6")
                    sim.spawn_group(3, 15, [0.1, 0.6, 0.8, 0.5, 0.5], (255, 0, 0), "D4")
                    sim.spawn_group(4, 15, [0.3, 0.8, 0.8, 0.5, 0.5], (255, 136, 0), "D8")
                elif cmd["scenario"] == "lone_wolf_vs_pack":
                    # Giant Iron-Fists (few but strong, fast, good sense)
                    sim.spawn_group(1, 3, [0.1, 0.8, 1.0, 0.8, 0.8], (200, 0, 0), "D4")
                    # Tiny Share-Bears (many, small, slow)
                    sim.spawn_group(2, 40, [0.9, 0.3, 0.2, 0.3, 0.4], (0, 100, 255), "D20")
                elif cmd["scenario"] == "the_hive_awakens":
                    # Two distinct hives fighting for dominance
                    sim.spawn_group(1, 25, [1.0, 0.7, 0.6, 0.5, 0.7], (128, 0, 128), "D12")
                    sim.spawn_group(2, 25, [1.0, 0.7, 0.6, 0.5, 0.7], (0, 128, 128), "D12")
                elif cmd["scenario"] == "traders_vs_workers":
                    # Efficiency vs Trade
                    sim.spawn_group(1, 20, [0.5, 0.9, 0.5, 0.6, 0.6], (0, 255, 0), "D6")
                    sim.spawn_group(2, 20, [0.3, 0.8, 0.5, 0.6, 0.6], (255, 136, 0), "D8")
                elif cmd["scenario"] == "survival_of_the_fittest":
                    for i in range(1, 6):
                        sim.spawn_group(
                            i, 10, 
                            [random.random(), random.random(), random.random(), random.random(), random.random()], 
                            (random.randint(50,255), random.randint(50,255), random.randint(50,255)), 
                            random.choice(["D4", "D6", "D8", "D12", "D20"])
                        )
                    
                await sim.broadcast_state()
            elif cmd["type"] == "FAST_FORWARD":
                await sim.fast_forward(cmd["days"])
                await websocket.send_text(sim.get_history_payload())
    except WebSocketDisconnect:
        sim.clients.remove(websocket)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
