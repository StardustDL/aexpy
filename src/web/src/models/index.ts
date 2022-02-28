import { ApiEntry, loadApiEntry } from "./description";
import { DiffEntry } from "./difference";

export class Product {
    creation: Date = new Date();
    duration: number = 0;
    success: boolean = false;

    from(data: any) {
        if (data.creation != null) {
            this.creation = new Date(data.creation);
        }
        if (data.duration != null) {
            this.duration = data.duration;
        }
        if (data.success != null) {
            this.success = data.success;
        }
    }
}

export class Release {
    project: string = "";
    version: string = "";

    from(data: any) {
        if (data.project != null) {
            this.project = data.project;
        }
        if (data.version != null) {
            this.version = data.version;
        }
    }
}

export class Distribution extends Product {
    release: Release = new Release();
    pyversion: string = "";
    topModules: string[] = [];

    from(data: any) {
        super.from(data);
        if (data.release != null) {
            this.release.from(data.release);
        }
        if (data.pyversion != null) {
            this.pyversion = data.pyversion;
        }
        if (data.topModules != null) {
            this.topModules = data.topModules;
        }
    }
}

export class ApiDescription extends Product {
    distribution: Distribution = new Distribution();
    entries: { [key: string]: ApiEntry } = {};

    from(data: any) {
        super.from(data);
        if (data.distribution != null) {
            this.distribution.from(data.distribution);
        }
        if (data.entries != null) {
            (<{ [key: string]: any }>data.entries).forEach((value: any, key: string) => {
                let entry = loadApiEntry(value);
                this.entries[entry.id] = entry;
            });
        }
    }
}

export class ApiDifference extends Product {
    old: Distribution = new Distribution();
    new: Distribution = new Distribution();
    entries: { [key: string]: DiffEntry } = {};

    from(data: any) {
        super.from(data);
        if (data.old != null) {
            this.old.from(data.old);
        }
        if (data.new != null) {
            this.new.from(data.new);
        }
        if (data.entries != null) {
            (<{ [key: string]: any }>data.entries).forEach((value: any, key: string) => {
                let entry = new DiffEntry();
                entry.from(value);
                this.entries[entry.id] = entry;
            });
        }
    }
}

export class ApiBreaking extends ApiDifference {
}

export class Report extends Product {
    old: Release = new Release();
    new: Release = new Release();

    from(data: any) {
        super.from(data);
        if (data.old != null) {
            this.old.from(data.old);
        }
        if (data.new != null) {
            this.new.from(data.new);
        }
    }
}