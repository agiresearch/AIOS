class Agent:
    existing = {}

    def __init__(self, purpose: str, name: str, **kwargs):
        self.name = name
        self.purpose = purpose

        self.args = {
            'name': name,
            'purpose' : purpose
        }

        for key, value in kwargs.items():
            setattr(self, key, value)
            self.args[key] = value

        self.existing[self.name] = self

    def call(self, **kwargs):
        for key, value in kwargs.items():
            if not hasattr(self, key):
                raise AttributeError(f"Attribute '{key}' is not defined in this agent.")

            expected_type = getattr(self, key)
            if not isinstance(value, expected_type):
                raise TypeError(f"Expected type '{expected_type.__name__}' for attribute '{key}', but got '{type(value).__name__}'.")

        self._call(**kwargs)

    def _call(self, **kwargs):
        raise NotImplementedError
    
    def __str__(self):
        g = ''

        for k,v in self.args.items():
            g += f'{k}: {v} \n'

        return g
    
    @classmethod
    def retrieve_agent(cls, name: str):
        return cls.existing.get(name)
