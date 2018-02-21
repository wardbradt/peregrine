class StackSet:
    def __init__(self):
        self.data = []
        self.soft_pop_counter = 0

    def add(self, element):
        if element in self.data:
            self.data.remove(element)
        self.data.append(element)

    def pop(self):
        self.data.pop()

    def soft_pop(self):
        """
        It is assumed that either no element e will be added after soft_pop is called or that if an element is added,
        soft_pop will be called with the knowledge that e will be ignored.

        Removing an element e after soft_pop is called will also have possibly unintended side effects (namely when
        soft_pop has not yet returned e).
        """
        self.soft_pop_counter -= 1
        if self.is_done_popping:
            raise IndexError("Done soft popping!")
        return self.data[self.soft_pop_counter]

    @property
    def is_done_popping(self):
        return -self.soft_pop_counter > len(self.data)
