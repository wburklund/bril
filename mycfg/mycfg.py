import collections
import json
import sys

import jinja2

TERMINATORS = ("jmp", "br", "ret")

CFG_DOT_TEMPLATE = jinja2.Template("""digraph {{func_name}} {
{%- for name, block in cfg.items() %}
    {{name}};
    {%- for succ in block.successors %}
    {{name}} -> {{succ}};
    {%- endfor %}
{%- endfor %}
}
""")


def form_blocks(body):
    cur_block = []

    for instr in body:
        if "op" in instr:  # An actual instruction.
            cur_block.append(instr)

            # Check for terminator.
            if instr["op"] in TERMINATORS:
                yield cur_block
                cur_block = []
        else:  # A label.
            if len(cur_block) > 0:
                yield cur_block
            cur_block = [instr]

    if len(cur_block) > 0:
        yield cur_block


def mycfg():
    prog = json.load(sys.stdin)
    cfg = {}

    label_counter = 1
    for func in prog["functions"]:
        func_cfg = collections.defaultdict(lambda: {"instrs": [], "successors": []})

        prev_name = None
        fallthrough = False
        for block in form_blocks(func["instrs"]):
            # Get block label, or create one.
            if "label" in block[0]:
                name = block.pop(0)["label"]
            else:
                name = f"_L{label_counter}"
                label_counter += 1

            # Wire up fallthrough from previous block if needed.
            if fallthrough:
                func_cfg[prev_name]["successors"].append(name)
                fallthrough = False

            # Look at last instruction / terminator to determine successors.
            last = block[-1]
            if last["op"] in ("jmp", "br"):
                func_cfg[name]["successors"] = last["labels"]
            elif last["op"] == "ret":  # Returning, so no successor.
                func_cfg[name]["successors"] = []
            else:  # Not a terminator. Fallthrough.
                fallthrough = True
                prev_name = name

            func_cfg[name]["instrs"] = block

        cfg[func["name"]] = dict(func_cfg)
        print(CFG_DOT_TEMPLATE.render(func_name=func["name"], cfg=func_cfg))


if __name__ == "__main__":
    mycfg()
