import sodium from 'libsodium-wrappers';

// Helper to manage sodium initialization
const ready = sodium.ready;

// Base64 to Uint8Array
const b64ToUint8 = (b64: string): Uint8Array => {
    const bin = atob(b64);
    const len = bin.length;
    const bytes = new Uint8Array(len);
    for (let i = 0; i < len; i++) {
        bytes[i] = bin.charCodeAt(i);
    }
    return bytes;
};

// Uint8Array to Base64
const uint8ToB64 = (arr: Uint8Array): string => {
    return btoa(String.fromCharCode.apply(null, Array.from(arr)));
};

export const generateKeyPair = async () => {
    await ready;
    const keyPair = sodium.crypto_kx_keypair();
    return {
        publicKey: uint8ToB64(keyPair.publicKey),
        privateKey: uint8ToB64(keyPair.privateKey),
    };
};

// --- THIS FUNCTION IS NOW CORRECT ---
export const deriveSharedSecret = async (
    clientPublicKeyB64: string,
    clientPrivateKeyB64: string,
    serverPublicKeyB64: string
) => {
    await ready;
    const clientPublicKey = b64ToUint8(clientPublicKeyB64);
    const clientPrivateKey = b64ToUint8(clientPrivateKeyB64);
    const serverPublicKey = b64ToUint8(serverPublicKeyB64);

    // Use the correct libsodium function with all three keys
    const { sharedRx } = sodium.crypto_kx_client_session_keys(
        clientPublicKey,
        clientPrivateKey,
        serverPublicKey
    );

    // sharedRx is the key for receiving data from the server
    return uint8ToB64(sharedRx);
};
// --- END OF CORRECTION ---

export const encryptData = async (aesKeyB64: string, data: object): Promise<string> => {
    await ready;
    const key = b64ToUint8(aesKeyB64);
    const nonce = sodium.randombytes_buf(sodium.crypto_aead_aes256gcm_NPUBBYTES);
    const message = JSON.stringify(data);

    const encryptedMessage = sodium.crypto_aead_aes256gcm_encrypt(
        message,
        null,
        null,
        nonce,
        key
    );

    const combined = new Uint8Array(nonce.length + encryptedMessage.length);
    combined.set(nonce);
    combined.set(encryptedMessage, nonce.length);

    return uint8ToB64(combined);
};

export const decryptData = async (aesKeyB64: string, encryptedB64: string): Promise<any> => {
    await ready;
    const key = b64ToUint8(aesKeyB64);
    const combined = b64ToUint8(encryptedB64);

    const nonce = combined.slice(0, sodium.crypto_aead_aes256gcm_NPUBBYTES);
    const ciphertext = combined.slice(sodium.crypto_aead_aes256gcm_NPUBBYTES);

    const decrypted = sodium.crypto_aead_aes256gcm_decrypt(
        ciphertext,
        null,
        null,
        nonce,
        key
    );
    
    return JSON.parse(new TextDecoder().decode(decrypted));
};