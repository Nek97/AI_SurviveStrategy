import numpy as np
from typing import List, Optional
from src.engine.ecs import Component, Entity

class Transform(Component):
    def __init__(self, x: float, y: float):
        self.x = x
        self.y = y

class Velocity(Component):
    def __init__(self, vx: float = 0.0, vy: float = 0.0):
        self.vx = vx
        self.vy = vy

class IsFood(Component):
    def __init__(self, food_type: str = "agriculture"):
        # "agriculture", "fruit", "animal"
        self.food_type = food_type

class Knowledge(Component):
    def __init__(self):
        self.discovered_recipes = set()



class Inventory(Component):
    def __init__(self):
        self.food_collected = 0
        self.food_types_collected = set()

class Genetics(Component):
    def __init__(self, group_id: int, color: tuple, shape: str, dna_vector: np.ndarray):
        self.group_id = group_id
        # Color (R, G, B) tuple
        self.color = color 
        # Shapes: 'D4', 'D6', 'D8', 'D10', 'D12', 'D20'
        self.shape = shape
        
        # DNA Vector:
        # [0]: Speed (Base multiplier for movement)
        # [1]: Sense Radius (Base multiplier for vision)
        # [2]: Size (Mass/stature)
        # [3]: Altruism (0.0 Egoist, 1.0 Altruist)
        self.dna = dna_vector
        
    @property
    def speed(self) -> float:
        return self.dna[0]
        
    @property
    def sense(self) -> float:
        return self.dna[1]
        
    @property
    def size(self) -> float:
        return self.dna[2]

    @property
    def altruism(self) -> float:
        return self.dna[3]

class LifeCycle(Component):
    def __init__(self):
        # 1: Baby, 3: Adult, 2: Elder
        self.age_level: int = 1
        self.ticks_alive: int = 0
        
        # Hunger is used as Energy (100 = full, 0 = starving)
        self.hunger: float = 100.0
        self.max_hunger: float = 100.0
        self.is_dead: bool = False

class Kinship(Component):
    def __init__(self, parents: Optional[List[Entity]] = None):
        self.parents = parents or []
        self.children = []

class ActionState(Component):
    def __init__(self):
        # 'IDLE', 'MOVING', 'EATING', 'SHARING', 'MATING'
        self.current_action: str = 'IDLE'
        self.action_target: Optional[Entity] = None
        self.face_mood: str = '|'  # ')', '|', '('
