from abc import ABC, abstractmethod

class RepositoryFactory(ABC):
    @abstractmethod
    def create(self, model):
        pass

    @abstractmethod
    def read(self, id):
        pass

    @abstractmethod
    def readAll(self):
        pass

    @abstractmethod
    def update(self, name):
        pass

    @abstractmethod
    def delete(self, id):
        pass
