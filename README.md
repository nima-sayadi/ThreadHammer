# ThreadHammer

*A multi-threaded extension of Blacksmith for Rowhammer research.*

---

## 🧩 Overview

ThreadHammer extends the [Blacksmith](https://github.com/comsec-group/blacksmith) Rowhammer fuzzer with **multi-threading** and **channel mapping**. 
It keeps full compatibility with Blacksmith’s patterns and JSON outputs, making it easy to reuse existing results and workflows.

---

## ⚙️ Features

- 🧵 **Multi-threaded sweeping** with disjoint memory regions  
- 🔍 **Channel mapping** through timing-based measurement  
- ⚡ **Thread-local configurations** to prevent interference  
- 🧾 **JSON output** for each thread  
- 📊 **Python tools** for result analysis and plotting  

---

## 🧠 Requirements

- Linux (tested on Ubuntu and Arch)  
- Root privileges
- Hugepages enabled  
- C++17 or newer  
- Libraries: `pthread`, `asmjit`, `nlohmann-json`, `cmake`, `make`  
- Python 3 (for analysis)  
- Correct DRAM addressing function mapping, hardcoded into the source code of both `/Blacksmith` and `/Blacksmith-Original` (The mappings should be same for both)

---

## 🔧 Quick Start

```bash
git clone https://github.com/nima-sayadi/ThreadHammer.git
cd ThreadHammer
```
### 1. Adjust Configuration
Open `conf.cfg` and change values according to your requirements:
- `DEFAULT_RUNTIME` is in seconds and is used only for fuzzing run of Blacksmith to obtain patterns
- `N_THREADS` is used to set maximum threads for your system. Read the description in `conf.cfg`.
Open `/Blacksmith/include/GlobalDefines.hpp` and set `MAX_SWEEP_SIZE` based on your requirements (For Sweeping).

### 2. Run One Fuzzing Iteration
To obtain patterns outputted as `/fuzz-summary.json`, you need a fuzzing run simply by:
```bash
sudo bash run.sh
```
After this, you can split patterns you need for multi-threading with the help of Python tools in `/scripts` or your own tools.

### 3. Run Sweeping Experiments
To start single-threaded or multi-threaded sweeping:
```bash
bash run.sh [-j pattern.json | -p pattern_dir -m] [-r repetition]
```
- `-j` : Path to a single pattern JSON file (single-thread mode)
- `-p` : Path to a folder with pattern files (required for multi-thread mode)
- `-m` : Enable multi-threading (must be used with `-p`)
- `-r` : Number of repetitions (default: 1)
Note: You can adjust the `MAX_SWEEP_SIZE` in `/Blacksmith/include/GlobalDefines.hpp` before starting your sweeping phase.

### Measure Channels (optional - only if your system has 2 DIMMs)
To measure DRAM channel mappings to banks and store the results in `results/`:
```bash
sudo bash measure-channel.sh -o channel-to-bank -r 3
```
- `-o` : Output file name (required)
- `-r` : Number of repetitions (default: 1)

Example output files:
```
results/channel-to-bank-1.json
results/channel-to-bank-2.json
results/channel-to-bank-3.json
```

## Imporant Notes
- Do not remove/un-mount Hugepages during your experiment phases, otherwise your bank to channel mappings and obtained patterns become invalid and you will need to start over from the fuzzing in step 1.
- Do NOT run `remove-hugepage.sh` unless you know what you are doing.
- Always run these scripts with root privileges.
- Do not interrupt a run to avoid partial data.
- If you have your bank functions in a form of Hex values (e.g., `[0x2040, 0x24000, 0x48000, 0x90000]`), you can use `mat_gen.py` to create mapping matrix and inject the output to both Blacksmith source codes.

---

## Author

**Nima Sayadi**  
Master of Applied Research in Computer Science, Hof University of Applied Sciences  
Supervisors: Prof. Dr. Florian Adamsky & Martin Heckel, M.Sc.
(System & Network Security)

---

## Citation

If you use this tool in your research, please cite:

> N. Sayadi, *ThreadHammer: A Multi-Thread Modification of Blacksmith*,  
> Master’s Thesis, Hof University of Applied Sciences, 2025.

---

## License

MIT License — see `LICENSE` for details.