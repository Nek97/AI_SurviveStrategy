import json
import numpy as np
import time
from src.engine.ecs import Registry
from src.components.components import Transform, Genetics, LifeCycle, Kinship, ActionState
from src.systems.systems import EnvironmentSystem, HungerSystem, GeneticsSystem, DecisionSystem

def run_headless_simulation(eras: int = 100):
    registry = Registry()
    
    # Init Systems
    env_system = EnvironmentSystem("abundance")
    hunger_system = HungerSystem()
    genetics_system = GeneticsSystem()
    decision_system = DecisionSystem()
    
    # Spawn initial group
    print("Spawning initial group of 100 entities...")
    for i in range(100):
        e = registry.create_entity()
        registry.add_component(e, Transform(np.random.uniform(0, 800), np.random.uniform(0, 600)))
        
        # DNA: [Altruism, Efficiency, Exploration, Reproduction, Speed]
        dna = np.array([0.8, 0.5, 0.5, 0.5, 0.5])
        registry.add_component(e, Genetics(group_id=1, color=(50, 200, 50), shape="D6", dna_vector=dna))
        
        lifecycle = LifeCycle()
        lifecycle.age_level = 3
        registry.add_component(e, lifecycle)
        registry.add_component(e, Kinship())
        registry.add_component(e, ActionState())

    print(f"Running simulation for {eras} eras...")
    start_time = time.time()
    
    for era in range(eras):
        dt = 0.1
        decision_system.update(registry, dt)
        hunger_system.update(registry, dt)
        
        # Simple report every 10 eras
        if era % 10 == 0:
            alive = len([e for e in registry.get_entities_with(LifeCycle) if not registry.get_component(e, LifeCycle).is_dead])
            print(f"Era {era}: {alive} entities alive.")

    end_time = time.time()
    
    alive_count = len([e for e in registry.get_entities_with(LifeCycle) if not registry.get_component(e, LifeCycle).is_dead])
    print(f"\nSimulation complete in {end_time - start_time:.2f} seconds.")
    print(f"Final alive count: {alive_count}")
    
if __name__ == "__main__":
    run_headless_simulation(100)
