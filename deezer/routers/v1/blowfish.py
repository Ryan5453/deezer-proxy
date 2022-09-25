import hashlib

from Cryptodome.Cipher import Blowfish

from deezer.core.config import master_key


def generate_blowfish_key(track_id: int) -> bytes:
    m = hashlib.md5()
    m.update(bytes([ord(x) for x in track_id]))
    id_md5 = m.hexdigest()

    blowfish_key = bytes(
        (
            [
                (ord(id_md5[i]) ^ ord(id_md5[i + 16]) ^ ord(master_key[i]))
                for i in range(16)
            ]
        )
    )

    return blowfish_key


def decrypt_chunk(data: bytes, blowfish_key: bytes) -> bytes:
    cipher = Blowfish.new(blowfish_key, Blowfish.MODE_CBC, bytes([i for i in range(8)]))
    return cipher.decrypt(data)
