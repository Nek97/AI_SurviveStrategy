import json
import numpy as np
import os
import random
from src.engine.ecs import Registry
from src.components.components import Transform, Genetics, LifeCycle, Kinship, ActionState, Velocity, Inventory
from src.systems.systems import EnvironmentSystem, MovementSystem, VisionSystem, InteractionSystem, DayNightSystem
from src.engine.config import ALLEGORICAL_GROUPS

def run_single_simulation(scenario: str, groups_to_spawn: list, days_to_run: int = 15) -> dict:
    registry = Registry()
    
    env_system = EnvironmentSystem(scenario)
    move_system = MovementSystem()
    vision_system = VisionSystem()
    interact_system = InteractionSystem()
    day_night_system = DayNightSystem()
    day_night_system.env_system = env_system
    
    # Initial food
    day_night_system.spawn_food(registry, 100)
    
    # Spawn groups
    for i, group_name in enumerate(groups_to_spawn):
        group_cfg = ALLEGORICAL_GROUPS[group_name]
        dna_arr = np.array(group_cfg["dna"])
        color = group_cfg["color"]
        shape = group_cfg["shape"]
        
        for _ in range(20): # 20 entities per group for faster sim
            e = registry.create_entity()
            registry.add_component(e, Transform(random.uniform(50, 750), random.uniform(50, 550)))
            registry.add_component(e, Velocity(0.0, 0.0))
            registry.add_component(e, Genetics(i+1, color, shape, dna_arr))
            
            lifecycle = LifeCycle()
            lifecycle.age_level = 3
            registry.add_component(e, lifecycle)
            registry.add_component(e, Kinship())
            registry.add_component(e, ActionState())
            registry.add_component(e, Inventory())
            
    # Run loop
    dt = 0.1
    # days_to_run * 300 ticks per day
    total_ticks = days_to_run * day_night_system.day_length
    
    for _ in range(total_ticks):
        vision_system.update(registry, dt)
        move_system.update(registry, dt)
        interact_system.update(registry, dt)
        day_night_system.update(registry, dt)

    # Collect stats
    alive_entities = [e for e in registry.get_entities_with(Genetics, LifeCycle) 
                      if not registry.get_component(e, LifeCycle).is_dead]
    
    group_survivors = {name: 0 for name in groups_to_spawn}
    total_altruism = 0
    mixed_breeds = 0
    
    for e in alive_entities:
        gen = registry.get_component(e, Genetics)
        total_altruism += gen.altruism
        
        # Determine closest original group by color distance
        min_dist = float('inf')
        closest_group = None
        for name in groups_to_spawn:
            orig_color = np.array(ALLEGORICAL_GROUPS[name]["color"])
            dist = np.linalg.norm(np.array(gen.color) - orig_color)
            if dist < min_dist:
                min_dist = dist
                closest_group = name
                
        if min_dist > 50: 
            mixed_breeds += 1
        else:
            group_survivors[closest_group] += 1
            
    avg_altruism = total_altruism / len(alive_entities) if alive_entities else 0
    
    return {
        "survivors_by_group": group_survivors,
        "mixed_breeds": mixed_breeds,
        "total_survivors": len(alive_entities),
        "average_altruism": avg_altruism
    }

def run_mass_simulation(runs_per_scenario=2, days_to_run=15):
    scenarios = ["equilibrium", "abundance", "famine"]
    all_groups = list(ALLEGORICAL_GROUPS.keys())
    
    results = {}
    os.makedirs("data", exist_ok=True)
    
    for scenario in scenarios:
        print(f"Running scenario: {scenario}")
        scenario_results = []
        for i in range(runs_per_scenario):
            print(f"  Run {i+1}/{runs_per_scenario}...")
            # Run all groups competing against each other
            res = run_single_simulation(scenario, all_groups, days_to_run=days_to_run)
            scenario_results.append(res)
        results[scenario] = scenario_results
        
    with open("data/simulation_results.json", "w") as f:
        json.dump(results, f, indent=2)
    print("Mass simulation complete. Data saved to data/simulation_results.json.")

if __name__ == "__main__":
    # In order to let the user test quickly, we run 2 iterations per scenario
    run_mass_simulation(2, 10)
