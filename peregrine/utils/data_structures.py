class StackSet:
    def __init__(self):
        self.data = []
        self.soft_pop_counter = 0

    def add(self, element, enforce_stack=True):
        if enforce_stack and element in self.data:
            self.data.remove(element)

        self.data.append(element)
        return True

    def pop(self):
        return self.data.pop()

    def soft_pop(self):
        """
        It is assumed that either no element e will be added after soft_pop is called or that if an element is added,
        soft_pop will be called with the knowledge that e will be ignored.

        Removing an element e after soft_pop is called will also have possibly unintended side effects (namely when
        soft_pop has not yet returned e).
        """
        self.soft_pop_counter -= 1
        if -self.soft_pop_counter <= len(self.data):
            return self.data[self.soft_pop_counter]
        else:
            raise IndexError("Soft popping completed.")

    @property
    def done_popping(self):
        result = -self.soft_pop_counter >= len(self.data)
        if result:
            self.soft_pop_counter = 0
        return result

    def __len__(self):
        return len(self.data)

    def __iter__(self):
        return iter(self.data)

    def __repr__(self):
        return str(self)

    def __str__(self):
        return str(list(self.data))
