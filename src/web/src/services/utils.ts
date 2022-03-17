import { Distribution, Release, ReleasePair, ApiDescription, ApiBreaking, ApiDifference, Report } from "../models";
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, TypeInfo, Location, Parameter, ParameterKind } from "../models/description";
import { DiffEntry, BreakingRank } from "../models/difference";


export function hashedColor(name: string) {
    var hash = 0, i, chr;
    for (i = 0; i < name.length; i++) {
        chr = name.charCodeAt(i);
        hash = ((hash * 29) - hash) + chr;
        hash |= 0; // Convert to 32bit integer
    }
    if (hash < 0) {
        hash = -hash;
    }
    let str = ('000000' + (hash / (1 << 30) * 0x1000000 << 0).toString(16));
    return '#' + str.substring(str.length - 6);
}

export function numberSum(values: number[]) {
    return values.reduce((a, b) => a + b, 0);
}

export function numberAverage(values: number[]) {
    return numberSum(values) / values.length;
}

export function publicVars(obj: any) {
    for (let key in obj) {
        Object.defineProperty(window, key, {
            value: obj[key],
            configurable: true,
        });
    }
}

export function publicModels() {
    publicVars({
        "Release": Release,
        "ReleasePair": ReleasePair,
        "Distribution": Distribution,
        "ApiDescription": ApiDescription,
        "ApiBreaking": ApiBreaking,
        "ApiDifference": ApiDifference,
        "Report": Report,
        "ApiEntry": ApiEntry,
        "ModuleEntry": ModuleEntry,
        "ClassEntry": ClassEntry,
        "FunctionEntry": FunctionEntry,
        "AttributeEntry": AttributeEntry,
        "TypeInfo": TypeInfo,
        "Location": Location,
        "Parameter": Parameter,
        "ParameterKind": ParameterKind,
        "DiffEntry": DiffEntry,
        "BreakingRank": BreakingRank,
    });
}