import { ApiEntry, loadApiEntry } from "./description";

export enum BreakingRank {
    Unknown = -1,
    Compatible = 0,
    Low = 30,
    Medium = 60,
    High = 100,
}

export enum VerifyState {
    Unknown = 0,
    Fail = 50,
    Pass = 100,
}

export class VerifyData {
    state: VerifyState = VerifyState.Unknown;
    message: string = "";
    verifier: string = "";

    from(data: any) {
        this.state = data.state ?? VerifyState.Unknown;
        this.message = data.message ?? "";
        this.verifier = data.verifier ?? "";
    }
}

export function getRankColor(rank: BreakingRank) {
    switch (rank) {
        case BreakingRank.Compatible: return '#18a058';
        case BreakingRank.Low: return '#2080f0';
        case BreakingRank.Medium: return '#f0a020';
        case BreakingRank.High: return '#d03050';
        default: return '#666666';
    }
}

export function getVerifyColor(ver: VerifyState) {
    switch (ver) {
        case VerifyState.Pass: return '#18a058';
        case VerifyState.Unknown: return '#666666';
        case VerifyState.Fail: return '#d03050';
    }
}

export class DiffEntry {
    id: string = "";
    kind: string = "";
    rank: BreakingRank = BreakingRank.Unknown;
    verify: VerifyData = new VerifyData();
    message: string = "";
    data: any = {};
    old?: ApiEntry;
    new?: ApiEntry;

    from(data: any) {
        this.id = data.id ?? "";
        this.kind = data.kind ?? "";
        this.rank = data.rank ?? BreakingRank.Unknown;
        if (this.verify != undefined) {
            this.verify.from(data.verify);
        }
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