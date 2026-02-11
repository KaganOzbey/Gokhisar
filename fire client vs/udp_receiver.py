#!/usr/bin/env python3
import socket
import argparse

def main():
    parser = argparse.ArgumentParser(description="UDP Receiver (debug) - prints datagram sizes")
    parser.add_argument("--host", default="0.0.0.0", help="Bind host (default: 0.0.0.0)")
    parser.add_argument("--port", type=int, default=5000, help="Bind port (default: 5000)")
    parser.add_argument("--max", type=int, default=20, help="Max packets to print (default: 20, 0=unlimited)")
    args = parser.parse_args()

    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.bind((args.host, args.port))
    print(f"Listening UDP on {args.host}:{args.port}...")

    n = 0
    while True:
        data, addr = sock.recvfrom(65535)
        n += 1
        print(f"#{n:04d} from {addr[0]}:{addr[1]} bytes={len(data)}")
        if args.max and n >= args.max:
            break

if __name__ == "__main__":
    main()
