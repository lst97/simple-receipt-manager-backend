from .repository_factory import RepositoryFactory
from ..models.groups import Groups
from mongoengine import DoesNotExist


class GroupRepository(RepositoryFactory):
    def create(self, group):
        try:
            new_group = Groups(
                name=group["name"],
                users=group.get("users", []),
                records=group.get("records", [])
            )
            new_group.save()
            return str(new_group.id)
        except Exception as e:
            return None

    def read(self, id):
        try:
            group = Groups.objects.get(id=id)
            return group.serialize()
        except DoesNotExist:
            return None

    def readAll(self):
        try:
            groups = Groups.objects()
            return [group.serialize() for group in groups]
        except DoesNotExist:
            return None

    def update(self, id, updated_group_data):
        try:
            group = Groups.objects.get(id=id)
            group.name = updated_group_data.get("name", group.name)
            group.users = updated_group_data.get("users", group.users)
            group.records = updated_group_data.get("records", group.records)
            group.save()
            return True
        except DoesNotExist:
            return False

    def delete(self, id):
        try:
            group = Groups.objects.get(id=id)
            group.delete()
            return True
        except DoesNotExist:
            return False

    def aggregate(self, pipeline):
        try:
            groups = Groups.objects.aggregate(*pipeline)
            return [group.serialize() for group in groups]
        except DoesNotExist:
            return None
