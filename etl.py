"""
etl.py

Description:
    * Provisions AWS infrastructure
    * Runs ETL pipeline (download, preprocess, build)

Instructions:
    * Run via CLI:
        python etl.py provision # Just provision AWS infra
        python etl.py download # Just download data to S3
        python etl.py preprocess # Just run preprocessing
        python etl.py build # Just build individual JSONs
        python etl.py etl # Run full ETL (download + preprocess + build)
        python etl.py all # Provision + full ETL

Authors:
    * Spencer Karofsky (https://github.com/spencer-karofsky)
"""
import sys

def provision():
    from infra.provision_aws_etl import provision_aws_etl
    provision_aws_etl()
    print("Provisioning complete")


def download():
    from data.data_download import download_and_upload_to_s3
    download_and_upload_to_s3()
    print("Data download complete")


def preprocess():
    from etl.preprocess import run_preprocessing
    run_preprocessing()
    print("Preprocessing complete")


def build():
    from etl.build_json import build_json
    build_json()
    print("Build JSON complete")


def etl():
    """Run full ETL pipeline: download -> preprocess -> build"""
    download()
    preprocess()
    build()
    print("Full ETL pipeline complete")

def all():
    provision()
    etl()

if __name__ == "__main__":
    commands = {
        "provision": provision,
        "download": download,
        "preprocess": preprocess,
        "build": build,
        "etl": etl,
        "all": all,
    }

    command = sys.argv[1] if len(sys.argv) > 1 else "all"

    if command in commands:
        commands[command]()
    else:
        print(f"Unknown command: {command}")
        print(f"Available: {', '.join(commands.keys())}")