# Obex.BinaryPacking 🚀

A lightweight, high-performance binary serialization and packing framework for Python, designed **completely independently of the standard `struct` module**. 

`BinaryPacking` provides explicit, bare-metal control over byte-level data layout, endianness, bit manipulation, and memory representation, making it ideal for custom network protocols, embedded systems, file formats, and low-level performance optimization.

---

## ✨ Key Features

- **Zero Dependencies:** Built entirely from scratch using pure Python bitwise operations, math, and byte conversions.
- **High Performance (C-Powered):** Critical packing and unpacking routines are written in **C** and published on PyPI for maximum speed and efficiency.
- **Advanced Endianness & Layout Contracts:**
  - Standard `little` and `big` endian byte ordering.
  - **Bare-metal modes** (`baremetal-little`, `baremetal-big`) for hardware-aligned structures.
  - **Dense modes** (`dense-little`, `dense-big`) that strip redundant trailing/leading zero or sign-extension bytes to minimize data footprint.
- **Custom IEEE-754 Float Handling:** Native Python/C implementation of float quantization, rounding (ties-to-even), and bit conversions for `binary16`, `binary32`, and `binary64` without relying on standard C libraries' `struct` limitations.
- **Bit-level Packing:** Compact boolean array packing (`PackBools`) where individual bits are mapped directly to bytes.
- **Robust Error Handling:** Strict validation of types (`TypeError`), value ranges (`ValueError`), and overflow conditions (`OverflowError`).

---

## 📦 Installation

You can install the package directly from PyPI using `pip`:

```bash
pip install BinaryPacking
