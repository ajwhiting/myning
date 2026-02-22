class Singleton(type):
    """Metaclass that ensures only one instance of a class exists.

    Usage:
        1. Define a class with ``metaclass=Singleton``
        2. Implement ``initialize()`` as a classmethod that loads or creates
           the instance using ``cls._create(...)`` and assigns it to ``cls._instance``
        3. Call ``ClassName.initialize()`` once at startup
        4. Use ``ClassName()`` anywhere to retrieve the singleton instance

    Calling ``ClassName()`` before ``initialize()`` raises ``RuntimeError``.
    """

    _instances: dict[type, object] = {}

    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            raise RuntimeError(
                f"{cls.__name__}() called before {cls.__name__}.initialize(). "
                f"Singletons must be initialized at startup."
            )
        return cls._instances[cls]

    def _create(cls, *args, **kwargs):
        """Create a new instance during initialization, bypassing the init check."""
        return super(Singleton, cls).__call__(*args, **kwargs)

    @property
    def _instance(cls):
        return cls._instances.get(cls)

    @_instance.setter
    def _instance(cls, instance):
        cls._instances[cls] = instance

    @classmethod
    def reset(cls):
        cls._instances = {}
