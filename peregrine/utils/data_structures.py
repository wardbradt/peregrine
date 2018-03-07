import heapq


class StackSet:
    def __init__(self):
        self.data = []
        self.soft_pop_counter = 0

    def add(self, element, enforce_stack=True):
        if enforce_stack and element in self.data:
            self.data.remove(element)

        self.data.append(element)
        return True

    def peek(self):
        return self.data[-1]

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


class PrioritySet:
    def __init__(self):
        self.heap = []
        self.popped = {}

    def add(self, d, pri):
        heapq.heappush(self.heap, (pri, d))

        return True

    def pop(self):
        popped = heapq.heappop(self.heap)
        while popped[1] in self.popped.keys():
            # Raises IndexError if done popping
            try:
                popped = heapq.heappop(self.heap)
            # for debugging
            except Exception as e:
                raise e

        self.popped[popped[1]] = popped[0]
        return popped

    def peek(self):
        # self.heap[0][1] is the name of the element
        try:
            while self.heap[0][1] in self.popped.keys():
                # Raises IndexError if done popping
                heapq.heappop(self.heap)
        # for debugging
        except Exception as e:
            raise e

        return self.heap[0]

    def reset(self):
        """
        Not optimized, slow.
        todo: optimize this method. how to account for the fact that self.popped is added in order?
        """
        for key, value in self.popped.items():
            heapq.heappush(self.heap, (value, key))
        self.popped = {}

    @property
    def empty(self):
        for elem in self.heap:
            if elem[1] not in self.popped.keys():
                return False

        return True

    def __str__(self):
        return str(list(self.heap))

    def __repr__(self):
        return str(self)

    def __len__(self):
        """
        Somewhat slow. (I think O(n^2))
        """
        total = 0
        seen = set()
        for elem in self.heap:
            if elem not in self.popped and elem not in seen:
                total += 1
                seen.add(elem)

        return total
