# Endian examples for a 32-bit value:
# little: 0x12345678 -> bytes 78 56 34 12
# big: 0x12345678 -> bytes 12 34 56 78
# baremetal-little and baremetal-big use the full fixed-width representation.
# dense-little removes trailing zero bytes; dense-big removes leading zero bytes.
# For example, dense-little packs 0x00123400 as bytes 00 34 12.
# Dense unpacking restores omitted zero or sign-extension bytes.


def ValidateEndian(Endian: str) -> tuple[str, bool]:
    """Validate an endian name and return its byte order and compactness.

    The accepted names are ``little``, ``big``, ``baremetal-little``,
    ``baremetal-big``, ``dense-little``, and ``dense-big``. Bare-metal modes
    retain fixed-width output; dense modes omit redundant edge bytes.

    Args:
        Endian: One of the six supported endian names.

    Returns:
        A pair containing ``little`` or ``big`` and a dense-mode flag.

    Raises:
        TypeError: If Endian is not a string.
        ValueError: If Endian is not one of the supported names.

    Examples:
        >>> ValidateEndian("dense-big")
        ('big', True)
    """
    if type(Endian) is not str:
        raise TypeError("Endian must be a string")
    if Endian == "little":
        return "little", False
    if Endian == "big":
        return "big", False
    if Endian == "baremetal-little":
        return "little", False
    if Endian == "baremetal-big":
        return "big", False
    if Endian == "dense-little":
        return "little", True
    if Endian == "dense-big":
        return "big", True
    raise ValueError("Endian must be little, big, baremetal-little, baremetal-big, dense-little, or dense-big")


def RoundRatio(Numerator: int, Denominator: int) -> int:
    """Round a positive integer ratio to the nearest integer, ties to even.

    Args:
        Numerator: A nonnegative numerator.
        Denominator: A positive denominator.

    Returns:
        The nearest integer, using round-to-nearest-even for exact ties.

    Raises:
        ValueError: If the numerator is negative or denominator is not positive.

    Examples:
        >>> RoundRatio(5, 2)
        2
        >>> RoundRatio(7, 2)
        4
    """
    if type(Numerator) is not int or type(Denominator) is not int:
        raise TypeError("Numerator and Denominator must be integers")
    if Numerator < 0 or Denominator <= 0:
        raise ValueError("RoundRatio requires a nonnegative numerator and positive denominator")
    Quotient, Remainder = divmod(Numerator, Denominator)
    TwiceRemainder = Remainder * 2
    if TwiceRemainder > Denominator or (TwiceRemainder == Denominator and Quotient & 1):
        Quotient += 1
    return Quotient


def ValidateFloatFormat(ExponentBits: int, FractionBits: int) -> int:
    """Validate an IEEE-754 format shape and return its bit width.

    Args:
        ExponentBits: An integer exponent width of at least two bits.
        FractionBits: A positive integer fraction width.

    Returns:
        The sign, exponent, and fraction width, which must be byte-aligned.

    Raises:
        TypeError: If either width is not an integer.
        ValueError: If either width is invalid or the total is not byte-aligned.

    Examples:
        >>> ValidateFloatFormat(5, 10)
        16
    """
    if type(ExponentBits) is not int or type(FractionBits) is not int:
        raise TypeError("ExponentBits and FractionBits must be integers")
    if ExponentBits < 2 or FractionBits < 1:
        raise ValueError("ExponentBits must be at least two and FractionBits must be positive")
    BitCount = 1 + ExponentBits + FractionBits
    if BitCount % 8 != 0:
        raise ValueError("The selected float format must have a byte-aligned width")
    return BitCount


def PackInteger(Value: int, BitCount: int, Endian: str, Signed: bool) -> bytes:
    """Encode an integer using a fixed-width or dense two's-complement format.

    Args:
        Value: An integer within the selected signed or unsigned range.
        BitCount: The output field width in bits; it must be byte-aligned.
        Endian: One of the supported endian names.
        Signed: Whether Value is interpreted as a signed integer.

    Returns:
        Encoded bytes. Dense modes omit redundant zero or sign-extension bytes.

    Raises:
        TypeError: If Value is not an integer or Signed is not a bool.
        ValueError: If BitCount is invalid or Endian is unsupported.
        OverflowError: If Value cannot be represented in BitCount bits.

    Examples:
        >>> PackInteger(4660, 32, "dense-little", False)
        b'4\\x12'
    """
    if type(Value) is not int:
        raise TypeError("Value must be an integer")
    if type(BitCount) is not int:
        raise TypeError("BitCount must be an integer")
    if BitCount <= 0 or BitCount % 8 != 0:
        raise ValueError("BitCount must be a positive multiple of eight")
    if type(Signed) is not bool:
        raise TypeError("Signed must be a bool")
    ByteOrder, IsDense = ValidateEndian(Endian)
    if Signed:
        Minimum = -(1 << (BitCount - 1))
        Maximum = (1 << (BitCount - 1)) - 1
    else:
        Minimum = 0
        Maximum = (1 << BitCount) - 1
    if Value < Minimum or Value > Maximum:
        raise OverflowError("Value is outside the selected integer range")

    ByteCount = BitCount // 8
    Encoded = Value.to_bytes(ByteCount, ByteOrder, signed=Signed)
    if not IsDense:
        return Encoded

    if Signed:
        SignByte = 255 if Value < 0 else 0
        if ByteOrder == "little":
            while len(Encoded) > 1 and Encoded[-1] == SignByte and (Encoded[-2] & 128) == (SignByte & 128):
                Encoded = Encoded[:-1]
        else:
            while len(Encoded) > 1 and Encoded[0] == SignByte and (Encoded[1] & 128) == (SignByte & 128):
                Encoded = Encoded[1:]
    elif ByteOrder == "little":
        while len(Encoded) > 1 and Encoded[-1] == 0:
            Encoded = Encoded[:-1]
    else:
        while len(Encoded) > 1 and Encoded[0] == 0:
            Encoded = Encoded[1:]
    return Encoded


def UnPackInteger(Value: bytes, BitCount: int, Endian: str, Signed: bool) -> int:
    """Decode a fixed-width or dense integer byte sequence.

    Args:
        Value: A bytes object of the required width, or a shorter dense value.
        BitCount: The original field width in bits; it must be byte-aligned.
        Endian: One of the supported endian names.
        Signed: Whether the original value was signed.

    Returns:
        The decoded integer.

    Raises:
        TypeError: If Value is not bytes or Signed is not a bool.
        ValueError: If the width, byte count, or Endian is invalid.

    Examples:
        >>> UnPackInteger(b"4\\x12", 32, "dense-little", False)
        4660
    """
    if type(Value) is not bytes:
        raise TypeError("Value must be bytes")
    if type(BitCount) is not int:
        raise TypeError("BitCount must be an integer")
    if BitCount <= 0 or BitCount % 8 != 0:
        raise ValueError("BitCount must be a positive multiple of eight")
    if type(Signed) is not bool:
        raise TypeError("Signed must be a bool")
    ByteOrder, IsDense = ValidateEndian(Endian)
    ByteCount = BitCount // 8
    if len(Value) == 0 or len(Value) > ByteCount or (not IsDense and len(Value) != ByteCount):
        raise ValueError("Value has an invalid byte count for the selected format")
    if len(Value) < ByteCount:
        if Signed:
            MostSignificantByte = Value[-1] if ByteOrder == "little" else Value[0]
            FillByte = 255 if MostSignificantByte & 128 else 0
        else:
            FillByte = 0
        Padding = bytes([FillByte]) * (ByteCount - len(Value))
        Value = Value + Padding if ByteOrder == "little" else Padding + Value
    return int.from_bytes(Value, ByteOrder, signed=Signed)


def FloatToBits(Value: float, ExponentBits: int, FractionBits: int) -> int:
    """Convert a Python float to a rounded IEEE-754 binary interchange value.

    Finite values are rounded to nearest, ties to even. Values that round
    beyond the largest finite number raise OverflowError. Infinities and NaNs
    are encoded using IEEE-754 special values.

    Args:
        Value: A Python float.
        ExponentBits: The number of exponent bits in the target format.
        FractionBits: The number of stored fraction bits.

    Returns:
        The complete sign, exponent, and fraction bit pattern as an integer.

    Raises:
        TypeError: If Value is not a float.
        OverflowError: If a finite value rounds beyond the target's finite range.

    Examples:
        >>> FloatToBits(1.5, 5, 10) == 15872
        True
    """
    if type(Value) is not float:
        raise TypeError("Value must be a float")
    ValidateFloatFormat(ExponentBits, FractionBits)
    SignBit = 1 if Value < 0 or (Value == 0.0 and Value.hex()[0] == "-") else 0
    SignShift = ExponentBits + FractionBits
    SignValue = SignBit << SignShift
    ExponentMask = (1 << ExponentBits) - 1
    Bias = (1 << (ExponentBits - 1)) - 1
    MinimumExponent = 1 - Bias
    MaximumExponent = Bias

    if Value != Value:
        return SignValue | (ExponentMask << FractionBits) | (1 << (FractionBits - 1))
    if Value == float("inf") or Value == float("-inf"):
        return SignValue | (ExponentMask << FractionBits)
    if Value == 0.0:
        return SignValue

    Numerator, Denominator = abs(Value).as_integer_ratio()
    BinaryExponent = Numerator.bit_length() - Denominator.bit_length()
    if BinaryExponent >= 0:
        if Numerator < Denominator << BinaryExponent:
            BinaryExponent -= 1
    elif Numerator << -BinaryExponent < Denominator:
        BinaryExponent -= 1

    if BinaryExponent >= MinimumExponent:
        Shift = FractionBits - BinaryExponent
        if Shift >= 0:
            RoundedSignificand = RoundRatio(Numerator << Shift, Denominator)
        else:
            RoundedSignificand = RoundRatio(Numerator, Denominator << -Shift)
        if RoundedSignificand == 1 << (FractionBits + 1):
            RoundedSignificand >>= 1
            BinaryExponent += 1
        if BinaryExponent > MaximumExponent:
            raise OverflowError("Value exceeds the largest finite value of the target float format")
        EncodedExponent = BinaryExponent + Bias
        EncodedFraction = RoundedSignificand - (1 << FractionBits)
    else:
        Shift = FractionBits - MinimumExponent
        RoundedSignificand = RoundRatio(Numerator << Shift, Denominator)
        if RoundedSignificand == 0:
            return SignValue
        if RoundedSignificand >= 1 << FractionBits:
            EncodedExponent = 1
            EncodedFraction = 0
        else:
            EncodedExponent = 0
            EncodedFraction = RoundedSignificand
    return SignValue | (EncodedExponent << FractionBits) | EncodedFraction


def BitsToFloat(Value: int, ExponentBits: int, FractionBits: int) -> float:
    """Convert an IEEE-754 binary interchange value into a Python float.

    Args:
        Value: The complete nonnegative sign, exponent, and fraction bit pattern.
        ExponentBits: The number of exponent bits in the encoded format.
        FractionBits: The number of stored fraction bits.

    Returns:
        The represented value as a Python float, including infinity or NaN.

    Raises:
        ValueError: If Value is not an integer or contains bits outside the format.

    Examples:
        >>> BitsToFloat(15872, 5, 10)
        1.5
    """
    ValidateFloatFormat(ExponentBits, FractionBits)
    if type(Value) is not int:
        raise TypeError("Value must be an integer")
    if Value < 0:
        raise ValueError("Value must be a nonnegative integer")
    TotalBits = 1 + ExponentBits + FractionBits
    if Value >= 1 << TotalBits:
        raise ValueError("Value contains bits outside the selected float format")
    Sign = -1.0 if Value >> (TotalBits - 1) else 1.0
    FractionMask = (1 << FractionBits) - 1
    ExponentMask = (1 << ExponentBits) - 1
    FractionValue = Value & FractionMask
    ExponentValue = (Value >> FractionBits) & ExponentMask
    Bias = (1 << (ExponentBits - 1)) - 1

    if ExponentValue == ExponentMask:
        if FractionValue:
            return float("nan")
        return float("-inf") if Sign < 0 else float("inf")
    if ExponentValue == 0:
        if FractionValue == 0:
            return -0.0 if Sign < 0 else 0.0
        Significand = FractionValue
        BinaryExponent = 1 - Bias - FractionBits
    else:
        Significand = (1 << FractionBits) | FractionValue
        BinaryExponent = ExponentValue - Bias - FractionBits
    return Sign * float(Significand) * (2.0 ** BinaryExponent)


def PackFloat(Value: float, ExponentBits: int, FractionBits: int, Endian: str) -> bytes:
    """Encode a float as IEEE-754 bytes without external modules.

    Args:
        Value: A Python float to encode.
        ExponentBits: The target format's exponent width.
        FractionBits: The target format's stored fraction width.
        Endian: One of the supported endian names.

    Returns:
        The encoded byte sequence, possibly shortened in dense mode.

    Raises:
        TypeError: If Value is not a float.
        OverflowError: If a finite value exceeds the format's finite range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackFloat(1.5, 5, 10, "little")
        b'\\x00>'
    """
    BitCount = ValidateFloatFormat(ExponentBits, FractionBits)
    FloatBits = FloatToBits(Value, ExponentBits, FractionBits)
    return PackInteger(FloatBits, BitCount, Endian, False)


def UnPackFloat(Value: bytes, ExponentBits: int, FractionBits: int, Endian: str) -> float:
    """Decode IEEE-754 bytes into a Python float.

    Args:
        Value: A complete-width byte sequence, or a shorter dense sequence.
        ExponentBits: The encoded format's exponent width.
        FractionBits: The encoded format's stored fraction width.
        Endian: One of the supported endian names.

    Returns:
        The represented Python float; binary16 and binary32 values are exactly
        representable in Python's binary64 float.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If the format width, byte count, or Endian is invalid.

    Examples:
        >>> UnPackFloat(b"\\x00>", 5, 10, "little")
        1.5
    """
    BitCount = ValidateFloatFormat(ExponentBits, FractionBits)
    FloatBits = UnPackInteger(Value, BitCount, Endian, False)
    return BitsToFloat(FloatBits, ExponentBits, FractionBits)


def PackInt8(Value: int, Endian: str = "little") -> bytes:
    """Pack a signed 8-bit integer.

    Args:
        Value: An integer from -128 through 127.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded byte.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the signed 8-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackInt8(-1)
        b'\\xff'
    """
    return PackInteger(Value, 8, Endian, True)


def PackInt16(Value: int, Endian: str = "little") -> bytes:
    """Pack a signed 16-bit integer.

    Args:
        Value: An integer from -32768 through 32767.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the signed 16-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackInt16(-4660, "big")
        b'\\xed\\xcc'
    """
    return PackInteger(Value, 16, Endian, True)


def PackInt32(Value: int, Endian: str = "little") -> bytes:
    """Pack a signed 32-bit integer.

    Args:
        Value: An integer from -2147483648 through 2147483647.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the signed 32-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackInt32(305419896, "big")
        b'\\x124Vx'
    """
    return PackInteger(Value, 32, Endian, True)


def PackInt64(Value: int, Endian: str = "little") -> bytes:
    """Pack a signed 64-bit integer.

    Args:
        Value: An integer from -2**63 through 2**63 - 1.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the signed 64-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackInt64(1, "big")
        b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01'
    """
    return PackInteger(Value, 64, Endian, True)


def PackUInt8(Value: int, Endian: str = "little") -> bytes:
    """Pack an unsigned 8-bit integer.

    Args:
        Value: An integer from 0 through 255.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded byte.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the unsigned 8-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackUInt8(255)
        b'\\xff'
    """
    return PackInteger(Value, 8, Endian, False)


def PackUInt16(Value: int, Endian: str = "little") -> bytes:
    """Pack an unsigned 16-bit integer.

    Args:
        Value: An integer from 0 through 65535.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the unsigned 16-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackUInt16(4660, "big")
        b'\\x124'
    """
    return PackInteger(Value, 16, Endian, False)


def PackUInt32(Value: int, Endian: str = "little") -> bytes:
    """Pack an unsigned 32-bit integer.

    Args:
        Value: An integer from 0 through 4294967295.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the unsigned 32-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackUInt32(305419896, "big")
        b'\\x124Vx'
    """
    return PackInteger(Value, 32, Endian, False)


def PackUInt64(Value: int, Endian: str = "little") -> bytes:
    """Pack an unsigned 64-bit integer.

    Args:
        Value: An integer from 0 through 2**64 - 1.
        Endian: A supported byte order and packing mode.

    Returns:
        The encoded bytes.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the unsigned 64-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackUInt64(1, "big")
        b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01'
    """
    return PackInteger(Value, 64, Endian, False)


def PackFloat16(Value: float, Endian: str = "little") -> bytes:
    """Pack a Python float into IEEE-754 binary16 format.

    Args:
        Value: A float rounded to binary16 precision using ties-to-even.
        Endian: A supported byte order and packing mode.

    Returns:
        Two encoded bytes, or fewer in dense mode.

    Raises:
        TypeError: If Value is not a float.
        OverflowError: If Value rounds outside the finite binary16 range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> UnPackFloat16(PackFloat16(1.5))
        1.5
    """
    return PackFloat(Value, 5, 10, Endian)


def PackFloat32(Value: float, Endian: str = "little") -> bytes:
    """Pack a Python float into IEEE-754 binary32 format.

    Args:
        Value: A float rounded to binary32 precision using ties-to-even.
        Endian: A supported byte order and packing mode.

    Returns:
        Four encoded bytes, or fewer in dense mode.

    Raises:
        TypeError: If Value is not a float.
        OverflowError: If Value rounds outside the finite binary32 range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> UnPackFloat32(PackFloat32(1.5))
        1.5
    """
    return PackFloat(Value, 8, 23, Endian)


def PackFloat64(Value: float, Endian: str = "little") -> bytes:
    """Pack a Python float into IEEE-754 binary64 format.

    Args:
        Value: A Python binary64 float, represented without additional precision loss.
        Endian: A supported byte order and packing mode.

    Returns:
        Eight encoded bytes, or fewer in dense mode.

    Raises:
        TypeError: If Value is not a float.
        OverflowError: If a finite value rounds outside the binary64 range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> UnPackFloat64(PackFloat64(0.1)) == 0.1
        True
    """
    return PackFloat(Value, 11, 52, Endian)


def PackBool(Value: bool, Endian: str = "little") -> bytes:
    """Pack one bool as a canonical zero or one byte.

    Args:
        Value: A bool value; integers 0 and 1 are not accepted as substitutes.
        Endian: A supported mode, validated even though a single byte has no order.

    Returns:
        ``b"\\x00"`` for False or ``b"\\x01"`` for True.

    Raises:
        TypeError: If Value is not a bool.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackBool(True)
        b'\\x01'
    """
    if type(Value) is not bool:
        raise TypeError("Value must be a bool")
    ValidateEndian(Endian)
    return b"\x01" if Value else b"\x00"


def PackBools(Value: list[bool], Endian: str = "little") -> bytes:
    """Pack bools consecutively into bytes, with the first bool in the low bit.

    Each byte stores up to eight list entries. A final partial byte is padded
    with zero bits. The endian name selects byte order semantics for bit order:
    little modes place each group's first bool in its least significant bit;
    big modes place it in its most significant bit. Dense modes trim redundant
    zero bytes at the endian-dependent edge.

    Args:
        Value: A list containing only bool values.
        Endian: A supported byte order and packing mode.

    Returns:
        The packed byte sequence; an empty list produces empty bytes.

    Raises:
        TypeError: If Value is not a list or contains a non-bool value.
        ValueError: If Endian is unsupported.

    Examples:
        >>> PackBools([True, False, True])
        b'\\x05'
    """
    if type(Value) is not list:
        raise TypeError("Value must be a list of bool values")
    if any(type(BooleanValue) is not bool for BooleanValue in Value):
        raise TypeError("Every item in Value must be a bool")
    ByteOrder, IsDense = ValidateEndian(Endian)
    Encoded = bytearray()
    for StartIndex in range(0, len(Value), 8):
        Group = Value[StartIndex:StartIndex + 8]
        ByteValue = 0
        for BitIndex, BooleanValue in enumerate(Group):
            Shift = BitIndex if ByteOrder == "little" else 7 - BitIndex
            if BooleanValue:
                ByteValue |= 1 << Shift
        Encoded.append(ByteValue)
    if ByteOrder == "big":
        Encoded.reverse()
    if IsDense:
        if ByteOrder == "little":
            while len(Encoded) > 1 and Encoded[-1] == 0:
                Encoded.pop()
        else:
            while len(Encoded) > 1 and Encoded[0] == 0:
                del Encoded[0]
    return bytes(Encoded)


def PackPointer(Value: int, Endian: str = "little") -> bytes:
    """Pack a pointer-sized value as an unsigned 64-bit integer.

    Args:
        Value: An integer from 0 through 2**64 - 1.
        Endian: A supported byte order and packing mode.

    Returns:
        Eight bytes, or fewer in dense mode.

    Raises:
        TypeError: If Value is not an integer.
        OverflowError: If Value is outside the unsigned 64-bit range.
        ValueError: If Endian is unsupported.

    Examples:
        >>> len(PackPointer(1))
        8
    """
    return PackInteger(Value, 64, Endian, False)


def UnPackInt8(Value: bytes, Endian: str = "little") -> int:
    """Unpack a signed 8-bit integer.

    Args:
        Value: Exactly one byte, or one dense byte.
        Endian: A supported byte order and packing mode.

    Returns:
        The signed integer in the range -128 through 127.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackInt8(b'\\xff')
        -1
    """
    return UnPackInteger(Value, 8, Endian, True)


def UnPackInt16(Value: bytes, Endian: str = "little") -> int:
    """Unpack a signed 16-bit integer.

    Args:
        Value: Two bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The signed integer in the range -32768 through 32767.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackInt16(b'\\xed\\xcc', "big")
        -4660
    """
    return UnPackInteger(Value, 16, Endian, True)


def UnPackInt32(Value: bytes, Endian: str = "little") -> int:
    """Unpack a signed 32-bit integer.

    Args:
        Value: Four bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The signed integer in the range -2**31 through 2**31 - 1.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackInt32(b'\\x124Vx', "big")
        305419896
    """
    return UnPackInteger(Value, 32, Endian, True)


def UnPackInt64(Value: bytes, Endian: str = "little") -> int:
    """Unpack a signed 64-bit integer.

    Args:
        Value: Eight bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The signed integer in the range -2**63 through 2**63 - 1.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackInt64(b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01', "big")
        1
    """
    return UnPackInteger(Value, 64, Endian, True)


def UnPackUInt8(Value: bytes, Endian: str = "little") -> int:
    """Unpack an unsigned 8-bit integer.

    Args:
        Value: Exactly one byte.
        Endian: A supported byte order and packing mode.

    Returns:
        An integer in the range 0 through 255.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackUInt8(b'\\xff')
        255
    """
    return UnPackInteger(Value, 8, Endian, False)


def UnPackUInt16(Value: bytes, Endian: str = "little") -> int:
    """Unpack an unsigned 16-bit integer.

    Args:
        Value: Two bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        An integer in the range 0 through 65535.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackUInt16(b'\\x124', "big")
        4660
    """
    return UnPackInteger(Value, 16, Endian, False)


def UnPackUInt32(Value: bytes, Endian: str = "little") -> int:
    """Unpack an unsigned 32-bit integer.

    Args:
        Value: Four bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        An integer in the range 0 through 4294967295.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackUInt32(b'\\x124Vx', "big")
        305419896
    """
    return UnPackInteger(Value, 32, Endian, False)


def UnPackUInt64(Value: bytes, Endian: str = "little") -> int:
    """Unpack an unsigned 64-bit integer.

    Args:
        Value: Eight bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        An integer in the range 0 through 2**64 - 1.

    Raises:
        TypeError: If Value has the wrong type.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackUInt64(b'\\x00\\x00\\x00\\x00\\x00\\x00\\x00\\x01', "big")
        1
    """
    return UnPackInteger(Value, 64, Endian, False)


def UnPackFloat16(Value: bytes, Endian: str = "little") -> float:
    """Unpack IEEE-754 binary16 bytes into a Python float.

    Args:
        Value: Two bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The binary16 value represented as a Python float.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackFloat16(b'\\x00>')
        1.5
    """
    return UnPackFloat(Value, 5, 10, Endian)


def UnPackFloat32(Value: bytes, Endian: str = "little") -> float:
    """Unpack IEEE-754 binary32 bytes into a Python float.

    Args:
        Value: Four bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The binary32 value represented as a Python float.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackFloat32(b'\\x00\\x00\\xc0?')
        1.5
    """
    return UnPackFloat(Value, 8, 23, Endian)


def UnPackFloat64(Value: bytes, Endian: str = "little") -> float:
    """Unpack IEEE-754 binary64 bytes into a Python float.

    Args:
        Value: Eight bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        The exact represented binary64 Python float.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackFloat64(PackFloat64(0.1)) == 0.1
        True
    """
    return UnPackFloat(Value, 11, 52, Endian)


def UnPackBool(Value: bytes, Endian: str = "little") -> bool:
    """Unpack one canonical bool byte.

    Args:
        Value: Exactly b"\\x00" or b"\\x01".
        Endian: A supported mode; it is validated for consistent argument checks.

    Returns:
        False for zero and True for one.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has the wrong length, is noncanonical, or Endian is invalid.

    Examples:
        >>> UnPackBool(b'\\x01')
        True
    """
    if type(Value) is not bytes:
        raise TypeError("Value must be bytes")
    ValidateEndian(Endian)
    if len(Value) != 1 or Value[0] > 1:
        raise ValueError("Value must contain exactly one canonical bool byte")
    return Value[0] == 1


def UnPackBools(Value: bytes, Endian: str = "little") -> list[bool]:
    """Unpack every bit into bools in the same order used by PackBools.

    The returned list contains eight bools per encoded byte. Because the bit
    count is not stored, padding bits in a final partial byte are returned too.
    Little modes read each byte from its low bit upward; big modes read from
    its high bit downward. Dense modes contain only the bytes retained by pack.

    Args:
        Value: The packed bytes; empty bytes produce an empty list.
        Endian: A supported byte order and packing mode.

    Returns:
        A list containing one bool for each bit in Value.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Endian is unsupported.

    Examples:
        >>> UnPackBools(b'\\x05')
        [True, False, True, False, False, False, False, False]
    """
    if type(Value) is not bytes:
        raise TypeError("Value must be bytes")
    ByteOrder = ValidateEndian(Endian)[0]
    if ByteOrder == "big":
        Value = Value[::-1]
    Result = []
    for ByteValue in Value:
        for BitIndex in range(8):
            Shift = BitIndex if ByteOrder == "little" else 7 - BitIndex
            Result.append(bool((ByteValue >> Shift) & 1))
    return Result


def UnPackPointer(Value: bytes, Endian: str = "little") -> int:
    """Unpack a pointer-sized unsigned 64-bit integer.

    Args:
        Value: Eight bytes, or a shorter dense representation.
        Endian: A supported byte order and packing mode.

    Returns:
        An integer in the range 0 through 2**64 - 1.

    Raises:
        TypeError: If Value is not bytes.
        ValueError: If Value has an invalid byte count or Endian is unsupported.

    Examples:
        >>> UnPackPointer(PackPointer(123))
        123
    """
    return UnPackInteger(Value, 64, Endian, False)
