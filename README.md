A small game written in pygame 2. I use Python 3.9 as the interpreter.

The entry point is `main.py` (that is, run the game with the command
`python3.9 main.py`). Controls are: W to accelerate, A and D to turn,
S to slow down, Space to shoot.

# (Programming) Concepts

## Singletons are singletons

This project went through three different phases in terms of
dependency injection:

1. Pass shared dependencies around manually through function and
   constructor arguments.
2. Use [Pinject](https://github.com/google/pinject) to construct the
   object graph.
3. Use modules as singleton objects. (current)

After using a DI framework (Google's Pinject) for a while, I ended up
having a lot of code like this:

```python
class AsteroidFactory:
    def __init__(
        self,
        game_object_system: GameObjectSystem,
        physics_system: PhysicsSystem,
        rendering_system: RenderingSystem,
        explosion_factory: ExplosionFactory,
        provide_asteroid_images,
        extra_heart_factory: ExtraHeartFactory,
        extra_bullet_factory: ExtraBulletFactory,
    ):
        self._game_object_system = game_object_system
        ...

     def __call__(
        self,
        counter,
        *,
        x: float = 400,
        y: float = 300,
        vx: float = 0,
        vy: float = 0
    ) -> GameObject:
        ...
        
    # No other methods
```

This felt too verbose for Python, but I justified it with the usual
argument for using DI instead of global state: it's hard to stub
global state, so it makes unit tests more fragile and difficult to
write. I wasn't planning on adding unit tests, but I wanted to "do
things right", so I used Pinject. I was a little miffed at `pygame`
using global state and considered writing a nice class to wrap it.

Until I realized that I can stub out modules in Python.

Now everything else is just silly. Physics and graphics are singletons
in my game; I'm not trying to write general-purpose libraries here.
Why pass them as arguments? That's just boilerplate. Python modules
are singletons! It's perfect!

## Transform

The `Transform` is a mutable object that represents a translation and
a rotation. It is meant to be shared by different pieces of code; for
example, the physics system modifies the transform by applying
velocities and the graphics system applies the transform when
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

The graphics system is defined in `graphics.py`

There are two types of graphical objects: `Sprite` and `Text`.
`Sprite` is used to display an image, and `Text` is used to display
text in a given font. All graphical objects are attached to a
`GameObject` (meaning they get destroyed when that object is
destroyed) and are positioned according to a `Transform`.

`Sprite` and `Text` should be created by calling the `new_sprite` and
`new_text` methods on the `graphics` module.

## Physics

Physics are implemented in the `physics` directory. I implement
elastic collisions between circle colliders, and I also implement
trigger colliders like in Unity. The physics engine doesn't support
angular momentum, friction, inelastic collisions or other collider
shapes yet, but the design of the code doesn't preclude this.

A `PhysicsBody` represents an object that participates in the physics
simulation (in a specific `PhysicsSystem`). `PhysicsBody`s are created
using the `physics.new_body` method. Use the `add_circle_collider`
method to specify a collider on the body so that it can bounce off of
other bodies. Colliders attached to a `PhysicsBody` are of type
`RegularCollider`.

A `TriggerCollider` is a region of space that detects when any other
kind of collider (`TriggerCollider` or `RegularCollider`) enters it.
The only trigger collider right now can be created using the
`physics.new_circle_trigger` method.

All physics objects are attached to a `GameObject` and positioned
according to a `Transform`. The physics system modifies a
`PhysicsBody`'s transform to move the body by its velocity.
