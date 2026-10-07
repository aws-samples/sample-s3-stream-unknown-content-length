# Streaming content of unknown length to Amazon S3

A minimal, dependency-light example of uploading a **stream of unknown total size**
to Amazon S3 using the [multipart upload](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpuoverview.html)
API.

A normal `PutObject` call needs to know the object's size up front. When data
arrives as an open-ended stream — application logs, a `tar` pipe, query output —
you do not know the final size in advance. S3 multipart upload solves this: you
send the data as a sequence of parts and only declare completion once the stream
ends.

`writer.py` reads bytes from standard input, buffers them into 5 MiB parts
(the smallest size S3 accepts for all but the final part), uploads each part as
it fills, and calls `CompleteMultipartUpload` on EOF. If anything fails, it
aborts the upload so no orphaned parts are left behind.

## Contents

| File          | Purpose                                                                 |
|---------------|-------------------------------------------------------------------------|
| `writer.py`   | Reads stdin, uploads it to S3 as a multipart upload of unknown length.  |
| `streamer.py` | Generates a continuous stream of synthetic JSON log lines on stdout, for testing. |

## Prerequisites

- Python 3.10 or later
- [`boto3`](https://boto3.amazonaws.com/v1/documentation/api/latest/index.html) (`pip install -r requirements.txt`)
- AWS credentials configured (environment variables, shared config file, or an
  instance/container role) with permission to call `s3:CreateMultipartUpload`,
  `s3:UploadPart`, `s3:CompleteMultipartUpload`, and `s3:AbortMultipartUpload`
  on the target bucket.
- An existing S3 bucket you own.

## Usage

Install the dependency:

```bash
pip install -r requirements.txt
```

Pipe any stream into `writer.py`, passing the destination bucket and key:

```bash
# Upload a local file
cat large.log | python3 writer.py my-bucket logs/large.log

# Upload the synthetic test stream (Ctrl+C stops the producer; the
# upload completes with whatever has been streamed so far)
python3 streamer.py | python3 writer.py my-bucket logs/stream.jsonl
```

Expected output:

```
uploaded part 1: 5242880 bytes
uploaded part 2: 5242880 bytes
...
Done: N part(s) uploaded to s3://my-bucket/logs/stream.jsonl
```

## How it works

1. The first time a full 5 MiB part is ready, `writer.py` calls
   `CreateMultipartUpload` to obtain an `UploadId`.
2. Each subsequent full part is sent with `UploadPart`; the returned `ETag` and
   part number are recorded.
3. On EOF, any remaining buffered bytes become the final part (which may be
   smaller than 5 MiB), and `CompleteMultipartUpload` assembles the object.
4. On any exception, `AbortMultipartUpload` is called so S3 discards the parts
   already sent — this avoids ongoing storage charges for incomplete uploads.

> **Tip:** For production buckets, add an
> [S3 Lifecycle rule to expire incomplete multipart uploads](https://docs.aws.amazon.com/AmazonS3/latest/userguide/mpu-abort-incomplete-mpu-lifecycle-config.html)
> as a backstop against parts left behind by processes that are hard-killed.

## Cleaning up

Delete any test objects you created and empty/remove the test bucket to avoid
storage charges.

## Security

See [CONTRIBUTING](CONTRIBUTING.md#security-issue-notifications) for more information.

## License

This library is licensed under the MIT-0 License. See the [LICENSE](LICENSE) file.
