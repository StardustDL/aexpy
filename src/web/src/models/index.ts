import { store } from "../services/store";
import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ItemEntry, loadApiEntry, ModuleEntry, SpecialEntry } from "./description";
import { BreakingRank, DiffEntry } from "./difference";
import { parse as durationParse } from "tinyduration";

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
        return this;
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

    sameProject(): boolean {
        return this.old.project == this.new.project;
    }

    equals(other: ReleasePair): boolean {
        return this.old.equals(other.old) && this.new.equals(other.new);
    }

    from(data: any) {
        this.old.from(data.old ?? {});
        this.new.from(data.new ?? {});
    }

    toString(): string {
        if (this.sameProject()) {
            return `${this.old.project}@${this.old.version}&${this.new.version}`;
        }
        else {
            return `${this.old.project}@${this.old.version}&${this.new.project}@${this.new.version}`;
        }
    }

    static fromString(str: string): ReleasePair | undefined {
        let parts = str.split("&");
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
    modules: { [key: string]: ModuleEntry } = {};
    classes: { [key: string]: ClassEntry } = {};
    functions: { [key: string]: FunctionEntry } = {};
    attributes: { [key: string]: AttributeEntry } = {};
    specials: { [key: string]: SpecialEntry } = {};

    from(data: any) {
        super.from(data);
        this.distribution.from(data.distribution ?? {});
        if (data.modules != undefined) {
            for (let key in <{ [key: string]: any }>data.modules) {
                this.modules[key] = new ModuleEntry().from(data.modules[key]);
            }
        }
        if (data.classes != undefined) {
            for (let key in <{ [key: string]: any }>data.classes) {
                this.classes[key] = new ClassEntry().from(data.classes[key]);
            }
        }
        if (data.functions != undefined) {
            for (let key in <{ [key: string]: any }>data.functions) {
                this.functions[key] = new FunctionEntry().from(data.functions[key]);
            }
        }
        if (data.attributes != undefined) {
            for (let key in <{ [key: string]: any }>data.attributes) {
                this.attributes[key] = new AttributeEntry().from(data.attributes[key]);
            }
        }
        if (data.specials != undefined) {
            for (let key in <{ [key: string]: any }>data.specials) {
                this.specials[key] = new SpecialEntry().from(data.specials[key]);
            }
        }
    }

    entry(id: string) {
        if (id in this.modules) return this.modules[id];
        if (id in this.classes) return this.classes[id];
        if (id in this.functions) return this.functions[id];
        if (id in this.attributes) return this.attributes[id];
        if (id in this.specials) return this.specials[id];
    }

    *entries() {
        for (let entry of Object.values(this.modules))
            yield entry;
        for (let entry of Object.values(this.classes))
            yield entry;
        for (let entry of Object.values(this.functions))
            yield entry;
        for (let entry of Object.values(this.attributes))
            yield entry;
        for (let entry of Object.values(this.specials))
            yield entry;
    }

    entriesMap() {
        let entries: { [key: string]: ApiEntry } = {};
        for (let entry of this.entries()) {
            entries[entry.id] = entry;
        }
        return entries;
    }

    publics() {
        let result: { [key: string]: ApiEntry } = {};
        for (let entry of this.entries()) {
            if (!entry.private) {
                result[entry.id] = entry;
            }
        }
        return result;
    }

    privates() {
        let result: { [key: string]: ApiEntry } = {};
        for (let entry of this.entries()) {
            if (entry.private) {
                result[entry.id] = entry;
            }
        }
        return result;
    }

    typedEntries() {
        let typed: { [key: string]: ItemEntry } = {};
        for (let item of Object.values(this.functions)) {
            if (item.type) {
                typed[item.id] = item;
            }
        }
        for (let item of Object.values(this.attributes)) {
            if (item.type) {
                typed[item.id] = item;
            }
        }
        return typed;
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

export class ProjectProductIndex {
    releases: Release[] = [];
    preprocessed: Release[] = [];
    extracted: Release[] = [];
    pairs: ReleasePair[] = [];
    diffed: ReleasePair[] = [];
    reported: ReleasePair[] = [];

    constructor(public project: string) { }

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

export type StatData = { [key: string]: { [key: string]: number | { [key: string]: number } } }

export class PackageStats extends Product {
    dists: PackageProductStats = new PackageProductStats();
    apis: PackageProductStats = new PackageProductStats();
    changes: PackageProductStats = new PackageProductStats();
    reports: PackageProductStats = new PackageProductStats();

    from(data: any) {
        super.from(data);
        this.dists.from(data.dists ?? {});
        this.apis.from(data.apis ?? {});
        this.changes.from(data.changes ?? {});
        this.reports.from(data.reports ?? {});
    }
}

export class PackageProductStats {
    data: StatData = {};
    keys: Set<string> = new Set();
    singleKeys: Set<string> = new Set();
    multipleKeys: Set<string> = new Set();

    from(data: any) {
        this.data = data;
        for (let id in this.data) {
            for (let key in this.data[id]) {
                this.keys.add(key);
                if (typeof (this.data[id][key]) == "number") {
                    this.singleKeys.add(key);
                } else {
                    this.multipleKeys.add(key);
                }
            }
        }
        if (this.singleKeys.size + this.multipleKeys.size != this.keys.size) {
            throw new Error("Unmatch key-value types, may keys has values of unexpected different types.");
        }
    }

    selectMany<T extends number | { [key: string]: number }>(...keys: (string | [string, string])[]) {
        let result: { [key: string]: { [key: string]: T } } = {};
        for (let id in this.data) {
            let origin = this.data[id];
            let sub: { [key: string]: T } = {};
            for (let key of keys) {
                if (typeof key == "string") {
                    if (!(key in origin)) continue;
                    sub[key] = <T>origin[key];
                } else {
                    if (!(key[0] in origin)) continue;
                    sub[key[1]] = <T>origin[key[0]];
                }
            }
            if (Object.keys(sub).length > 0) {
                result[id] = sub;
            }
        }
        return result;
    }

    select<T extends number | { [key: string]: number }>(key: string | [string, string]) {
        let data = this.selectMany<T>(key);
        let result: { [key: string]: T } = {};
        for (let id in data) {
            if (typeof key == "string") {
                result[id] = data[id][key];
            } else {
                result[id] = data[id][key[1]];
            }
        }
        return result;
    }
}