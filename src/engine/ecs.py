from typing import Type, TypeVar, Dict, Any, List

C = TypeVar('C')

class Component:
    pass

class Entity(int):
    pass

class Registry:
    def __init__(self):
        self._next_entity_id = 0
        self._components: Dict[Type[Component], Dict[Entity, Component]] = {}
        self._entities: set = set()

    def create_entity(self) -> Entity:
        entity = Entity(self._next_entity_id)
        self._next_entity_id += 1
        self._entities.add(entity)
        return entity

    def destroy_entity(self, entity: Entity):
        if entity in self._entities:
            self._entities.remove(entity)
            for comp_dict in self._components.values():
                if entity in comp_dict:
                    del comp_dict[entity]

    def add_component(self, entity: Entity, component: Component):
        comp_type = type(component)
        if comp_type not in self._components:
            self._components[comp_type] = {}
        self._components[comp_type][entity] = component

    def remove_component(self, entity: Entity, comp_type: Type[C]):
        if comp_type in self._components and entity in self._components[comp_type]:
            del self._components[comp_type][entity]

    def get_component(self, entity: Entity, comp_type: Type[C]) -> C | None:
        if comp_type in self._components:
            return self._components[comp_type].get(entity)
        return None

    def get_entities_with(self, *comp_types: Type[Component]) -> List[Entity]:
        if not comp_types:
            return []
        
        # Start with entities having the first component
        first_comp = comp_types[0]
        if first_comp not in self._components:
            return []
            
        entities = set(self._components[first_comp].keys())
        
        # Intersect with the rest
        for comp_type in comp_types[1:]:
            if comp_type not in self._components:
                return []
            entities.intersection_update(self._components[comp_type].keys())
            
        return list(entities)

class System:
    def update(self, registry: Registry, dt: float):
        pass
