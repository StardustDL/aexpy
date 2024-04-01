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
        this.id = data.id ?? "";
        this.kind = data.kind ?? "";
        this.rank = data.rank ?? BreakingRank.Unknown;
        this.message = data.message ?? "";
        this.data = data.data ?? {};
        if (data.old != undefined) {
            this.old = loadApiEntry(data.old);
        }
        if (data.new != undefined) {
            this.new = loadApiEntry(data.new);
        }
    }
}