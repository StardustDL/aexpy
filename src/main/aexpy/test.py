from .downloads import index, wheels, releases, mirrors


import ssl
ssl._create_default_https_context = ssl._create_unverified_context


def work():
    projects = index.getIndex(mirrors.INDEX_TSINGHUA)
    projects = ["ao3_api",
                "smart_open",
                "flask",
                "urllib3",
                "setuptools",
                "pyyaml",
                "click",
                "rsa",
                "wheel",
                "requests",
                "schemdule",
                "enlighten",
                "trypackage",
                "observable",
                "aiowebsocket",
                "resolvelib",
                "requirementslib",
                "pythonfinder",
                "botocore",
                "django",
                "matplotlib",
                "scrapy",
                "beautifulsoup4",
                "numpy"]
    for project in projects:
        print(f"Process {project}.")
        rels = releases.getReleases(project)
        for version, files in rels.items():
            print(f"Process {project} @ {version}.")
            download = releases.getDownloadInfo(files)
            if download:
                print(f"Download {project} @ {version}.")
                wheel = wheels.downloadWheel(download, mirror=mirrors.FILE_TSINGHUA)
                print(wheel)
                print(f"Unpack {project} @ {version}.")
                unpack = wheels.unpackWheel(wheel)
                print(unpack)
