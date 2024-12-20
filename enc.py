rainbow_encoding = {
    'A': '001', 'B': '002', 'C': '003', 'D': '004', 'E': '005', 'F': '006', 'G': '007', 'H': '008', 'I': '009',
    'J': '0010', 'K': '0011', 'L': '0012', 'M': '0013', 'N': '0014', 'O': '0015', 'P': '0016', 'Q': '0017',
    'R': '0018', 'S': '0019', 'T': '0020', 'U': '0021', 'V': '0022', 'W': '0023', 'X': '0024', 'Y': '0025',
    'Z': '0026', 'a': '010', 'b': '020', 'c': '030', 'd': '040', 'e': '050', 'f': '060', 'g': '070', 'h': '080',
    'i': '090', 'j': '0100', 'k': '0110', 'l': '0120', 'm': '0130', 'n': '0140', 'o': '0150', 'p': '0160',
    'q': '0170', 'r': '0180', 's': '0190', 't': '0200', 'u': '0210', 'v': '0220', 'w': '0230', 'x': '0240',
    'y': '0250', 'z': '0260'
}

def encode_password(password):
    encoded = ""
    for char in password:
        encoded += rainbow_encoding.get(char, char) 
    return encoded
