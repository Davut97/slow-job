import time
import redis


r = redis.Redis(host="localhost", port=6379, decode_responses=True)


def recover():
    for processing_job in r.lrange("processing", 0, -1):
        if not r.exists(f"lock:{processing_job}"):
            r.lrem("processing", 1, processing_job)
            r.rpush("jobs", processing_job)
            print(f"recovered {processing_job}")


recover()
while True:
    job_id = r.blmove("jobs", "processing", timeout=2, src="RIGHT", dest="LEFT")
    if job_id is None:
        recover()
        continue
    lock_id = f"lock:{job_id}"
    r.set(lock_id, job_id, nx=True, ex=5)
    print(f"started job {job_id}")
    for number in range(10, 101, 10):
        r.expire(lock_id, 5)
        r.set(f"progress:{job_id}", f"{number}", ex=3600)
        r.publish(f"progress:{job_id}", f"{number}")

        time.sleep(1)
    r.lrem("processing", 1, job_id)
    r.delete(lock_id)
    print(f"finished job {job_id}")
