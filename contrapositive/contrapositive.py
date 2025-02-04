import json
import sys

# Map of inequalities to their inverses
INEQUALITIES = {"lt": "ge", "le": "gt", "gt": "le", "ge": "lt"}


def replace_inequality(instr):
    instr["op"] = INEQUALITIES[instr["op"]]
    instr["args"] = list(reversed(instr["args"]))
    return instr


def contrapositive():
    prog = json.load(sys.stdin)

    for func in prog["functions"]:
        for i in range(len(func["instrs"])):
            if func["instrs"][i]["op"] in INEQUALITIES:
                func["instrs"][i] = replace_inequality(func["instrs"][i])

    print(json.dumps(prog, indent=4))


if __name__ == "__main__":
    contrapositive()
