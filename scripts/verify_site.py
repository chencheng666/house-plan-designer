"""从公网校验站点文件，并比较正式切换前的原站页面摘要。"""

import argparse
import concurrent.futures
import hashlib
import json
import time
import urllib.error
import urllib.parse
import urllib.request
from pathlib import Path


def fetch(url):
    request = urllib.request.Request(
        url, headers={"User-Agent": "HousePlanReleaseVerifier/2.0"}
    )
    with urllib.request.urlopen(request, timeout=40) as response:
        return response.status, response.read(), dict(response.headers)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--manifest", required=True)
    parser.add_argument("--before", required=True)
    parser.add_argument("--out", required=True)
    parser.add_argument(
        "--url", default="https://www.daguojueqi.site/house-plan-designer/"
    )
    args = parser.parse_args()
    manifest = json.loads(Path(args.manifest).read_text())
    before = json.loads(Path(args.before).read_text())["before"]
    origin = urllib.parse.urlsplit(args.url)
    root = f"{origin.scheme}://{origin.netloc}"

    def check_file(row):
        url = urllib.parse.urljoin(args.url, urllib.parse.quote(row["path"]))
        status, body, headers = fetch(url)
        digest = hashlib.sha256(body).hexdigest()
        return {
            **row,
            "status": status,
            "actualSha256": digest,
            "ok": status == 200 and digest == row["sha256"],
            "contentType": headers.get("Content-Type"),
        }

    with concurrent.futures.ThreadPoolExecutor(max_workers=4) as pool:
        files = list(pool.map(check_file, manifest["files"]))

    pages = {}
    for path, wanted in before["pages"].items():
        status, body, _ = fetch(root + path)
        digest = hashlib.sha256(body).hexdigest()
        pages[path] = {
            "status": status,
            "sha256": digest,
            "unchanged": status == 200 and digest == wanted,
        }

    missing = {}
    for path in ["__missing-hpd-file__.js", "demo/__missing-hpd-file__.js"]:
        try:
            missing[path] = fetch(urllib.parse.urljoin(args.url, path))[0]
        except urllib.error.HTTPError as error:
            missing[path] = error.code

    result = {
        "url": args.url,
        "release": manifest["release"],
        "verified": (
            all(file["ok"] for file in files)
            and all(page["unchanged"] for page in pages.values())
            and all(status == 404 for status in missing.values())
        ),
        "files": files,
        "protectedPages": pages,
        "missingFiles": missing,
        "checkedAt": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
    }
    output = Path(args.out)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n")
    print(json.dumps({
        "verified": result["verified"],
        "files": len(files),
        "protectedPages": len(pages),
        "missingFiles": missing,
    }, ensure_ascii=False))
    raise SystemExit(0 if result["verified"] else 2)


if __name__ == "__main__":
    main()
