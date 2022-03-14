import { store } from "../services/store";
import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, loadApiEntry, ModuleEntry } from "./description";
import { BreakingRank, DiffEntry } from "./difference";

export class ProducerOptions {
    static fromQuery(data: any): ProducerOptions {
        let options = new ProducerOptions();
        if (data.redo != undefined) {
            options.redo = data.redo == "true";
        }
        if (data.onlyCache != undefined) {
            options.onlyCache = data.onlyCache == "true";
        }
        if (data.cached != undefined) {
            options.cached = data.cached == "true";
        }
        return options;
    }

    constructor(public redo?: boolean, public onlyCache?: boolean, public cached?: boolean) { }
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

export class Provider {
    name: string = "default";

    toString(): string {
        return this.name;
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


export class Product {
    creation: Date = new Date();
    duration: number = 0;
    success: boolean = false;

    from(data: any) {
        this.creation = new Date(data.creation ?? new Date());
        this.duration = data.duration ?? 0;
        this.success = data.success ?? false;
    }
}

export class Distribution extends Product {
    release: Release = new Release();
    pyversion: string = "";
    topModules: string[] = [];
    wheelFile: string = "";
    wheelDir: string = "";

    from(data: any) {
        super.from(data);
        this.release.from(data.release ?? {});
        this.pyversion = data.pyversion ?? "";
        this.topModules = data.topModules ?? [];
        this.wheelFile = data.wheelFileRel ?? "";
        this.wheelDir = data.wheelDirRel ?? "";
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

export class ApiBreaking extends ApiDifference {
}

export class Report extends Product {
    old: Release = new Release();
    new: Release = new Release();

    from(data: any) {
        super.from(data);
        this.old.from(data.old ?? {});
        this.new.from(data.new ?? {});
    }
}

export class ProjectResult extends Product {
    project: string = "";
    provider: string = ""
    releases: Release[] = [];
    preprocessed: Release[] = [];
    extracted: Release[] = [];
    pairs: ReleasePair[] = [];
    diffed: ReleasePair[] = [];
    evaluated: ReleasePair[] = [];
    reported: ReleasePair[] = [];

    from(data: any) {
        super.from(data);
        this.project = data.project ?? "";
        this.provider = data.provider ?? "";
        (<any[]>data.releases ?? []).forEach((value: any) => {
            let release = new Release();
            release.from(value);
            this.releases.push(release);
        });
        (<any[]>data.preprocessed ?? []).forEach((value: any) => {
            let release = new Release();
            release.from(value);
            this.preprocessed.push(release);
        });
        (<any[]>data.extracted ?? []).forEach((value: any) => {
            let release = new Release();
            release.from(value);
            this.extracted.push(release);
        });
        (<any[]>data.pairs ?? []).forEach((value: any) => {
            let pair = new ReleasePair();
            pair.from(value);
            this.pairs.push(pair);
        });
        (<any[]>data.diffed ?? []).forEach((value: any) => {
            let pair = new ReleasePair();
            pair.from(value);
            this.diffed.push(pair);
        });
        (<any[]>data.evaluated ?? []).forEach((value: any) => {
            let pair = new ReleasePair();
            pair.from(value);
            this.evaluated.push(pair);
        });
        (<any[]>data.reported ?? []).forEach((value: any) => {
            let pair = new ReleasePair();
            pair.from(value);
            this.reported.push(pair);
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

    isevaluated(pair: ReleasePair): boolean {
        return this.evaluated.find((item: ReleasePair) => item.equals(pair)) != undefined;
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

    failevaluated(): ReleasePair[] {
        return this.pairs.filter((pair: ReleasePair) => {
            return !this.isevaluated(pair);
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
        let options = new ProducerOptions(undefined, true, undefined);
        for (let item of this.preprocessed) {
            let cur = item;
            let tfunc = async () => {
                preprocessed[cur.toString()] = await store.state.api.preprocessor.process(cur, this.provider, options);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return preprocessed;
    }

    async loadExtracted() {
        let extracted: { [key: string]: ApiDescription } = {};
        let promised: Promise<any>[] = [];
        let options = new ProducerOptions(undefined, true, undefined);
        for (let item of this.extracted) {
            let cur = item;
            let tfunc = async () => {
                extracted[cur.toString()] = await store.state.api.extractor.process(cur, this.provider, options);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return extracted;
    }

    async loadDiffed() {
        let diffed: { [key: string]: ApiDifference } = {};
        let promised: Promise<any>[] = [];
        let options = new ProducerOptions(undefined, true, undefined);
        for (let item of this.diffed) {
            let cur = item;
            let tfunc = async () => {
                diffed[cur.toString()] = await store.state.api.differ.process(cur, this.provider, options);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return diffed;
    }

    async loadEvaluated() {
        let evaluated: { [key: string]: ApiBreaking } = {};
        let promised: Promise<any>[] = [];
        let options = new ProducerOptions(undefined, true, undefined);
        for (let item of this.evaluated) {
            let cur = item;
            let tfunc = async () => {
                evaluated[cur.toString()] = await store.state.api.evaluator.process(cur, this.provider, options);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return evaluated;
    }

    async loadReported() {
        let reported: { [key: string]: Report } = {};
        let promised: Promise<any>[] = [];
        let options = new ProducerOptions(undefined, true, undefined);
        for (let item of this.reported) {
            let cur = item;
            let tfunc = async () => {
                reported[cur.toString()] = await store.state.api.reporter.process(cur, this.provider, options);
            }
            promised.push(tfunc());
        }
        await Promise.all(promised);
        return reported;
    }
}