import datetime
import uuid


class DynamoDB:
    def __init__(self, table_resource, key_name):
        self._table = table_resource
        self.key_name = key_name

    def add_file(self, data_id, info=None):
        if info is None:
            info = []
        self._table.put_item(
            Item={
                self.key_name: data_id,
                'Info': info
            }
        )

    def get_file(self, data_id):
        response = self._table.get_item(
            Key={
                self.key_name: data_id
            }
        )
        return response.get('Item')

    def delete_all_file(self, data_id):
        self._table.delete_item(
            Key={
                self.key_name: data_id,
            }
        )

    def list_all(self):
        response = self._table.scan()
        return response['Items']

    def delete_all(self):
        response = self._table.scan()
        items = response['Items']
        for item in items:
            self.delete_all_file(item[self.key_name])


def generate_unique_id():
    current_time = datetime.datetime.now().strftime("%Y-%m-%d_%H:%M:%S")
    unique_id = str(uuid.uuid4())
    return current_time + unique_id
