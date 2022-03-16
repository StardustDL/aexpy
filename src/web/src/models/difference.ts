import { ApiEntry, loadApiEntry } from "./description";

export enum BreakingRank {
    Unknown = -1,
    Compatible = 0,
    Low = 30,
    Medium = 60,
    High = 100,
}

export enum VerifyState {
    None,
    Unknown,
    Fail,
    Pass
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
        case VerifyState.Unknown: return '#2080f0';
        // case BreakingRank.Medium: return '#f0a020';
        case VerifyState.Fail: return '#d03050';
        default: return '#666666';
    }
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

    verified() {
        if (this.data.trigger && this.data.triggerResultOld && this.data.triggerResultNew) {
            if (this.data.triggerResultOld.exit != null && this.data.triggerResultNew.exit != null) {
                if (this.data.triggerResultOld.exit == 0) {
                    if (this.data.triggerResultNew.exit != 0) {
                        return VerifyState.Pass;
                    }
                    else {
                        return VerifyState.Fail;
                    }
                }
                else {
                    return VerifyState.Unknown;
                }
            }
            else {
                return VerifyState.Unknown;
            }
        }
        return VerifyState.None;
    }
}