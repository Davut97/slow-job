import redis

r = redis.Redis(host="localhost", port=6379, decode_responses=True)

r.set("name", "Owais")
print(r.get("name"))

r.lpush("queue", "job-1")
r.lpush("queue", "job-2")
r.lpush("queue", "job-3")
print(r.llen("queue"))
print(r.rpop("queue"))
print(r.llen("queue"))
