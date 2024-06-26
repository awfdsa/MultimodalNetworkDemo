import logging
from datetime import datetime
import os
from pathlib import Path
import toml
from pydantic import BaseModel,Field
from ipaddress import IPv4Address
import typing_extensions as typing

__all__=['logger','switch_configs']

root = Path(__file__).parent.parent

class SSHConfig(BaseModel):
    ip:IPv4Address
    port:int
    user:str
    password:str
class Bmv2Config(BaseModel):
    port:int
    register_indexes:typing.Tuple[int,int,int]=Field(description="路径123分别对应寄存器的哪些索引")
class SwitchConfig(BaseModel):
    ssh:SSHConfig
    bmv2:Bmv2Config
    name:str


CONFIG_PATH = root/"config.toml"
switch_configs = [SwitchConfig(**i) for i in toml.load(CONFIG_PATH)['multipath']['switch']]

LOG_FILE_PATH = root/"logs"/datetime.now().strftime("%Y%m%d_%H-%M-%S.log")
LOG_FILE_PATH.parent.mkdir(exist_ok=True)

logger=logging.getLogger('schedule')
logger.setLevel(logging.DEBUG)

console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

file_handler = logging.FileHandler(LOG_FILE_PATH,encoding='utf8',mode="w")
file_handler.setLevel(logging.DEBUG)
file_handler.setFormatter(
    logging.Formatter(
        fmt='%(asctime)s - %(name)s - %(levelname)s > %(message)s',
        datefmt= '%Y-%m-%d %H:%M:%S'
    )
)
logger.addHandler(file_handler)
logger.addHandler(console_handler)