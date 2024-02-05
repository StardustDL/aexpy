import { ApiDescription, ApiDifference, Distribution, ProduceMode, Product, Release, ReleasePair, Report, Info, PackageProductIndex } from '../models'

export const UPLOADED_DATA_PACKAGE = "upload:data";

export class Api {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    package(project: string) {
        if (project == UPLOADED_DATA_PACKAGE) {
            return new SessionStoragePackageApi(this.baseUrl);
        } else {
            return new PackageApi(`${this.baseUrl}/${project}`);
        }
    }

    async packages() {
        let results = await fetch(`${this.baseUrl}/packages.json`);
        return <string[]>await results.json();
    }

    async info() {
        if (import.meta.env.VITE_NOSERVER) {
            return new Info(import.meta.env.VITE_COMMIT_ID ?? "unknown", new Date(import.meta.env.VITE_BUILD_DATE ?? new Date()));
        } else {
            let results = await fetch(`${this.baseUrl}/info`);
            let data = await results.json();
            return new Info(data.commitId ?? "unknown", new Date(data.buildDate ?? new Date()));
        }
    }

    async distribution(release: Release) {
        return this.package(release.project).distribution(release.version);
    }

    async api(release: Release) {
        return this.package(release.project).api(release.version);
    }

    async change(pair: ReleasePair) {
        if (pair.old.project != pair.new.project) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).change(pair.old.version, pair.new.version);
    }

    async report(pair: ReleasePair) {
        if (pair.old.project != pair.new.project) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).report(pair.old.version, pair.new.version);
    }

    async distributionLog(release: Release) {
        return this.package(release.project).distributionLog(release.version);
    }

    async apiLog(release: Release) {
        return this.package(release.project).apiLog(release.version);
    }

    async changeLog(pair: ReleasePair) {
        if (pair.old.project != pair.new.project) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).changeLog(pair.old.version, pair.new.version);
    }

    async reportLog(pair: ReleasePair) {
        if (pair.old.project != pair.new.project) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).reportLog(pair.old.version, pair.new.version);
    }
}

export class PackageApi {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async index() {
        let results = await fetch(`${this.baseUrl}/index.json`);
        let ret = new PackageProductIndex();
        ret.from(await results.json());
        return ret;
    }

    async product<T extends Product>(result: T, url: string) {
        let results = await fetch(`${this.baseUrl}/${url}`);
        result.from(await results.json());
        return result;
    }

    async log(url: string) {
        let results = await fetch(`${this.baseUrl}/${url}`);
        return await results.text();
    }

    async distribution(version: string) {
        return this.product(new Distribution(), `distributions/${version}.json`);
    }

    async api(version: string) {
        return this.product(new ApiDescription(), `apis/${version}.json`);
    }

    async change(old: string, newRel: string) {
        return this.product(new ApiDifference(), `changes/${old}&${newRel}.json`);
    }

    async report(old: string, newRel: string) {
        return this.product(new Report(), `reports/${old}&${newRel}.json`);
    }

    async distributionLog(version: string) {
        return this.log(`distributions/${version}.log`);
    }

    async apiLog(version: string) {
        return this.log(`apis/${version}.log`);
    }

    async changeLog(old: string, newRel: string) {
        return this.log(`changes/${old}&${newRel}.log`);
    }

    async reportLog(old: string, newRel: string) {
        return this.log(`reports/${old}&${newRel}.log`);
    }
}

export class SessionStoragePackageApi extends PackageApi {
    override async index() {
        return new PackageProductIndex();
    }

    override async product<T extends Product>(result: T, url: string) {
        const cached = window.sessionStorage.getItem("uploaded-data");
        if (cached == null) {
            throw new Error("Failed to find in session storage");
        }
        const data = JSON.parse(cached);
        result.from(data);
        return result;
    }

    override async log(url: string) {
        return "";
    }
}