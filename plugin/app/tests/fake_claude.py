"""A stand-in for `claude -p --input-format stream-json --output-format stream-json`.

It reads one stream-json user message per line on stdin and prints the kinds of
line the real command prints: init, thinking, a text delta, a tool call, a
rate-limit event and a result. It never talks to any service. A message
containing the word `slow` starts a reply and then never finishes it, so the
tests can stop a turn half-way.
"""
import json
import os
import sys
import time


def out(obj) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def main() -> int:
    argv = sys.argv[1:]
    resumed = argv[argv.index("--resume") + 1] if "--resume" in argv else ""
    session = resumed or f"fake-{os.getpid()}"
    for raw in sys.stdin:
        raw = raw.strip()
        if not raw:
            continue
        message = json.loads(raw)
        text = message["message"]["content"][0]["text"]
        out({"type": "system", "subtype": "init", "session_id": session})
        out({"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "thinking"}}})
        out({"type": "system", "subtype": "thinking_tokens", "estimated_tokens": 12})
        out({"type": "stream_event", "event": {"type": "content_block_start", "content_block": {"type": "text"}}})
        reply = f"pid={os.getpid()} resumed={resumed or 'no'} cwd={os.getcwd()} echo={text} $x^2$"
        out({"type": "stream_event", "event": {"type": "content_block_delta",
                                               "delta": {"type": "text_delta", "text": reply}}})
        if "slow" in text:
            time.sleep(120)
            return 1
        out({"type": "assistant", "message": {"content": [
            {"type": "tool_use", "name": "Bash",
             "input": {"command": 'python3 "/plugin/engine/vl.py" record "Alpha" --result pass'}}]}})
        out({"type": "rate_limit_event", "rate_limit_info": {
            "unifiedWindows": {"five_hour": {"utilization": 0.25, "resetsAt": 1000}}}})
        out({"type": "result", "subtype": "success", "total_cost_usd": 0.5,
             "usage": {"output_tokens": 20, "iterations": [{"input_tokens": 2, "cache_read_input_tokens": 300}]}})
    return 0


if __name__ == "__main__":
    sys.exit(main())
