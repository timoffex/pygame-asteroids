TODO: This README is out-of-date.

A small game written in pygame 2. I use Python 3.9 as the interpreter.

This depends on the `pinject` and `pygame` packages.

The entry point is `main.py` (that is, run the game with the command
`python3.9 main.py`). Controls are: W to accelerate, A and D to turn,
S to slow down, Space to shoot.

# (Programming) Concepts

## Transform

The `Transform` is a mutable object that represents a translation and
a rotation. It is meant to be shared by different pieces of code; for
example, the physics system modifies the transform by applying
velocities and the rendering system applies the transform when
rendering sprites.

I model this roughly on Unity's Transform component, except:

* it's not a component
* it's not automatically present on all game objects
* it doesn't have scaling (because pygame doesn't make it easy to
  scale images)
  
A transform can have a parent transform. Changes to a parent transform
also move all descendant transforms. This allows defining a transform
that is always at some offset relative to another transform.

## GameObject

A `GameObject` is something that is updated every frame and can be
destroyed. The purpose of a `GameObject` is to allow code to refer to
the lifecycle of some entity in the game.

This is pretty different from Unity's GameObject. My `GameObject` is
not a container for components and doesn't automatically have a
`Transform`. Its sole purpose is to be a place where you can attach
two kinds of hooks: update hooks (which run on every frame) and
destroy hooks (which run when the object is destroyed).

A `GameObject` can have a "parent" in which case it is destroyed
whenever the parent is destroyed. In Unity, the Transform parent and
GameObject parent coincide; this is not a requirement in my code. The
only reason to create a child `GameObject` is when

1. the child is a "part of" the parent (and should cease to exist when
   the parent does),
2. and you want to be able to destroy the part but not the parent.

## Graphics

The graphics system is in `rendering.py`. There is a `RenderingSystem`
class which can be used to create `Sprite` objects.

`RenderingSystem` keeps track of all graphical objects and would be
responsible for rendering them efficiently (if there were more complex
graphics). It is meant to be a singleton that is created at startup
and that stays alive until the app shuts down.

There are two types of graphical objects: `Sprite` and `Text`.
`Sprite` is used to display an image, and `Text` is used to display
text in a given font. All graphical objects are attached to a
`GameObject` (meaning they get destroyed when that object is
destroyed) and are positioned according to a `Transform`.

`Sprite` and `Text` should be created by calling the `new_sprite` and
`new_text` methods on a `RenderingSystem` object.

## Physics

Physics are implemented in the `physics` directory. I implement
elastic collisions between circle colliders, and I also implement
trigger colliders like in Unity. The physics engine doesn't support
angular momentum, friction, inelastic collisions or other collider
shapes yet, but the design of the code doesn't preclude this.

The `PhysicsSystem` is a singleton object that manages everything
related to collisions, triggers, and physics-based motion.

A `PhysicsBody` represents an object that participates in the physics
simulation (in a specific `PhysicsSystem`). `PhysicsBody`s are created
using the `PhysicsSystem.new_body` method. Use the
`add_circle_collider` method to specify a collider on the body so that
it can bounce off of other bodies. Colliders attached to a
`PhysicsBody` are of type `RegularCollider`.

A `TriggerCollider` is a region of space that detects when any other
kind of collider (`TriggerCollider` or `RegularCollider`) enters it.
These are created using methods on a `PhysicsSystem` object such as
`new_circle_trigger`.

All physics objects are attached to a `GameObject` and positioned
according to a `Transform`. The physics system modifies a
`PhysicsBody`'s transform to move the body by its velocity.

## Pinject dependency injection

I use [Pinject](https://github.com/google/pinject) for dependency
injection.

The purpose of dependency injection (passing stuff through function
arguments) is to separate concerns. For example, the
`AsteroidGeneratorFactory` injects an `AsteroidFactory` and so doesn't
need to know the details of how to make an asteroid. I can redefine
how asteroids work without changing the asteroid spawner code, and I
can modify the spawner code without changing how asteroids work.

If you do dependency injection by manually passing function arguments,
you still have to construct all of the dependencies in the correct
order at the top level of your program. So while
`AsteroidGeneratorFactory` doesn't need to know how to make an
`AsteroidFactory`, `main.py` has to know how to make both:

```py
game_object_system = GameObjectSystem()
physics_system = PhysicsSystem()
rendering_system = RenderingSystem()
game_time = GameTime()
explosion_factory = ExplosionFactory(...)

asteroid_factory = AsteroidFactory(
    game_object_system=game_object_system,
    physics_system=physics_system,
    rendering_system=rendering_system,
    explosion_factory=explosion_factory,
)
asteroid_generator_factory = AsteroidGeneratorFactory(
    game_object_system=game_object_system,
    game_time=game_time,
    asteroid_factory=asteroid_factory
)
```

Clearly this is all boilerplate. All constructor arguments are in the
form `name=name` because all dependencies are named after their class
by convention. Worse: whenever any class gains a new dependency, I
have to touch `main.py` and might even have to rearrange the order in
which I make the objects! For example, if `game_object_system` started
to rely on `GameTime`, I would have to shuffle around those two lines
of code.

Pinject automates away this boilerplate.
