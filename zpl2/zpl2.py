import re


class Zpl2FirmwareMismatch(Exception):
    pass


class Zpl2(list):
    CONTROL_COMMAND = '~'
    FORMAT_COMMAND = '^'

    ORIENTATION_NORMAL = 'N'
    ORIENTATION_ROTATED = 'R'
    ORIENTATION_INVERTED = 'I'
    ORIENTATION_BOTTOMUP = 'B'

    JUSTITIFACTION_LEFT = 'L'
    JUSTITIFACTION_CENTER = 'C'
    JUSTITIFACTION_RIGHT = 'R'
    JUSTITIFACTION_JUSTIFIED = 'J'

    def __init__(self, firmware='unknown'):
        self.firmware = firmware
        self.delimiter = b','
        self.tilde = b'~'
        self.caret = b'^'

    def append(self, item, encoding='ascii'):
        if isinstance(item, str):
            item = item.encode(encoding)
        super(Zpl2, self).append(item)

    def appendCommand(self, commandType, command, *args):
        if (not isinstance(commandType, str)) or (
                not isinstance(command, str)):
            raise TypeError
        if ((commandType != self.CONTROL_COMMAND) and
                (commandType != self.FORMAT_COMMAND)):
            raise ValueError

        data = b''

        if (commandType == self.CONTROL_COMMAND):
            data = data + self.tilde
        else:
            data = data + self.caret

        data = data + command.encode('ascii')

        for i in range(0, len(args)):
            arg = args[i]

            if (isinstance(arg, str)):
                data = data + arg.encode('ascii')
            elif (isinstance(arg, int)):
                data = data + str(arg).encode('ascii')
            elif (isinstance(arg, bytes)) or (isinstance(arg, bytearray)):
                data = data + arg
            else:
                raise Exception("Not supported type")

            if i < len(args) - 1:
                data = data + self.delimiter

        self.append(data)

    def splitFirmware(self, firmware):
        matches = re.search(
            r'^V([0-9]+|x)\.([0-9]+|x)\.([0-9A-Z]+|x)', firmware)
        return matches.groups()

    def checkFirmwareRestrictions(self, restrictions):
        # convert single restriction to list, so we can handle all the same way
        if isinstance(restrictions, str):
            restrictions = [restrictions]

        # no restrions are always fullfilled
        if restrictions == []:
            return True

        # check all firmware restrictions. if at least one is matched, return
        # true
        firmware_parts = self.splitFirmware(self.firmware)
        for restriction in restrictions:
            restriction_parts = self.splitFirmware(restriction)

            part_fulfilled = [True, True, True]

            for i in range(0, 3):
                if (restriction_parts[i] == 'x'):
                    part_fulfilled[i] = True
                elif (restriction_parts[i] == firmware_parts[i]):
                    part_fulfilled[i] = True
                elif ((i < 2) and
                        (int(restriction_parts[i]) <= int(firmware_parts[i]))):
                    part_fulfilled[i] = True
                else:
                    part_fulfilled[i] = False

            if part_fulfilled[0] and part_fulfilled[1] and part_fulfilled[2]:
                return True

        return False

    def getAllBytes(self):
        return b"".join(self)

    def printText(self, x, y, width, fontWidth, fontHeight, text, font='0',
                  orientation=ORIENTATION_NORMAL, encoding='cp850',
                  maximumNumberOfLines=1, trimLineSpace=0,
                  textJustification='L', hangingIndent=0):
        self.FieldOrigin(x, y)
#        self.FieldTypeset(x, y)
        self.FieldBlock(
            width,
            maximumNumberOfLines,
            trimLineSpace,
            textJustification,
            hangingIndent)
        self.ScalableBitmappedFont(font, orientation, fontHeight, fontWidth)
        self.FieldData(text.encode(encoding))
        self.FieldSeparator()

    def printDataMatrixBarCode(self, x, y, height, data,
                               orientation=ORIENTATION_NORMAL, quality=200,
                               columns=0, rows=0):
        self.FieldOrigin(x, y)
        self.DataMatrixBarCode(orientation, height, quality, columns, rows)
        self.FieldData(data.encode('cp850'))
        self.FieldSeparator()

    def printBox(self, x, y, width, height, thickness=1):
        self.FieldOrigin(x, y)
        self.GraphicBox(width, height, thickness)
        self.FieldSeparator()

    def ScalableBitmappedFont(self, font, orientation, h, w):
        if ((not isinstance(font, str)) or
                (not isinstance(orientation, str)) or
                (not isinstance(h, int)) or
                (not isinstance(w, int))):
            raise TypeError
        if not re.match(r'^[A-Z0-9]$', font):
            raise ValueError
        if not re.match(r'^[NRIB]$', orientation):
            raise ValueError
        if (h < 1) or (h > 32000):
            raise ValueError
        if (w < 1) or (w > 32000):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "A" + font, orientation, h, w)

    def DataMatrixBarCode(self, orientation, height, quality, columns, rows,
                          formatId=6, escapeCharacter='~', aspectRatio=1):
        if ((not isinstance(orientation, str)) or
                (not isinstance(height, int)) or
                (not isinstance(columns, int)) or
                (not isinstance(rows, int)) or
                (not isinstance(formatId, int)) or
                (not isinstance(escapeCharacter, str)) or
                (not isinstance(aspectRatio, int))):

            raise TypeError
        if not re.match(r'^[NRIB]$', orientation):
            raise ValueError
        if (formatId < 0) or (formatId > 6):
            raise ValueError
        if (aspectRatio < 1) or (aspectRatio > 2):
            raise ValueError
        if (quality not in [0, 50, 80, 100, 140, 200]):
            raise ValueError
        if (((columns > 0) and (columns < 9)) or
                (((quality > 0) and (quality < 140)) and (columns % 2 == 0)) or
                ((quality == 200) and (columns % 2 != 0)) or
                (columns > 49)):
            raise ValueError
        if ((rows > 0) and (rows < 9)) or (rows > 49):
            raise ValueError

        if self.checkFirmwareRestrictions(["V60.15.5Z", "V53.16.5Z"]):
            self.appendCommand(self.FORMAT_COMMAND, "BX", orientation, height,
                               quality, columns, rows, formatId,
                               escapeCharacter, aspectRatio)
        else:
            self.appendCommand(self.FORMAT_COMMAND, "BX", orientation,
                               height, quality, columns, rows, formatId,
                               escapeCharacter)

    def ChangeCaret(self, caret='^'):
        if (not isinstance(caret, str)):
            raise TypeError
        if (len(caret) > 1) or (ord(caret) > 127):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "CC", caret)
        # update afterwards as otherwise self.caret would be already new caret
        self.caret = caret.encode('ascii')

    def ChangeDelimiter(self, delimiter=','):
        if (not isinstance(delimiter, str)):
            raise TypeError
        if (len(delimiter) > 1) or (ord(delimiter) > 127):
            raise ValueError

        self.delimiter = delimiter.encode('ascii')
        self.appendCommand(self.FORMAT_COMMAND, "CD", delimiter)

    def ChangeTilde(self, tilde='~'):
        if (not isinstance(tilde, str)):
            raise TypeError
        if (len(tilde) > 1) or (ord(tilde) > 127):
            raise ValueError

        self.tilde = tilde.encode('ascii')
        self.appendCommand(self.FORMAT_COMMAND, "CT", tilde)

    def ChangeInternationalFontEncoding(self, encoding):
        ENCODINGS = [
            ['cp850', 13, []],
            ['shift_jis', 15, []],
            ['euc_jp', 16, []],
            ['cp1252', 27, []],
            ['utf_8', 28, ["V60.14.x", "V50.14.x"]],
            ['utf_16', 29, ["V60.14.x", "V50.14.x"]],
            ['utf_32', 30, ["V60.14.x", "V50.14.x"]],
            ['cp1250', 31, ["Vx.16.x"]],
            ['cp1251', 33, ["Vx.16.x"]],
            ['cp1253', 34, ["Vx.16.x"]],
            ['cp1254', 35, ["Vx.16.x"]],
            ['cp1255', 36, ["Vx.16.x"]],
        ]

        characterSet = 0

        for encoding_set in ENCODINGS:
            if (encoding_set[0] == encoding):
                if self.checkFirmwareRestrictions(encoding_set[2]):
                    characterSet = encoding_set[1]
                else:
                    raise Zpl2FirmwareMismatch

        self.appendCommand(self.FORMAT_COMMAND, "CI", characterSet)

    def FieldBlock(self, width, maximumNumberOfLines=1, trimLineSpace=0,
                   textJustification='L', hangingIndent=0):
        if ((not isinstance(width, int)) or
                (not isinstance(maximumNumberOfLines, int)) or
                (not isinstance(trimLineSpace, int)) or
                (not isinstance(textJustification, str)) or
                (not isinstance(hangingIndent, int))):
            raise TypeError
        if (maximumNumberOfLines < 1) or (maximumNumberOfLines > 9999):
            raise ValueError
        if (trimLineSpace < -9999) or (trimLineSpace > 9999):
            raise ValueError
        if (not re.match(r'^[LCRJ]$', textJustification)):
            raise ValueError
        if (hangingIndent < 0) or (hangingIndent > 9999):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "FB", width,
                           maximumNumberOfLines, trimLineSpace,
                           textJustification, hangingIndent)

    def FieldData(self, data):
        if (not isinstance(data, str)) and (not isinstance(data, bytes)):
            raise TypeError
        if len(data) > 3072:
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "FD", data)

    def FieldOrigin(self, x=0, y=0, z=0):
        if (not isinstance(x, int)) or (
                not isinstance(y, int)) or (not isinstance(z, int)):
            raise TypeError
        if (x < 0) or (x > 32000):
            raise ValueError
        if (y < 0) or (y > 32000):
            raise ValueError
        if (z < 0) or (z > 2):
            raise ValueError

        if self.checkFirmwareRestrictions(["V60.14.x", "V50.14.x"]):
            self.appendCommand(self.FORMAT_COMMAND, "FO", x, y, z)
        else:
            self.appendCommand(self.FORMAT_COMMAND, "FO", x, y)

    def FieldTypeset(self, x=0, y=0, z=0):
        if (not isinstance(x, int)) or (
                not isinstance(y, int)) or (not isinstance(z, int)):
            raise TypeError
        if (x < 0) or (x > 32000):
            raise ValueError
        if (y < 0) or (y > 32000):
            raise ValueError
        if (z < 0) or (z > 2):
            raise ValueError

        if self.checkFirmwareRestrictions(["V60.14.x", "V50.14.x"]):
            self.appendCommand(self.FORMAT_COMMAND, "FT", x, y, z)
        else:
            self.appendCommand(self.FORMAT_COMMAND, "FT", x, y)

    def FieldSeparator(self):
        self.appendCommand(self.FORMAT_COMMAND, "FS")

    def GraphicBox(self, w, h, thickness=1, color='B', rounding=0):
        if ((not isinstance(w, int)) or
                (not isinstance(h, int)) or
                (not isinstance(thickness, int)) or
                (not isinstance(color, str)) or
                (not isinstance(rounding, int))):
            raise TypeError
        if (thickness < 1) or (thickness > 32000):
            raise ValueError
        if (w < thickness) or (w > 32000):
            raise ValueError
        if (h < thickness) or (h > 32000):
            raise ValueError
        if not re.match(r'^[BW]$', color):
            raise ValueError
        if (rounding < 0) or (rounding > 8):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "GB", w,
                           h, thickness, color, rounding)

    def GraphicField(self, compressionType, binaryByteCount,
                     graphicFieldCount, bytesPerRow, data, optimizeAscii=True):
        if ((not isinstance(compressionType, str)) or
                (not isinstance(binaryByteCount, int)) or
                (not isinstance(graphicFieldCount, int)) or
                (not isinstance(bytesPerRow, int)) or
                (not isinstance(data, bytes) and not isinstance(data, bytearray))):
            raise TypeError
        if not re.match('^[ABC]$', compressionType):
            raise ValueError
        if (binaryByteCount < 1):  # or (binaryByteCount > 99999):
            raise ValueError
        if (graphicFieldCount < 1):  # or (graphicFieldCount > 99999):
            raise ValueError
        if (bytesPerRow < 1):  # or (bytesPerRow > 99999):
            raise ValueError
        if (len(data) != binaryByteCount):
            raise ValueError

        if compressionType == 'C' or compressionType == 'B':
            raise Exception('Compression type not implemented.')

        if compressionType == 'A':
            if optimizeAscii:
                dataArgument = bytearray()
                lines = (data[i:i + bytesPerRow]
                         for i in range(0, len(data), bytesPerRow))
                for line in lines:
                    line = line.rstrip(b'\0') or b'\0'
                    dataArgument.extend(line.hex().encode('ascii'))
                    if (len(line) < bytesPerRow):
                        dataArgument.extend(b',')
            else:
                dataArgument = data.hex()

        self.appendCommand(
            self.FORMAT_COMMAND,
            "GF",
            compressionType,
            binaryByteCount,
            graphicFieldCount,
            bytesPerRow,
            dataArgument)

    def ConfigurationUpdate(self, configuration):
        if (not isinstance(configuration, str)):
            raise TypeError
        if not re.match(r'^[FNRS]$', configuration):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "JU", configuration)

    def LabelHome(self, x=0, y=0):
        if (not isinstance(x, int)) or (not isinstance(y, int)):
            raise TypeError
        if (x < 0) or (x > 32000):
            raise ValueError
        if (y < 0) or (y > 32000):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "LH", x, y)

    def LabelLength(self, x):
        if (not isinstance(x, int)):
            raise TypeError
        if (x < 1) or (x > 32000):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "LL", x)

    def LabelTop(self, x):
        if (not isinstance(x, int)):
            raise TypeError
        if (x < -120) or (x > 120):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "LT", x)

    def PrintWidth(self, labelWidth):
        if (not isinstance(labelWidth, int)):
            raise TypeError
        if (labelWidth < 2):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "PW", labelWidth)

    def SetDarkness(self, darkness):
        if (not isinstance(darkness, int)):
            raise TypeError
        if (darkness < 0) and (darkness > 30):
            raise ValueError

        self.appendCommand(self.CONTROL_COMMAND, "SD", ('%02u' % darkness))

    def MediaType(self, mediaType):
        if (mediaType != "T") and (mediaType != "D"):
            raise ValueError

        self.appendCommand(self.FORMAT_COMMAND, "MT", mediaType)

    def StartFormat(self):
        self.appendCommand(self.FORMAT_COMMAND, "XA")

    def EndFormat(self):
        self.appendCommand(self.FORMAT_COMMAND, "XZ")
