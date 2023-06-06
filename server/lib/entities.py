import json
from typing import List
from .event_emitter import EventEmitter, EVENTS

class Model:
    def __init__(
        self, name: str, enabled: bool, capabilities: List[str],  provider: str, status: str, parameters: dict = None, engine: str=None, api_version: str=None,
    ):
        self.name = name
        self.capabilities = capabilities
        self.enabled = enabled
        self.provider = provider
        self.engine = engine
        self.api_version = api_version
        self.status = status
        self.parameters = parameters

    def copy(self):
        return Model(
            name=self.name,
            capabilities=self.capabilities,
            enabled=self.enabled,
            provider=self.provider,
            engine=self.engine,
            api_version= self.api_version,
            status=self.status,
            parameters=self.parameters.copy()
        )

    def __repr__(self):
        return f'Model({self.name}, {self.capabilities}, {self.enabled}, {self.provider}, {self.engine}, {self.status}, {self.parameters})'

class ModelEncoder(json.JSONEncoder):
    def __init__(self, *args, serialize_as_list=True, **kwargs):
        self.serialize_as_list = serialize_as_list
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, Model):
            properties = {
                "capabilities": obj.capabilities, "engine": obj.engine, "api_version": obj.api_version,
                "enabled": obj.enabled, "status": obj.status, "parameters": obj.parameters
            }
            if self.serialize_as_list:
                return {**{"name": obj.name, "provider": obj.provider}, **properties}
            else:
                return {f"{obj.provider}:{obj.name}": properties}
        return super().default(obj)

class Provider:
    def __init__(
        self, name: str, models: List[Model], remote_inference: bool = False,
        default_capabilities: List[str] = None, default_parameters: dict = None,
        api_key: str = None, requires_api_key: bool = False,
        api_base: str = None,
        search_url: str = None
    ):
        self.event_emitter = EventEmitter()
        self.name = name
        self.models = models
        self.remote_inference = remote_inference
        self.default_capabilities = default_capabilities
        self.default_parameters = default_parameters
        self.api_key = api_key
        self.api_base = api_base
        self.requires_api_key = requires_api_key
        self.search_url = search_url
    
    def has_model(self, model_name: str) -> bool:
        return any(model.name == model_name for model in self.models)
    
    def get_model(self, model_name: str) -> Model:
        for model in self.models:
            if model.name == model_name:
                return model
            
    def update_model(self, model_name: str, model: Model) -> None:
        for i, m in enumerate(self.models):
            if m.name == model_name:
                self.models[i] = model
                self.event_emitter.emit(EVENTS.MODEL_UPDATED, model)
                return
    
    def add_model(self, model: Model) -> None:
        self.models.append(model)
        print("Added model!")
        self.event_emitter.emit(EVENTS.MODEL_ADDED, model)

    def remove_model(self, model_name: str) -> None:
        for model in self.models:
            if model.name == model_name:
                self.models.remove(model)
                self.event_emitter.emit(EVENTS.MODEL_REMOVED, model)
                return
            
    def copy(self):
        return Provider(
            name=self.name,
            models=[model.copy() for model in self.models],
            remote_inference=self.remote_inference,
            default_capabilities=self.default_capabilities.copy() if self.default_capabilities else None,
            default_parameters=self.default_parameters.copy() if self.default_parameters else None,
            api_key=self.api_key,
            api_base=self.api_base,
            requires_api_key=self.requires_api_key,
            search_url=self.search_url
        )
    
    def __repr__(self):
        return f'Provider({self.name}, {self.models}, {self.remote_inference}, {self.default_parameters}, {self.api_key}, {self.requires_api_key}, {self.search_url})'

class ProviderEncoder(json.JSONEncoder):
    def __init__(self, *args, serialize_models_as_list=True, **kwargs):
        self.serialize_models_as_list = serialize_models_as_list
        super().__init__(*args, **kwargs)

    def default(self, obj):
        if isinstance(obj, Provider):
            models = [{
                "name": model.name, "capabilities": model.capabilities,
                "enabled": model.enabled, "provider": model.provider, "engine": model.engine,
                "api_version": model.api_version,
                "status": model.status, "parameters": model.parameters
            } for model in obj.models]
            
            if not self.serialize_models_as_list:
                models = dict(zip([model["name"] for model in models], models))
        
            return {self.to_camel_case(k): v for k, v in obj.__dict__.items() if k not in {'models', 'event_emitter', 'api_key'}} | {'models': models}
        return super().default(obj)
    
    @staticmethod
    def to_camel_case(snake_str):
        components = snake_str.split('_')
        return components[0] + ''.join(x.capitalize() for x in components[1:])