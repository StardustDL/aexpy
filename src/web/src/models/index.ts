import { store } from "../services/store";
import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ItemEntry, loadApiEntry, ModuleEntry } from "./description";
import { BreakingRank, DiffEntry, VerifyState } from "./difference";
import { parse as durationParse } from "tinyduration";

export enum ProduceMode {
    Access = 0,
    Read = 1,
    Write = 2
}

export class Info {
    constructor(public commitId: string = "unknown", public buildDate: Date = new Date()) { }
}

export class Release {
    constructor(public project: string = "", public version: string = "") { }

    equals(other: Release): boolean {
        return this.project == other.project && this.version == other.version;
    }

    from(data: any) {
        if (data.project != undefined) {
            this.project = data.project;
        }
        if (data.version != undefined) {
            this.version = data.version;
        }
    }

    toString(): string {
        return `${this.project}@${this.version}`;
    }

    static fromString(str: string): Release | undefined {
        let parts = str.split("@");
        if (parts.length == 2) {
            let release = new Release();
            release.project = parts[0];
            release.version = parts[1];
            return release;
        }
    }
}

export class ReleasePair {
    new: Release = new Release();

    constructor(public old: Release = new Release(), newRelease: Release = new Release()) {
        this.new = newRelease;
    }

    equals(other: ReleasePair): boolean {
        return this.old.equals(other.old) && this.new.equals(other.new);
    }

    from(data: any) {
        this.old.from(data.old ?? {});
        this.new.from(data.new ?? {});
    }

    toString(): string {
        if (this.old.project == this.new.project) {
            return `${this.old.project}@${this.old.version}:${this.new.version}`;
        }
        else {
            return `${this.old.project}@${this.old.version}:${this.new.project}@${this.new.version}`;
        }
    }

    static fromString(str: string): ReleasePair | undefined {
        let parts = str.split(":");
        if (parts.length == 2) {
            let pair = new ReleasePair();
            let old = Release.fromString(parts[0])
            if (old == undefined) {
                return undefined;
            }
            pair.old = old;
            if (parts[1].indexOf("@") >= 0) {
                let ne = Release.fromString(parts[1]);
                if (ne == undefined) {
                    return undefined;
                }
                pair.new = ne;
            }
            else {
                pair.new.project = old.project;
                pair.new.version = parts[1];
            }
            return pair;
        }
    }
}

export enum ProduceState {
    Pending = 0,
    Success = 1,
    Failure = 2,
}

function parseDurationAsSeconds(text: string) {
    const data = durationParse(text);
    return (data.hours ?? 0) * 3600 + (data.minutes ?? 0) * 60 + (data.seconds ?? 0);
}

export class Product {
    creation: Date = new Date();
    duration: number = 0;
    state: ProduceState = ProduceState.Pending;
    producer: string = "";

    from(data: any) {
        this.creation = new Date(data.creation ?? new Date());
        this.duration = parseDurationAsSeconds(data.duration);
        this.state = data.state ?? ProduceState.Pending;
        this.producer = data.producer ?? "";
    }
}

export class Distribution extends Product {
    release: Release = new Release();
    pyversion: string = "";
    topModules: string[] = [];
    wheelFile: string = "";
    rootPath: string = "";
    fileCount: number = 0;
    fileSize: number = 0;
    locCount: number = 0;
    metadata: string[][] = [];
    description: string = "";
    dependencies: string[] = [];

    from(data: any) {
        super.from(data);
        this.release.from(data.release ?? {});
        this.pyversion = data.pyversion ?? "";
        this.topModules = data.topModules ?? [];
        this.wheelFile = data.wheelFile ?? "";
        this.rootPath = data.rootPath ?? "";
        this.fileCount = data.fileCount ?? 0;
        this.fileSize = data.fileSize ?? 0;
        this.locCount = data.locCount ?? 0;
        this.metadata = data.metadata ?? [];
        this.description = data.description ?? "";
        this.dependencies = data.dependencies ?? [];
    }

    fileName(): string {
        let file = this.wheelFile.replace(/\\/g, "/");
        let index = file.lastIndexOf("/");
        if (index >= 0) {
            return file.substring(index + 1);
        }
        return file;
    }
}

export class ApiDescription extends Product {
    distribution: Distribution = new Distribution();
    entries: { [key: string]: ApiEntry } = {};

    from(data: any) {
        super.from(data);
        this.distribution.from(data.distribution ?? {});
        if (data.entries != undefined) {
            for (let key in <{ [key: string]: any }>data.entries) {
                this.entries[key] = loadApiEntry(data.entries[key]);
            }
        }
    }

    publics(): { [key: string]: ApiEntry } {
        let result: { [key: string]: ApiEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (!entry.private) {
                result[key] = entry;
            }
        }
        return result;
    }

    privates(): { [key: string]: ApiEntry } {
        let result: { [key: string]: ApiEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry.private) {
                result[key] = entry;
            }
        }
        return result;
    }

    modules(): { [key: string]: ModuleEntry } {
        let modules: { [key: string]: ModuleEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry instanceof ModuleEntry) {
                modules[key] = entry;
            }
        }
        return modules;
    }

    classes(): { [key: string]: ClassEntry } {
        let classes: { [key: string]: ClassEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry instanceof ClassEntry) {
                classes[key] = entry;
            }
        }
        return classes;
    }

    typedEntries(): { [key: string]: ItemEntry } {
        let typed: { [key: string]: ItemEntry } = {};
        for (let item of Object.values(this.funcs())) {
            if (item.type) {
                typed[item.id] = item;
            }
        }
        for (let item of Object.values(this.attrs())) {
            if (item.type) {
                typed[item.id] = item;
            }
        }
        return typed;
    }

    funcs(): { [key: string]: FunctionEntry } {
        let funcs: { [key: string]: FunctionEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry instanceof FunctionEntry) {
                funcs[key] = entry;
            }
        }
        return funcs;
    }

    attrs(): { [key: string]: AttributeEntry } {
        let attrs: { [key: string]: AttributeEntry } = {};
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry instanceof AttributeEntry) {
                attrs[key] = entry;
            }
        }
        return attrs;
    }
}

export class ApiDifference extends Product {
    old: Distribution = new Distribution();
    new: Distribution = new Distribution();
    entries: { [key: string]: DiffEntry } = {};

    from(data: any) {
        super.from(data);
        this.old.from(data.old ?? {});
        this.new.from(data.new ?? {});
        if (data.entries != undefined) {
            for (let key in <{ [key: string]: any }>data.entries) {
                let entry = new DiffEntry();
                entry.from(data.entries[key]);
                this.entries[entry.id] = entry;
            }
        }
    }

    kinds(): string[] {
        let kinds: string[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (kinds.indexOf(entry.kind) < 0) {
                kinds.push(entry.kind);
            }
        }
        return kinds;
    }

    kind(kind: string): DiffEntry[] {
        let entries: DiffEntry[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry.kind == kind) {
                entries.push(entry);
            }
        }
        return entries;
    }

    verifies(): VerifyState[] {
        let states: VerifyState[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (states.indexOf(entry.verify.state) < 0) {
                states.push(entry.verify.state);
            }
        }
        return states;
    }

    verify(state: VerifyState): DiffEntry[] {
        let entries: DiffEntry[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry.verify.state == state) {
                entries.push(entry);
            }
        }
        return entries;
    }

    ranks(): BreakingRank[] {
        let ranks: BreakingRank[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (ranks.indexOf(entry.rank) < 0) {
                ranks.push(entry.rank);
            }
        }
        return ranks.sort((a, b) => a - b).reverse();
    }

    rank(rank: BreakingRank): DiffEntry[] {
        let entries: DiffEntry[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry.rank == rank) {
                entries.push(entry);
            }
        }
        return entries;
    }

    breaking(): DiffEntry[] {
        let entries: DiffEntry[] = [];
        for (let key in this.entries) {
            let entry = this.entries[key];
            if (entry.rank >= BreakingRank.Low) {
                entries.push(entry);
            }
        }
        return entries;
    }
}

export class Report extends Product {
    old: Distribution = new Distribution();
    new: Distribution = new Distribution();
    content: string = "";

    from(data: any) {
        super.from(data);
        this.old.from(data.old ?? {});
        this.new.from(data.new ?? {});
        this.content = data.content ?? "";
    }
}

export class PackageProductIndex {
    releases: Release[] = [];
    preprocessed: Release[] = [];
    extracted: Release[] = [];
    pairs: ReleasePair[] = [];
    diffed: ReleasePair[] = [];
    reported: ReleasePair[] = [];

    from(data: any) {
        (<any[]>data.releases ?? []).forEach((value: any) => {
            let release = Release.fromString(value);
            if (release) {
                this.releases.push(release);
            }
        });
        (<any[]>data.distributions ?? []).forEach((value: any) => {
            let release = Release.fromString(value);
            if (release) {
                this.preprocessed.push(release);
            }
        });
        (<any[]>data.apis ?? []).forEach((value: any) => {
            let release = Release.fromString(value);
            if (release) {
                this.extracted.push(release);
            }
        });
        (<any[]>data.pairs ?? []).forEach((value: any) => {
            let pair = ReleasePair.fromString(value);
            if (pair) {
                this.pairs.push(pair);
            }
        });
        (<any[]>data.changes ?? []).forEach((value: any) => {
            let pair = ReleasePair.fromString(value);
            if (pair) {
                this.diffed.push(pair);
            }
        });
        (<any[]>data.reports ?? []).forEach((value: any) => {
            let pair = ReleasePair.fromString(value);
            if (pair) {
                this.reported.push(pair);
            }
        });
    }

    ispreprocessed(release: Release): boolean {
        return this.preprocessed.find((item: Release) => item.equals(release)) != undefined;
    }

    isextracted(release: Release): boolean {
        return this.extracted.find((item: Release) => item.equals(release)) != undefined;
    }

    isdiffed(pair: ReleasePair): boolean {
        return this.diffed.find((item: ReleasePair) => item.equals(pair)) != undefined;
    }

    isreported(pair: ReleasePair): boolean {
        return this.reported.find((item: ReleasePair) => item.equals(pair)) != undefined;
    }

    failpreprocessed(): Release[] {
        return this.releases.filter((release: Release) => {
            return !this.ispreprocessed(release);
        });
    }

    failextracted(): Release[] {
        return this.releases.filter((release: Release) => {
            return !this.isextracted(release);
        });
    }

    faildiffed(): ReleasePair[] {
        return this.pairs.filter((pair: ReleasePair) => {
            return !this.isdiffed(pair);
        });
    }

    failreported(): ReleasePair[] {
        return this.pairs.filter((pair: ReleasePair) => {
            return !this.isreported(pair);
        });
    }

    async loadPreprocessed() {
        let preprocessed: { [key: string]: Distribution } = {};
        let promised: Promise<any>[] = [];
        for (let item of this.preprocessed) {
            let cur = item;
            let tfunc = async () => {
                preprocessed[cur.toString()] = await store.state.api.distribution(cur);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return preprocessed;
    }

    async loadExtracted() {
        let extracted: { [key: string]: ApiDescription } = {};
        let promised: Promise<any>[] = [];
        for (let item of this.extracted) {
            let cur = item;
            let tfunc = async () => {
                extracted[cur.toString()] = await store.state.api.api(cur);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return extracted;
    }

    async loadDiffed() {
        let diffed: { [key: string]: ApiDifference } = {};
        let promised: Promise<any>[] = [];
        for (let item of this.diffed) {
            let cur = item;
            let tfunc = async () => {
                diffed[cur.toString()] = await store.state.api.change(cur);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return diffed;
    }

    async loadReported() {
        let reported: { [key: string]: Report } = {};
        let promised: Promise<any>[] = [];
        for (let item of this.reported) {
            let cur = item;
            let tfunc = async () => {
                reported[cur.toString()] = await store.state.api.report(cur);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return reported;
    }
}