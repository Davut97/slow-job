# Slow job with live progress

A small job queue built on Redis. A web page starts a slow job, a worker runs it, and the page shows a live progress bar over a WebSocket.

## How it works

1. The page sends `POST /jobs`. The API creates a job id and pushes it to the Redis list `jobs`.
2. A worker moves the job from `jobs` to `processing` and starts working.
3. Every second the worker saves the progress in a key and publishes it on the channel `progress:<job_id>`.
4. The page opens a WebSocket to `/ws/jobs/<job_id>`. The API subscribes to that channel and forwards each message.
5. At 100 the API closes the WebSocket.

## How to run it

```
docker run -d --name slow-job-redis -p 6379:6379 redis
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
uvicorn main:app --reload
python worker.py
```

Start `python worker.py` in a second terminal. You can start more than one worker. Then open http://127.0.0.1:8000/

## Design decisions

| Problem | What I did | Why |
| --- | --- | --- |
| A worker dies in the middle of a job | The job is moved to a `processing` list, not removed, and is deleted only when the work is finished | The job is never lost if the worker crashes |
| Another worker takes a job that is still running | Each worker holds a lease on its job: a key `lock:<job_id>` that expires after 5 seconds and is renewed every second. Idle workers check `processing` every 2 seconds and requeue only jobs with no lease | A job in `processing` only shows it was claimed. The lease shows the worker is still alive |
| The browser connects late and misses messages | The worker saves the latest progress in a key before publishing it, and the API sends that value when a WebSocket connects | Pub/sub does not store messages, so the current state has to live somewhere else |

## Known limits

- A worker that freezes for longer than its lease can lose the job while still running it, so a job can run twice. The fix is to make the job idempotent.
- `recover()` checks the lease and moves the job in separate commands, so it is not atomic.
- A page that connects after the job has finished gets 100 but the WebSocket is not closed.

## Next steps

- Make the job idempotent with a `done:<job_id>` key.
- Make recovery atomic with a Lua script.
- Add a dead letter list for jobs that fail several times.
