"""Utils for the Grenton objects integration."""
import requests
from typing import Any

def _send_request(api_endpoint: str, command: str):
    response = requests.get(
        f"{api_endpoint}",
        json = command
    )
    response.raise_for_status()
    return response.json()

def send_request(api_endpoint: str, payload: str):
    return _send_request(api_endpoint, {"status": payload})["status"]

def send_batch_requests(api_endpoint: str, requests: list[str]):
    commands = {f"req_{i}": v for i, v in enumerate(requests)}
    
    response_json = _send_request(api_endpoint, commands)
    
    return [response_json[f"req_{i}"] for i in range(len(commands))]

def get_feature(api_endpoint: str, grenton_id: str, index: int):
    splt = grenton_id.split('->')
    return send_request(api_endpoint, f"return {splt[0]}:execute(0, '{splt[1]}:get({index})')")

def set_feature(api_endpoint: str, grenton_id: str, index: int, value: Any):
    splt = grenton_id.split('->')
    return send_request(api_endpoint, f"{splt[0]}:execute(0, '{splt[1]}:set({index},{value})')")

def execute(api_endpoint: str, grenton_id: str, index: int, arg: Any = 0):
    splt = grenton_id.split('->')
    send_request(api_endpoint, f"{splt[0]}:execute(0, '{splt[1]}:execute({index},{arg})')")

def get_features(api_endpoint: str, grenton_id: str, indexes: list[int]):
    splt = grenton_id.split('->')
    return send_batch_requests(api_endpoint, [f"return {splt[0]}:execute(0, '{splt[1]}:get({i})" for i in indexes])

def set_features(api_endpoint: str, grenton_id: str, pairs: list[tuple[int, Any]]):
    splt = grenton_id.split('->')
    return send_batch_requests(api_endpoint, [f"return {splt[0]}:execute(0, '{splt[1]}:set({i},{v})" for i, v in pairs])