# Obex.BinaryPacking 🚀

A lightweight, high-performance binary serialization and packing framework for Python, designed **completely independently of the standard `struct` module**. 

`Obex.BinaryPacking` provides explicit, bare-metal control over byte-level data layout, endianness, bit manipulation, and memory representation, making it ideal for custom network protocols, embedded systems, file formats, and low-level performance optimization.

---

## ✨ Key Features

- **Zero Dependencies:** Built entirely from scratch using pure Python bitwise operations, math, and byte conversions.
- **Advanced Endianness & Layout Contracts:**
  - Standard `little` and `big` endian byte ordering.
  - **Bare-metal modes** (`baremetal-little`, `baremetal-big`) for hardware-aligned structures.
  - **Dense modes** (`dense-little`, `dense-big`) that strip redundant trailing/leading zero or sign-extension bytes to minimize data footprint.
- **Custom IEEE-754 Float Handling:** Native Python implementation of float quantization, rounding (ties-to-even), and bit conversions for `binary16`, `binary32`, and `binary64` without relying on C libraries.
- **Bit-level Packing:** Compact boolean array packing (`PackBools`) where individual bits are mapped directly to bytes.
- **Robust Error Handling:** Strict validation of types (`TypeError`), value ranges (`ValueError`), and overflow conditions (`OverflowError`).

---

## 📦 Installation

Simply drop `BinaryPacking.py` into your project directory or site-packages. No external dependencies are required.

---

## 🛠️ Usage Examples

### 1. Basic Integer Packing
```python
from BinaryPacking import PackUInt32, UnPackUInt32

# Pack an unsigned 32-bit integer in Big-Endian format
packed = PackUInt32(0x12345678, "big")
print(packed)  # b'\x12\x34\x56\x78'

# Unpack it back
value = UnPackUInt32(packed, "big")
print(value)  # 305419896
