import numpy as np
import random
from typing import List, Dict
from src.engine.ecs import System, Registry, Entity
from src.components.components import Transform, Genetics, LifeCycle, Kinship, ActionState, Velocity, IsFood, Inventory, Knowledge

MAP_WIDTH = 800
MAP_HEIGHT = 600
FOOD_TYPES = ["agriculture", "fruit", "animal"]

def are_allies(g1: Genetics, g2: Genetics) -> bool:
    if g1.group_id == g2.group_id: return True
    diff = abs(g1.dna[0] - g2.dna[0]) + abs(g1.dna[1] - g2.dna[1])
    return diff < 0.15

class EnvironmentSystem(System):
    def __init__(self, scenario: str = "equilibrium"):
        self.scenario = scenario
        self.food_abundance = 1.0
        
        self.utopia_mode = False
        self.mutation_rate = 0.05
        self.cost_of_fighting = 0.5
        self.food_multiplier = 1.5
        
        self.deaths_by_fight = 0
        self.deaths_by_starvation = 0
        self.stop_requested = False
        self.stop_conditions = {
            "one_race": False,
            "extinction": False,
            "pop_50": False,
            "day_100": False
        }
        self.economy_win_enabled = False
        self.winner = None
        self.group_sizes = {}
        
        self._update_scenario(scenario)

    def _update_scenario(self, scenario: str):
        if scenario == "famine":
            self.food_abundance = 0.5
        elif scenario == "abundance":
            self.food_abundance = 2.0
        else:
            self.food_abundance = 1.0

    def update(self, registry: Registry, dt: float):
        agents = registry.get_entities_with(Transform, Genetics, LifeCycle)
        grid = {}
        new_sizes = {}
        
        for agent in agents:
            lc = registry.get_component(agent, LifeCycle)
            if lc.is_dead: continue
            
            t = registry.get_component(agent, Transform)
            g = registry.get_component(agent, Genetics)
            
            new_sizes[g.group_id] = new_sizes.get(g.group_id, 0) + 1
            
            cell_x = int(t.x // 50)
            cell_y = int(t.y // 50)
            cell_key = (cell_x, cell_y)
            
            if cell_key not in grid:
                grid[cell_key] = {}
            if g.group_id not in grid[cell_key]:
                grid[cell_key][g.group_id] = []
            
            grid[cell_key][g.group_id].append((agent, lc))
            
        for cell_key, groups in grid.items():
            for group_id, group_agents in groups.items():
                if len(group_agents) >= 25:
                    for agent, lc in group_agents:
                        lc.is_dead = True
                        self.deaths_by_starvation += 1
                        new_sizes[group_id] -= 1
                        
        self.group_sizes = new_sizes

class MovementSystem(System):
    def update(self, registry: Registry, dt: float):
        entities = registry.get_entities_with(Transform, Velocity, LifeCycle, Genetics)
        
        for e in entities:
            lc = registry.get_component(e, LifeCycle)
            if lc.is_dead or lc.hunger <= 0: continue
            
            t = registry.get_component(e, Transform)
            v = registry.get_component(e, Velocity)
            
            speed_mod = 1.0
            if lc.age_level == 1: speed_mod = 0.4
            elif lc.age_level == 2: speed_mod = 0.6
                
            new_x = t.x + v.vx * dt * speed_mod
            new_y = t.y + v.vy * dt * speed_mod
            
            t.x = new_x
            t.y = new_y
            
            if t.x < 10:
                t.x = 10
                v.vx *= -1
            elif t.x > MAP_WIDTH - 10:
                t.x = MAP_WIDTH - 10
                v.vx *= -1
                
            if t.y < 10:
                t.y = 10
                v.vy *= -1
            elif t.y > MAP_HEIGHT - 10:
                t.y = MAP_HEIGHT - 10
                v.vy *= -1

class VisionSystem(System):
    def update(self, registry: Registry, dt: float):
        agents = registry.get_entities_with(Transform, Velocity, Genetics, ActionState, Inventory, LifeCycle, Kinship)
        foods = registry.get_entities_with(Transform, IsFood)
        
        grid = {}
        for agent in agents:
            if registry.get_component(agent, LifeCycle).is_dead: continue
            t = registry.get_component(agent, Transform)
            g = registry.get_component(agent, Genetics)
            lc = registry.get_component(agent, LifeCycle)
            cell = (int(t.x // 50), int(t.y // 50))
            if cell not in grid: grid[cell] = []
            grid[cell].append((agent, t, g, lc))
            
        for agent in agents:
            lc = registry.get_component(agent, LifeCycle)
            v = registry.get_component(agent, Velocity)
            state = registry.get_component(agent, ActionState)
            
            if lc.is_dead: continue
            
            if lc.hunger <= 0:
                v.vx = 0
                v.vy = 0
                state.current_action = 'EXHAUSTED'
                state.face_mood = 'X'
                continue
                
            t = registry.get_component(agent, Transform)
            g = registry.get_component(agent, Genetics)
            inv = registry.get_component(agent, Inventory)
            kin = registry.get_component(agent, Kinship)
            
            if inv.food_collected >= 2:
                v.vx = 0
                v.vy = 0
                state.current_action = 'FULL'
                state.face_mood = ')'
                continue
                
            # Mood based on energy
            if lc.hunger > 70:
                state.face_mood = ')'
            elif lc.hunger > 30:
                state.face_mood = '|'
            else:
                state.face_mood = '('
            
            cell_x, cell_y = int(t.x // 50), int(t.y // 50)
            
            cohesion_x, cohesion_y = 0.0, 0.0
            separation_x, separation_y = 0.0, 0.0
            ally_count = 0
            
            target_x, target_y = None, None
            min_dist = 999999
            
            # Look for allies to share food with if we have full inventory and high energy
            if inv.food_collected >= 2 and lc.hunger >= 60:
                for cx in [cell_x-1, cell_x, cell_x+1]:
                    for cy in [cell_y-1, cell_y, cell_y+1]:
                        if (cx, cy) in grid:
                            for other, ot, og, olc in grid[(cx, cy)]:
                                if other == agent: continue
                                if are_allies(og, g):
                                    oinv = registry.get_component(other, Inventory)
                                    if olc.hunger < 40 or oinv.food_collected == 0:
                                        dist = (t.x - ot.x)**2 + (t.y - ot.y)**2
                                        if dist < min_dist:
                                            min_dist = dist
                                            target_x, target_y = ot.x, ot.y
                                        
            # Sense Radius logic: between 50 and 300px (squared: 2500 to 90000)
            sense_radius_sq = (50 + (g.sense * 250)) ** 2
            
            # Look for food if hungry or inventory not full
            if target_x is None and (lc.hunger < 60 or inv.food_collected < 2):
                for food in foods:
                    ft = registry.get_component(food, Transform)
                    dist = (t.x - ft.x)**2 + (t.y - ft.y)**2
                    if dist < min_dist and dist < sense_radius_sq:
                        min_dist = dist
                        target_x, target_y = ft.x, ft.y
                        
            # Rob enemies if egoist
            if target_x is None and g.altruism < 0.5 and (lc.hunger < 60 or inv.food_collected < 2):
                for cx in [cell_x-1, cell_x, cell_x+1]:
                    for cy in [cell_y-1, cell_y, cell_y+1]:
                        if (cx, cy) in grid:
                            for other, ot, og, olc in grid[(cx, cy)]:
                                if other == agent: continue
                                if not are_allies(og, g):
                                    oinv = registry.get_component(other, Inventory)
                                    if oinv.food_collected > 0:
                                        dist = (t.x - ot.x)**2 + (t.y - ot.y)**2
                                        if dist < min_dist and dist < sense_radius_sq:
                                            min_dist = dist
                                            target_x, target_y = ot.x, ot.y
            
            # Avoid enemies or gather with allies
            for cx in [cell_x-1, cell_x, cell_x+1]:
                for cy in [cell_y-1, cell_y, cell_y+1]:
                    if (cx, cy) in grid:
                        for other, ot, og, olc in grid[(cx, cy)]:
                            if other == agent: continue
                            
                            dist_sq = (t.x - ot.x)**2 + (t.y - ot.y)**2
                            if dist_sq < 2500:
                                if are_allies(og, g):
                                    ally_count += 1
                                    cohesion_x += ot.x
                                    cohesion_y += ot.y
                                    if dist_sq < 400 and dist_sq > 0:
                                        separation_x += (t.x - ot.x) / dist_sq
                                        separation_y += (t.y - ot.y) / dist_sq
                                else:
                                    if dist_sq < 900 and dist_sq > 0:
                                        separation_x += (t.x - ot.x) / dist_sq
                                        separation_y += (t.y - ot.y) / dist_sq

            flock_vx, flock_vy = 0, 0
            if ally_count > 0:
                cx = (cohesion_x / ally_count) - t.x
                cy = (cohesion_y / ally_count) - t.y
                cl = np.sqrt(cx**2 + cy**2)
                if cl > 0:
                    flock_vx += (cx/cl) * 10
                    flock_vy += (cy/cl) * 10
            
            flock_vx += separation_x * 50
            flock_vy += separation_y * 50

            if target_x is not None:
                dx = target_x - t.x
                dy = target_y - t.y
                dist = np.sqrt(dx**2 + dy**2)
                if dist > 0:
                    speed = 20 + (g.speed * 150)
                    v.vx = (dx / dist) * speed + flock_vx
                    v.vy = (dy / dist) * speed + flock_vy
                state.current_action = 'MOVING'
            else:
                if random.random() < 0.05:
                    speed = 10 + (g.speed * 80)
                    current_speed = np.sqrt(v.vx**2 + v.vy**2)
                    if current_speed > 0.1:
                        current_angle = np.arctan2(v.vy, v.vx)
                        # 180 degrees cone (-90 to +90 degrees from current trajectory)
                        angle = current_angle + random.uniform(-np.pi/2, np.pi/2)
                    else:
                        angle = random.uniform(0, 2 * np.pi)
                    v.vx = np.cos(angle) * speed + flock_vx
                    v.vy = np.sin(angle) * speed + flock_vy
                else:
                    v.vx += flock_vx * 0.05
                    v.vy += flock_vy * 0.05
                state.current_action = 'IDLE'

            current_speed = np.sqrt(v.vx**2 + v.vy**2)
            max_s = 20 + (g.speed * 150)
            if current_speed > max_s:
                v.vx = (v.vx / current_speed) * max_s
                v.vy = (v.vy / current_speed) * max_s

class InteractionSystem(System):
    def update(self, registry: Registry, dt: float):
        agents = registry.get_entities_with(Transform, Velocity, Inventory, ActionState, LifeCycle, Genetics)
        foods = registry.get_entities_with(Transform, IsFood)
        env = self.env_system
        
        foods_to_destroy = []
        
        # 1. Resolving food consumption on ground
        for food in foods:
            ft = registry.get_component(food, Transform)
            food_comp = registry.get_component(food, IsFood)
            
            touching_agents = []
            for agent in agents:
                lc = registry.get_component(agent, LifeCycle)
                if lc and lc.is_dead: continue
                t = registry.get_component(agent, Transform)
                if (t.x - ft.x)**2 + (t.y - ft.y)**2 < 144:
                    touching_agents.append(agent)
                    
            if len(touching_agents) > 0:
                # Decide who gets it
                winner = touching_agents[0]
                if len(touching_agents) > 1:
                    a1, a2 = touching_agents[0], touching_agents[1]
                    gen1 = registry.get_component(a1, Genetics)
                    gen2 = registry.get_component(a2, Genetics)
                    lc1 = registry.get_component(a1, LifeCycle)
                    lc2 = registry.get_component(a2, LifeCycle)
                    
                    if are_allies(gen1, gen2):
                        winner = a1 if lc1.hunger < lc2.hunger else a2
                    else:
                        size_diff = gen1.size - gen2.size
                        p_win1 = max(0.0, min(1.0, 0.40 + (size_diff * 0.20)))
                        p_win2 = max(0.0, min(1.0, 0.40 - (size_diff * 0.20)))
                        
                        roll = random.random()
                        if roll < p_win1:
                            winner = a1
                            if random.random() < env.cost_of_fighting:
                                registry.get_component(a2, LifeCycle).is_dead = True
                                env.deaths_by_fight += 1
                        elif roll < p_win1 + p_win2:
                            winner = a2
                            if random.random() < env.cost_of_fighting:
                                registry.get_component(a1, LifeCycle).is_dead = True
                                env.deaths_by_fight += 1
                        else:
                            winner = a1 if random.random() < 0.5 else a2
                if not registry.get_component(winner, LifeCycle).is_dead:
                    self.consume_or_collect_food(registry, winner, food_comp)
                    foods_to_destroy.append(food)
                    
        for f in set(foods_to_destroy):
            registry.destroy_entity(f)
            
        # 2. Agent updates (energy depletion, eating from inventory, sharing, raiding)
        for agent in agents:
            lc = registry.get_component(agent, LifeCycle)
            if lc and lc.is_dead: continue
            
            g = registry.get_component(agent, Genetics)
            inv = registry.get_component(agent, Inventory)
            t = registry.get_component(agent, Transform)
            
            # Energy depletion (based on time and traits)
            energy_cost = (0.2 + g.speed**2 + (g.sense * 0.5) + g.size**3) * dt * 2.5
            lc.hunger -= energy_cost
            
            if lc.hunger <= 0:
                lc.hunger = 0
                continue
                

            # Interactions with other agents
            for other in agents:
                if other == agent: continue
                olc = registry.get_component(other, LifeCycle)
                if olc and olc.is_dead: continue
                
                ot = registry.get_component(other, Transform)
                if (t.x - ot.x)**2 + (t.y - ot.y)**2 < 144:
                    og = registry.get_component(other, Genetics)
                    oinv = registry.get_component(other, Inventory)
                    
                    if are_allies(g, og):
                        # Sharing
                        if inv.food_collected > 0 and (olc.hunger < 40 or oinv.food_collected == 0) and inv.food_collected > oinv.food_collected:
                            inv.food_collected -= 1
                            if olc.hunger < 60:
                                olc.hunger = min(100.0, olc.hunger + 40.0)
                            else:
                                oinv.food_collected += 1
                    else:
                        # Combat / Raiding
                        if g.altruism < 0.5 and oinv.food_collected > 0 and (lc.hunger < 60 or inv.food_collected < 2):
                            size_diff = g.size - og.size
                            p_win = max(0.0, min(1.0, 0.40 + (size_diff * 0.20)))
                            p_lose = max(0.0, min(1.0, 0.40 - (size_diff * 0.20)))
                            
                            roll = random.random()
                            if roll < p_win:
                                if random.random() < env.cost_of_fighting:
                                    olc.is_dead = True
                                    env.deaths_by_fight += 1
                                stole = min(2 - inv.food_collected, oinv.food_collected)
                                oinv.food_collected -= stole
                                inv.food_collected += stole
                            elif roll < p_win + p_lose:
                                if random.random() < env.cost_of_fighting:
                                    lc.is_dead = True
                                    env.deaths_by_fight += 1
                            
                            break

    def consume_or_collect_food(self, registry: Registry, agent: Entity, food_comp: IsFood):
        inv = registry.get_component(agent, Inventory)
        
        if inv.food_collected < 2:
            inv.food_collected += 1

class DayNightSystem(System):
    def __init__(self):
        self.day_length = 300
        self.current_tick = 0
        self.days_passed = 0
        
    def spawn_food(self, registry: Registry, amount: int):
        for _ in range(amount):
            e = registry.create_entity()
            x = random.uniform(50, MAP_WIDTH-50)
            y = random.uniform(50, MAP_HEIGHT-50)
            registry.add_component(e, Transform(x, y))
            registry.add_component(e, IsFood(food_type=random.choice(FOOD_TYPES)))

    def update(self, registry: Registry, dt: float):
        self.current_tick += 1
        env = self.env_system
        
        agents = registry.get_entities_with(Genetics, Inventory, LifeCycle)
        
        # Fast-forward day if everyone is done
        if agents:
            all_done = True
            for agent in agents:
                lc = registry.get_component(agent, LifeCycle)
                if lc.is_dead: continue
                inv = registry.get_component(agent, Inventory)
                if inv.food_collected < 2 and lc.hunger > 0:
                    all_done = False
                    break
            
            if all_done:
                self.current_tick = self.day_length
        
        if self.current_tick >= self.day_length:
            self.current_tick = 0
            self.days_passed += 1
            
            agents = registry.get_entities_with(Genetics, Inventory, LifeCycle)
            
            survivors = []
            alive_count = 0
            
            for agent in agents:
                lc = registry.get_component(agent, LifeCycle)
                if lc.is_dead: 
                    registry.destroy_entity(agent)
                    continue
                    
                alive_count += 1
                inv = registry.get_component(agent, Inventory)
                g = registry.get_component(agent, Genetics)
                
                lc.ticks_alive += self.day_length
                if lc.ticks_alive < 300: lc.age_level = 1
                elif lc.ticks_alive > 3000: lc.age_level = 2
                else: lc.age_level = 3
                
                # Primer Rule: 0 food = die, 1 = survive, 2 = reproduce
                if inv.food_collected == 0:
                    lc.is_dead = True
                    env.deaths_by_starvation += 1
                    registry.destroy_entity(agent)
                else:
                    survivors.append(agent)
                    lc.hunger = 100.0 # reset energy for new day
                    
                    if inv.food_collected >= 2:
                        # Reproduce
                        if env.group_sizes.get(g.group_id, 0) < 60:
                            self.reproduce(registry, agent, env.mutation_rate)
                            env.group_sizes[g.group_id] = env.group_sizes.get(g.group_id, 0) + 1
                            
                    inv.food_collected = 0 # reset inventory
            
            active_groups = [g for g, size in env.group_sizes.items() if size > 0]
            
            if env.stop_conditions.get("extinction") and alive_count == 0:
                env.stop_requested = True
                env.winner = "Extinction (0 alive)"
                
            if env.stop_conditions.get("one_race") and self.days_passed > 0 and len(active_groups) == 1:
                env.stop_requested = True
                env.winner = f"Group {active_groups[0]} is the sole survivor"
                
            if env.stop_conditions.get("day_100") and self.days_passed >= 100:
                env.stop_requested = True
                env.winner = f"Reached Day 100"
                
            if env.stop_conditions.get("pop_50"):
                for g, size in env.group_sizes.items():
                    if size >= 50:
                        env.stop_requested = True
                        env.winner = f"Group {g} reached 50 population"
                        break
                    
            foods = registry.get_entities_with(IsFood)
            for f in foods:
                registry.destroy_entity(f)
                
            base_food = len(survivors)
            total_food = int(base_food * env.food_abundance * env.food_multiplier) + 5
            self.spawn_food(registry, total_food)
            
    def reproduce(self, registry: Registry, parent: Entity, mutation_rate: float):
        gen = registry.get_component(parent, Genetics)
        pos = registry.get_component(parent, Transform)
        pk = registry.get_component(parent, Knowledge)
        
        child_dna = gen.dna + np.random.normal(0, mutation_rate, size=gen.dna.shape)
        child_dna = np.clip(child_dna, 0.0, 1.0)
        
        child = registry.create_entity()
        registry.add_component(child, Genetics(gen.group_id, gen.color, gen.shape, child_dna))
        
        lifecycle = LifeCycle()
        lifecycle.age_level = 1
        lifecycle.ticks_alive = 0
        registry.add_component(child, lifecycle)
        
        registry.add_component(child, Kinship(parents=[parent]))
        registry.add_component(child, ActionState())
        registry.add_component(child, Inventory())
        registry.add_component(child, Velocity(0.0, 0.0))
        registry.add_component(child, Transform(pos.x + random.uniform(-20, 20), pos.y + random.uniform(-20, 20)))
        
        child_k = Knowledge()
        child_k.discovered_recipes = set(pk.discovered_recipes)
        registry.add_component(child, child_k)

class GeneticsSystem(System): pass
class HungerSystem(System): pass
class DecisionSystem(System): pass

