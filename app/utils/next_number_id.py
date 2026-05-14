def next_number_id():
  """
  生成唯一数字格式ID
  """
  return _generator.generate_id()


import hashlib
import socket
import threading
import time
from typing import Optional


class AutoSnowflakeGenerator:
  """
  自动分配机器ID的雪花算法生成器
  """

  EPOCH = 1672531200000
  TIMESTAMP_BITS = 41
  MACHINE_ID_BITS = 10
  SEQUENCE_BITS = 12

  MAX_MACHINE_ID = -1 ^ (-1 << MACHINE_ID_BITS)
  MAX_SEQUENCE = -1 ^ (-1 << SEQUENCE_BITS)
  MACHINE_ID_SHIFT = SEQUENCE_BITS
  TIMESTAMP_LEFT_SHIFT = SEQUENCE_BITS + MACHINE_ID_BITS

  def __init__(self, machine_id: Optional[int] = None):
    """
    初始化雪花ID生成器，支持自动分配机器ID

    Args:
        machine_id: 机器ID，如果为None则自动分配
    """
    if machine_id is None:
      self.machine_id = self._generate_auto_machine_id()
    else:
      if machine_id < 0 or machine_id > self.MAX_MACHINE_ID:
        raise ValueError(f"Machine ID must be between 0 and {self.MAX_MACHINE_ID}")
      self.machine_id = machine_id

    self.sequence = 0
    self.last_timestamp = -1
    self.lock = threading.Lock()

  def _generate_auto_machine_id(self) -> int:
    """自动生成机器ID"""
    # 方法1：基于IP地址
    hostname = socket.gethostname()
    ip_address = socket.gethostbyname(hostname)
    hash_obj = hashlib.md5(ip_address.encode())
    hash_hex = hash_obj.hexdigest()
    machine_id = int(hash_hex[:8], 16) % 1024
    return machine_id

  def _current_time_millis(self) -> int:
    """获取当前时间戳（毫秒）"""
    return int(time.time() * 1000)

  def _wait_next_millis(self, last_timestamp: int) -> int:
    """等待下一毫秒直到时间戳变化"""
    timestamp = self._current_time_millis()
    while timestamp <= last_timestamp:
      timestamp = self._current_time_millis()
    return timestamp

  def generate_id(self) -> int:
    """
    生成唯一的雪花ID

    Returns:
        64位整数形式的唯一ID
    """
    with self.lock:
      current_timestamp = self._current_time_millis()

      if current_timestamp < self.last_timestamp:
        raise RuntimeError("Clock moved backwards. Refusing to generate id")

      if current_timestamp == self.last_timestamp:
        self.sequence = (self.sequence + 1) & self.MAX_SEQUENCE
        if self.sequence == 0:
          current_timestamp = self._wait_next_millis(self.last_timestamp)
      else:
        self.sequence = 0

      self.last_timestamp = current_timestamp

      timestamp_part = (current_timestamp - self.EPOCH) << self.TIMESTAMP_LEFT_SHIFT
      machine_id_part = self.machine_id << self.MACHINE_ID_SHIFT
      sequence_part = self.sequence

      return timestamp_part | machine_id_part | sequence_part


_generator = AutoSnowflakeGenerator()
