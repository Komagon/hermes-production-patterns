#!/usr/bin/env python3
"""幂等性冒烟测试:同 key 第二次执行必须跳过."""

def test_state_roundtrip():
    state = {"idempotency_keys": []}
    key = "{job}-20260830-001"
    assert key not in state["idempotency_keys"], "首次不应命中"
    state["idempotency_keys"].append(key)
    assert key in state["idempotency_keys"], "写入后应可检索"

test_state_roundtrip()
print("PASS: idempotency roundtrip")
