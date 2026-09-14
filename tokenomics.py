COST_PER_1K_INPUT = 0.00001875
COST_PER_1K_OUTPUT = 0.000075


def log_usage(agent_name: str, input_tokens: int, output_tokens: int):
    cost = (input_tokens / 1000 * COST_PER_1K_INPUT) + (output_tokens / 1000 * COST_PER_1K_OUTPUT)
    print(f"[{agent_name}] tokens: in={input_tokens} out={output_tokens} cost=${cost:.6f}")

    _usage_log.append({
        "agent_name": agent_name,
        "input_tokens": input_tokens,
        "output_tokens": output_tokens,
        "cost": cost,
    })
    return cost

_usage_log = []

def summarize():
    if not _usage_log:
        print("No usage logged yet.")
        return

    total_cost = sum(e["cost"] for e in _usage_log)
    print(f"\n=== Tokenomics Summary ({len(_usage_log)} calls) ===")
    print(f"Total cost: ${total_cost:.6f}")

    by_agent = {}
    for e in _usage_log:
        stats = by_agent.setdefault(e["agent_name"], {"calls": 0, "tokens": 0, "cost": 0.0})
        stats["calls"] += 1
        stats["tokens"] += e["input_tokens"] + e["output_tokens"]
        stats["cost"] += e["cost"]

    for agent, stats in sorted(by_agent.items(), key=lambda kv: kv[1]["cost"], reverse=True):
        print(f"  {agent:<20} calls={stats['calls']:<3} tokens={stats['tokens']:<6} cost=${stats['cost']:.6f}")

    top_agent = max(by_agent, key=lambda a: by_agent[a]["tokens"])
    print(f"\nMost tokens consumed: {top_agent}")


if __name__ == "__main__":
    #simple test to demo logging
    log_usage("ManagerAgent", 320, 45)
    log_usage("QualitativeAgent", 890, 210)
    log_usage("QuantitativeAgent", 610, 130)
    log_usage("QualitativeAgent", 940, 180)
    summarize()