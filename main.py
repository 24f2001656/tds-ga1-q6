import os
from pathlib import Path
from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
import yaml
from dotenv import dotenv_values

BASE = Path(__file__).resolve().parent
DEFAULTS = {'port':8000,'workers':1,'debug':False,'log_level':'info','api_key':'default-secret-000'}
KEYS = set(DEFAULTS)
ENV_NAMES = {'APP_PORT':'port','APP_WORKERS':'workers','NUM_WORKERS':'workers','APP_DEBUG':'debug','APP_LOG_LEVEL':'log_level','APP_API_KEY':'api_key'}

def convert(key, value):
    if key in ('port','workers'):
        return int(value)
    if key == 'debug':
        return str(value).lower() in ('true','1','yes','on')
    return str(value)

def update(config, values, mapping=None):
    for key, value in values.items():
        target = mapping.get(key, key) if mapping else key
        if target in KEYS and value is not None:
            config[target] = convert(target, value)

app = FastAPI()
app.add_middleware(CORSMiddleware, allow_origins=['*'], allow_methods=['GET'], allow_headers=['*'])

@app.get('/effective-config')
def effective_config(set: list[str] = Query(default=[])):
    config = DEFAULTS.copy()
    env_name = os.environ.get('APP_ENV', 'development')
    yaml_path = BASE / f'config.{env_name}.yaml'
    if yaml_path.is_file():
        update(config, yaml.safe_load(yaml_path.read_text()) or {})
    update(config, dotenv_values(BASE / '.env'), ENV_NAMES)
    update(config, {k:v for k,v in os.environ.items() if k.startswith('APP_') and k != 'APP_ENV'}, ENV_NAMES)
    for item in set:
        if '=' in item:
            key, value = item.split('=',1)
            update(config, {key:value})
    config['api_key'] = '****'
    return config
