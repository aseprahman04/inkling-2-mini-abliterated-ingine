"""Check a small coding task against a local Ingine endpoint."""
import argparse
import json
import sqlite3
import time
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--url", default="http://127.0.0.1:19554/v1")
    url = parser.parse_args().url.rstrip("/")
    with urllib.request.urlopen(url + "/models", timeout=10) as response:
        model = json.load(response)["data"][0]["id"]

    prompt = ("Write one SQLite statement selecting the names from users for which score >= 10, "
              "sorted by score descending then name ascending. Return SQL only.")
    payload = {"model": model, "temperature": 0, "max_tokens": 100,
               "messages": [{"role": "user", "content": prompt}],
               "chat_template_kwargs": {"enable_thinking": False, "reasoning_effort": "none"}}
    request = urllib.request.Request(url + "/chat/completions", json.dumps(payload).encode(),
                                     {"Content-Type": "application/json"})
    start = time.monotonic()
    with urllib.request.urlopen(request, timeout=120) as response:
        result = json.load(response)
    wall = time.monotonic() - start
    choice = result["choices"][0]
    sql = choice["message"]["content"].strip()
    if sql.startswith("```"):
        sql = sql.split("\n", 1)[1].removesuffix("```").strip()

    with sqlite3.connect(":memory:") as db:
        db.execute("CREATE TABLE users(name TEXT, score INTEGER)")
        db.executemany("INSERT INTO users VALUES (?,?)",
                       [("Z", 10), ("A", 10), ("C", 9), ("B", 11), ("N", None)])
        db.execute("PRAGMA query_only=ON")
        db.set_authorizer(lambda action, *_: sqlite3.SQLITE_OK if action in
                          (sqlite3.SQLITE_SELECT, sqlite3.SQLITE_READ) else sqlite3.SQLITE_DENY)
        db.set_progress_handler(lambda: 1, 10000)
        rows = db.execute(sql).fetchall()
    if choice["finish_reason"] != "stop" or rows != [("B",), ("A",), ("Z",)]:
        raise ValueError(f"Unexpected result: {rows!r}, reason={choice['finish_reason']!r}")
    print(json.dumps({"sql": sql, "rows": rows, "usage": result["usage"], "wall_seconds": wall}))


if __name__ == "__main__":
    main()
