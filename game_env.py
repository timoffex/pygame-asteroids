from game_object import GameObjectSystem
from game_time import GameTime
from inputs import Inputs
from physics import PhysicsSystem
from rendering import RenderingSystem


class GameEnv:
    """A container object to keep track of all game singletons."""

    def __init__(self):
        self.physics = PhysicsSystem()
        self.graphics = RenderingSystem()
        self.inputs = Inputs()
        self.game_objects = GameObjectSystem()
        self.time = GameTime()
