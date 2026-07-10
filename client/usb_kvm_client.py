import datetime
import os
import sys
import tempfile
import traceback


def write_message(path: str, message: str):
    with open(path, "a+") as f:
        f.write(f"{message}\n")


if __name__ == "__main__":
    try:
        gen_dir = os.environ.get("COMTYPES_GEN_DIR", "").strip()
        if not gen_dir:
            gen_dir = os.path.join(
                tempfile.gettempdir(), "usb_kvm_client_comtypes_gen"
            )
            os.makedirs(gen_dir, exist_ok=True)
            os.environ["COMTYPES_GEN_DIR"] = gen_dir

        from main import main

        return_code = main()
        sys.exit(return_code)
    except Exception as error:
        base_path = os.path.dirname(os.path.abspath(sys.argv[0]))
        log_path = os.path.join(base_path, "exception.log")
        write_message(
            log_path, f"Error occurred at: {datetime.datetime.now()}\n"
        )
        write_message(log_path, f"Exception message: {error}\n")
        write_message(log_path, traceback.format_exc())
        sys.exit(1)
