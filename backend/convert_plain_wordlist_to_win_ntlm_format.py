from ntlm.helpers import ntlm_hash
import sys
import os

def main():
    if len(sys.argv) != 2:
        print("Usage: python make_wordlist.py <input_wordlist.txt>")
        sys.exit(1)

    input_path = sys.argv[1]
    input_path = os.path.abspath(input_path)

    if not os.path.isfile(input_path):
        print(f"Input file not found: {input_path}")
        sys.exit(1)

    input_dir = os.path.dirname(input_path)
    output_path = os.path.join(input_dir, "wordlist_win.txt")

    print(f"Reading:  {input_path}")
    print(f"Writing:  {output_path}")

    with open(input_path, "r", encoding="utf-8", errors="ignore") as fin, \
         open(output_path, "w", encoding="utf-8") as fout:

        for line in fin:
            password = line.rstrip("\r\n")
            if not password:
                continue  # skip empty lines
            hash_str = ntlm_hash(password)
            fout.write(hash_str + "\n")


if __name__ == "__main__":
    main()