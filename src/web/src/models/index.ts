import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, loadApiEntry, ModuleEntry } from "./description";
import { BreakingRank, DiffEntry } from "./difference";

export class ProducerOptions {
    redo?: boolean;
    onlyCache?: boolean;
    cached?: boolean;

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
}


export class Release {
    project: string = "";
    version: string = "";

    constructor(project: string = "", version: string = "") {
        this.project = project;
        this.version = version;
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
    old: Release = new Release();
    new: Release = new Release();

    constructor(old?: Release, newRelease?: Release) {
        if (old != undefined) {
            this.old = old;
        }
        if (newRelease != undefined) {
            this.new = newRelease;
        }
    }

    from(data: any) {
        if (data.old != undefined) {
            this.old.from(data.old);
        }
        if (data.new != undefined) {
            this.new.from(data.new);
        }
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
        if (data.creation != undefined) {
            this.creation = new Date(data.creation);
        }
        if (data.duration != undefined) {
            this.duration = data.duration;
        }
        if (data.success != undefined) {
            this.success = data.success;
        }
    }
}

export class Distribution extends Product {
    release: Release = new Release();
    pyversion: string = "";
    topModules: string[] = [];
    wheelFile: string = "";

    from(data: any) {
        super.from(data);
        if (data.release != undefined) {
            this.release.from(data.release);
        }
        if (data.pyversion != undefined) {
            this.pyversion = data.pyversion;
        }
        if (data.topModules != undefined) {
            this.topModules = data.topModules;
        }
        if (data.wheelFileRel != undefined) {
            this.wheelFile = data.wheelFileRel;
        }
    }
}

export class ApiDescription extends Product {
    distribution: Distribution = new Distribution();
    entries: { [key: string]: ApiEntry } = {};

    from(data: any) {
        super.from(data);
        if (data.distribution != undefined) {
            this.distribution.from(data.distribution);
        }
        if (data.entries != undefined) {
            for (let key in <{ [key: string]: any }>data.entries) {
                this.entries[key] = loadApiEntry(data.entries[key]);
            }
        }
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
        if (data.old != undefined) {
            this.old.from(data.old);
        }
        if (data.new != undefined) {
            this.new.from(data.new);
        }
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
}

export class ApiBreaking extends ApiDifference {
}

export class Report extends Product {
    old: Release = new Release();
    new: Release = new Release();

    from(data: any) {
        super.from(data);
        if (data.old != undefined) {
            this.old.from(data.old);
        }
        if (data.new != undefined) {
            this.new.from(data.new);
        }
    }
}

export class ProjectResult extends Product {
    project: string = "";
    pipeline: string = ""
    releases: Release[] = [];
    preprocessed: Release[] = [];
    extracted: Release[] = [];
    pairs: ReleasePair[] = [];
    diffed: ReleasePair[] = [];
    evaluated: ReleasePair[] = [];
    reported: ReleasePair[] = [];

    from(data: any) {
        super.from(data);
        if (data.project != undefined) {
            this.project = data.project;
        }
        if (data.pipeline != undefined) {
            this.pipeline = data.pipeline;
        }
        if (data.releases != undefined) {
            (<any[]>data.releases).forEach((value: any) => {
                let release = new Release();
                release.from(value);
                this.releases.push(release);
            });
        }
        if (data.preprocessed != undefined) {
            (<any[]>data.preprocessed).forEach((value: any) => {
                let release = new Release();
                release.from(value);
                this.preprocessed.push(release);
            });
        }
        if (data.extracted != undefined) {
            (<any[]>data.extracted).forEach((value: any) => {
                let release = new Release();
                release.from(value);
                this.extracted.push(release);
            });
        }
        if (data.pairs != undefined) {
            (<any[]>data.pairs).forEach((value: any) => {
                let pair = new ReleasePair();
                pair.from(value);
                this.pairs.push(pair);
            });
        }
        if (data.diffed != undefined) {
            (<any[]>data.diffed).forEach((value: any) => {
                let pair = new ReleasePair();
                pair.from(value);
                this.diffed.push(pair);
            });
        }
        if (data.evaluated != undefined) {
            (<any[]>data.evaluated).forEach((value: any) => {
                let pair = new ReleasePair();
                pair.from(value);
                this.evaluated.push(pair);
            });
        }
        if (data.reported != undefined) {
            (<any[]>data.reported).forEach((value: any) => {
                let pair = new ReleasePair();
                pair.from(value);
                this.reported.push(pair);
            });
        }
    }
}