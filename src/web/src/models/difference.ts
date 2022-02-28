import { ApiEntry, loadApiEntry } from "./description";

export enum BreakingRank {
    Unknown = -1,
    Compatible = 0,
    Low = 30,
    Medium = 60,
    High = 100,
}

export class DiffEntry {
    id: string = "";
    kind: string = "";
    rank: BreakingRank = BreakingRank.Unknown;
    message: string = "";
    data: any = {};
    old?: ApiEntry;
    new?: ApiEntry;

    from(data: any) {
        if (data.id != null) {
            this.id = data.id;
        }
        if (data.kind != null) {
            this.kind = data.kind;
        }
        if (data.rank != null) {
            this.rank = data.rank;
        }
        if (data.message != null) {
            this.message = data.message;
        }
        if (data.data != null) {
            this.data = data.data;
        }
        if (data.old != null) {
            this.old = loadApiEntry(data.old);
        }
        if (data.new != null) {
            this.new = loadApiEntry(data.new);
        }
    }
}