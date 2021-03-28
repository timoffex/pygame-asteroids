from abc import ABC, abstractmethod


class Collider(ABC):
    """Abstract base class for collider objects.

    There are two types of colliders: regular colliders and trigger
    colliders.

    Regular colliders always belong to a PhysicsBody and should be
    created through the methods on PhysicsBody. Regular colliders cause
    their physics bodies to bounce off of each other when they collide.
    You can create an immovable collider by using a PhysicsBody with
    infinite mass.

    Trigger colliders do not belong to a PhysicsBody and are created
    through PhysicsSystem methods. Physics bodies do not bounce when
    they encounter trigger colliders. Trigger colliders are used to
    detect when something has entered an area on the screen.

    """

    @abstractmethod
    def __init__(self):
        pass

    def destroy(self):
        pass
