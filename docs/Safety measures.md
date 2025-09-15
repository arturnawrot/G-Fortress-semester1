To keep our AES-encrypted vault effective, follow these guidelines:



Master Password

* The GF\_MASTER\_PASSWORD must never be committed to GitHub or stored in plaintext.
* Provide it securely at runtime (e.g., environment variable, container secret, or your orchestrator’s secret manager).
* Treat the master password like a root credential: whoever has it can decrypt everything in the vault.



Vault File (vault.json)

* The vault file is encrypted, but still sensitive:
* &nbsp;	Back it up securely (encrypted disk, secure S3 bucket, etc.).
* &nbsp;	Don’t commit it to GitHub. It’s already in .gitignore.

Without the master password, the file is useless, but don’t assume it’s safe to share.



Key Rotation

* Rotating the master password requires:

1. &nbsp;	Unlocking the vault with the old master.
2. &nbsp;	Re-encrypting all entries with the new one.
3. &nbsp;	Saving the vault.



* A helper function (rotate\_master) can be added later if needed.

Auditing \& Logging

* Log when secrets are accessed, not the secret values themselves.
* Avoid printing secrets to console/logs during debugging.

Usage in Production

* Always source GF\_MASTER\_PASSWORD from a secrets manager (Kubernetes Secrets, AWS Secrets Manager, Azure Key Vault, Vault by HashiCorp, etc.).
* Restrict file permissions on vault.json so only the app can read/write it.
