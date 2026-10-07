import signal
import sys

import boto3

PART_SIZE = 5 * 1024 * 1024  # 5 MiB, the smallest part S3 accepts

bucket, key = sys.argv[1], sys.argv[2]
signal.signal(signal.SIGINT, signal.SIG_IGN)  # Ctrl+C stops only the producer
s3 = boto3.client("s3")
upload_id = None  # set when the first part is ready
parts = []        # (PartNumber, ETag) pairs for CompleteMultipartUpload
buffer = bytearray()


def upload_part(data):
    global upload_id
    if upload_id is None:  # first part: start the upload, with no size
        upload_id = s3.create_multipart_upload(Bucket=bucket, Key=key)["UploadId"]
    number = len(parts) + 1
    result = s3.upload_part(
        Bucket=bucket, Key=key,
        PartNumber=number, UploadId=upload_id, Body=data,
    )
    parts.append({"PartNumber": number, "ETag": result["ETag"]})
    print(f"uploaded part {number}: {len(data)} bytes")


def cancel_multipart_upload():
    # Cancels the upload and discards any parts already sent.
    if upload_id is not None:
        s3.abort_multipart_upload(Bucket=bucket, Key=key, UploadId=upload_id)


try:
    while True:
        chunk = sys.stdin.buffer.read(64 * 1024)
        if not chunk:                    # EOF: the stream has ended
            break
        buffer += chunk
        while len(buffer) >= PART_SIZE:  # a full 5 MiB part is ready
            upload_part(buffer[:PART_SIZE])
            del buffer[:PART_SIZE]       # drop the sent bytes in place
    if buffer:                           # leftover becomes the last part
        upload_part(buffer)
    if not parts:                        # empty stream: nothing was started
        sys.exit("No data received; nothing was uploaded.")
    s3.complete_multipart_upload(
        Bucket=bucket, Key=key, UploadId=upload_id,
        MultipartUpload={"Parts": parts},
    )
    print(f"Done: {len(parts)} part(s) uploaded to s3://{bucket}/{key}")
except Exception:
    cancel_multipart_upload()  # S3 discards the parts already sent
    raise
