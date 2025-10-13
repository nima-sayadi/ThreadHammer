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
- Correct DRAM addressing function mapping, hardcoded into the source code

---

## 🔧 Quick Start

```bash
git clone https://github.com/<yourusername>/ThreadHammer.git
cd ThreadHammer
```

### 1. Measure DRAM channels (optional)
`sudo ./threadhammer --measure-channels`