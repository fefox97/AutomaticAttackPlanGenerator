import json
from sqlalchemy import types

class ExternalReferencesType(types.TypeDecorator):
    impl = types.Unicode

    def process_bind_param(self, value, dialect):
        serialized = [v.serialize() for v in value]
        return json.dumps(serialized)

    def process_result_value(self, value, dialect):
        value = json.loads(value)
        deserialized = [json.loads(v) for v in value]
        return deserialized