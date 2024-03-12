import { ApiDescription, ApiDifference, Distribution, Product, Release, ReleasePair, Report, Info, ProjectProductIndex, PackageStats } from '../models'
import { apiUrl, changeUrl, distributionUrl, reportUrl, decode, autoDecompressAndParse, autoDecompressAndDecode } from './utils';

export const UPLOADED_DATA_PACKAGE_PREFIX = "upload:";

export class Api {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    package(project: string) {
        if (project.startsWith(UPLOADED_DATA_PACKAGE_PREFIX)) {
            return new SessionStorageProjectApi(project, `${this.baseUrl}/data/${project}`);
        } else {
            return new ProjectApi(project, `${this.baseUrl}/data/${project}`);
        }
    }

    async packages() {
        let results = await fetch(`${this.baseUrl}/data/packages.json`);
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

    distribution(release: Release) {
        return this.package(release.project).distribution(release.version);
    }

    api(release: Release) {
        return this.package(release.project).api(release.version);
    }

    change(pair: ReleasePair) {
        if (!pair.sameProject()) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).change(pair.old.version, pair.new.version);
    }

    report(pair: ReleasePair) {
        if (!pair.sameProject()) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).report(pair.old.version, pair.new.version);
    }

    distributionLog(release: Release) {
        return this.package(release.project).distributionLog(release.version);
    }

    apiLog(release: Release) {
        return this.package(release.project).apiLog(release.version);
    }

    changeLog(pair: ReleasePair) {
        if (!pair.sameProject()) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).changeLog(pair.old.version, pair.new.version);
    }

    reportLog(pair: ReleasePair) {
        if (!pair.sameProject()) {
            throw new Error(`Difference project: ${pair.toString()}`);
        }
        return this.package(pair.old.project).reportLog(pair.old.version, pair.new.version);
    }
}

export class ProjectApi {
    project: string;
    baseUrl: string;

    constructor(project: string, baseUrl: string) {
        this.project = project;
        this.baseUrl = baseUrl;
    }

    async index() {
        let results = await fetch(`${this.baseUrl}/index.json`);
        let ret = new ProjectProductIndex(this.project);
        if (!results.ok) throw new Error(`Index response fetching failed: ${results.status} ${results.statusText}.`)
        ret.from(await results.json());
        return ret;
    }

    async stats() {
        let results = await fetch(`${this.baseUrl}/stats.json`);
        let ret = new PackageStats();
        if (!results.ok) throw new Error(`Stats response fetching failed: ${results.status} ${results.statusText}.`)
        ret.from(await results.json());
        return ret;
    }

    async product<T extends Product>(result: T, url: string) {
        let results = await fetch(`${this.baseUrl}/${url}`);
        if (!results.ok) throw new Error(`Product response fetching failed: ${results.status} ${results.statusText}.`)
        result.from(await autoDecompressAndParse(await results.arrayBuffer()));
        return result;
    }

    async log(url: string) {
        let results = await fetch(`${this.baseUrl}/${url}`);
        if (!results.ok) throw new Error(`Log response fetching failed: ${results.status} ${results.statusText}.`)
        return await autoDecompressAndDecode(await results.arrayBuffer());
    }

    distribution(version: string) {
        return this.product(new Distribution(), `distributions/${version}.json`);
    }

    api(version: string) {
        return this.product(new ApiDescription(), `apis/${version}.json`);
    }

    change(old: string, newRel: string) {
        return this.product(new ApiDifference(), `changes/${old}&${newRel}.json`);
    }

    report(old: string, newRel: string) {
        return this.product(new Report(), `reports/${old}&${newRel}.json`);
    }

    distributionLog(version: string) {
        return this.log(`distributions/${version}.log`);
    }

    apiLog(version: string) {
        return this.log(`apis/${version}.log`);
    }

    changeLog(old: string, newRel: string) {
        return this.log(`changes/${old}&${newRel}.log`);
    }

    reportLog(old: string, newRel: string) {
        return this.log(`reports/${old}&${newRel}.log`);
    }
}

export class SessionStorageProjectApi extends ProjectApi {
    static uploadedData: any | null = null;

    static async uploadData(content: ArrayBuffer) {
        let data = await autoDecompressAndParse(content);
        let path = '/';
        if ("release" in data) {
            let project = data.release.project;
            data.release.project = UPLOADED_DATA_PACKAGE_PREFIX + project;
            path = distributionUrl(new Release().from(data.release));
        } else if ("distribution" in data) {
            let project = data.distribution.release.project;
            data.distribution.release.project = UPLOADED_DATA_PACKAGE_PREFIX + project;
            path = apiUrl(new Release().from(data.distribution.release));
        } else {
            let oldProject = data.old.release.project;
            data.old.release.project = UPLOADED_DATA_PACKAGE_PREFIX + oldProject;
            let newProject = data.new.release.project;
            data.new.release.project = UPLOADED_DATA_PACKAGE_PREFIX + newProject;
            let pair = new ReleasePair(new Release().from(data.old.release), new Release().from(data.new.release));
            if (!pair.sameProject()) {
                data.old.release.version = `${oldProject}:${pair.old.version}`;
                data.new.release.version = `${newProject}:${pair.new.version}`;
                data.old.release.project = data.new.release.project = UPLOADED_DATA_PACKAGE_PREFIX + 'data';
                pair = new ReleasePair(new Release().from(data.old.release), new Release().from(data.new.release));
            }
            if ("entries" in data) {
                path = changeUrl(pair);
            } else {
                path = reportUrl(pair);
            }
        }
        SessionStorageProjectApi.uploadedData = data;
        return path;
    }

    static getUploadData() {
        return SessionStorageProjectApi.uploadedData;
    }

    override async index() {
        return new ProjectProductIndex(this.project);
    }

    override async product<T extends Product>(result: T, url: string) {
        const cached = SessionStorageProjectApi.getUploadData();
        if (cached == null) {
            throw new Error("Failed to find in session storage");
        }

        let data = cached;

        if (result instanceof Distribution) {

        } else if (result instanceof ApiDescription) {

        } else if (result instanceof ApiDifference) {

        } else if (result instanceof Report) {

        } else {
            throw new Error(`Unknown product type: ${result}`);
        }

        result.from(data);
        return result;
    }

    override async log(url: string) {
        return "";
    }
}