from typing import TypedDict

class User(TypedDict):
    id: int
    name: str
    age: int
# 可以实例化、创建对象
p = User("2222", "张三",14)
print(p.name)
print(p.id)
