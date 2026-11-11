Read /work/task.md. It names a stripped binary in /work and a target function address in it.

Explain:
1. what the program does,
2. what input it reads and how that input is structured,
3. the call path from the program entry to the target function, and the role of each function on that path, with the address of the instruction where each function hands control to the next one and what you observed there,
4. which part of the input reaches the target function (through the call site named in task.md, if one is given).

Answer in the required JSON format. Use confidence "unknown" when you cannot determine something.

Tools available in this container: Ghidra 12.1 headless (`analyzeHeadless`, Ghidra at /opt/ghidra), radare2 (`r2`), binutils (`objdump`, `readelf`, `nm`, `strings`), `file`, `xxd`, `python3`. /work is read-only; use /tmp for scratch files.
