from abc import ABC, abstractmethod

# Define the abstract base class 'Format'
class IFormat(ABC):
    """
    An abstract base class for different export formats.
    It defines the common methods that all formats should have.
    """

    @abstractmethod
    def export(self, text, location, filename):
        """
        Abstract method to generate and export the format to the filesystem
        :param text: The chapter text content to be exported.
        :param location: The filesystem location where the export will be saved.
        :param filename: The name of the file to be created.
        """
        pass
