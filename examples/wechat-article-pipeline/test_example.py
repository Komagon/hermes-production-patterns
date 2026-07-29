#!/usr/bin/env python3
"""Smoke test for wechat-article-pipeline: verify ai_detect.py works."""
import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'scripts'))
from ai_detect import analyze

# Test 1: Clean text (human-written style)
clean_text = """上周我把Hermes的内存从内部切到了外部记忆提供者。
本以为插上就能用，结果折腾了三天。
问题出在哪呢？Memory provider有8个，你选谁？
我干脆把两个最主流的——Hindsight和Mem0——的源码都扒了一遍。"""
result1 = analyze(clean_text, verbose=False)
assert result1['concentration'] <= 20, f"Clean text should be <=20%, got {result1['concentration']}%"

# Test 2: AI-tainted text
ai_text = """随着AI技术的不断发展，多Agent系统已经成为了当前最热门的技术方向。
首先，我们需要理解多Agent系统的核心概念。
其次，我们来看一下它的架构设计。
最后，值得一提的是，在实际部署中需要注意几个关键问题。"""
result2 = analyze(ai_text, verbose=False)
assert result2['concentration'] > 20, f"AI text should be >20%, got {result2['concentration']}%"

# Test 3: Grade classification
assert result1['grade'].startswith('A'), f"Clean should be A, got {result1['grade']}"
assert result2['grade'].startswith('B') or result2['grade'].startswith('C'), f"AI should be B/C, got {result2['grade']}"

print(f"✅ wechat-article-pipeline smoke test passed")
print(f"   Clean text: {result1['concentration']}% ({result1['grade']})")
print(f"   AI text:    {result2['concentration']}% ({result2['grade']})")
