import argparse
import pyvisa

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="Test simple SCPI communication via VISA.",
                                     formatter_class=argparse.ArgumentDefaultsHelpFormatter)
    parser.add_argument("port", type=str, nargs='?', default=None, help="The port to use. Must be a Visa compatible connection string.")
    args = parser.parse_args()
        
    rm = pyvisa.ResourceManager()
    print("VISA Resources found: ", end='')
    print(rm.list_resources())
    if args.port:
        inst = rm.open_resource(args.port)
        msgs = ["*IDN?", "IDN-SGLT-PRI?", "C1:OUTP LOAD,50;BSWV WVTP,SINE,PHSE,0,FRQ,50000,AMP,2.1,OFST,0;OUTP ON"]
        for m in msgs:
            if m.endswith("?"):
                print(f"Query \"{m}\" reply: ", end='')
                r = inst.query(m).strip()
                print(f"\"{r}\"")
            else:
                print(f"Write \"{m}\"")
                inst.write(m)
