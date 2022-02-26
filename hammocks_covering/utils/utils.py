class DSU:
    def __init__(self):
        self.__elements = {}  # element -> number id
        self.__heights = []
        self.__parent = []

    def add_element(self, element):
        if element in self.__elements:
            return
        element_id = len(self.__elements)
        self.__elements[element] = element_id
        self.__heights.append(1)
        self.__parent.append(element_id)

    def __get_class(self, element_id):
        if self.__parent[element_id] == element_id:
            return element_id

        res = self.__get_class(self.__parent[element_id])
        self.__parent[element_id] = res
        return res

    def get_class(self, element) -> Union[int, None]:
        if element not in self.__elements:
            return None

        element_id = self.__elements[element]
        return self.__get_class(element_id)

    def unite(self, element1, element2):
        class1 = self.get_class(element1)
        class2 = self.get_class(element2)

        if class1 is None or class2 is None:
            raise Exception("No such elements in the DSU")

        if class1 == class2:
            return
        if self.__heights[class1] < self.__heights[class2]:
            class1, class2 = class2, class1

        self.__parent[class2] = class1
        if self.__heights[class1] == self.__heights[class2]:
            self.__heights[class1] += 1

    def get_sets(self):
        sets = {}
        for element, element_id in self.__elements.items():
            element_class = self.__get_class(element_id)
            if element_class not in sets:
                sets[element_class] = set()
            sets[element_class].add(element)
        return sets.values()
