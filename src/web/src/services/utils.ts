import { Distribution, Release, ReleasePair, ApiDescription, ApiDifference, Report } from "../models";
import { ApiEntry, ModuleEntry, ClassEntry, FunctionEntry, AttributeEntry, Location, Parameter, ParameterKind } from "../models/description";
import { DiffEntry, BreakingRank } from "../models/difference";

export function projectUrl(name: string) {
    return `/projects/${name}`;
}

export function distributionUrl(release: Release) {
    return `${projectUrl(release.project)}/@${release.version}`;
}

export function apiUrl(release: Release) {
    return `${projectUrl(release.project)}/${release.version}`;
}

export function changeUrl(pair: ReleasePair) {
    if (!pair.sameProject()) {
        throw new Error(`Difference project: ${pair.toString()}`);
    }
    return `${projectUrl(pair.old.project)}/${pair.old.version}..${pair.new.version}`;
}

export function reportUrl(pair: ReleasePair) {
    if (!pair.sameProject()) {
        throw new Error(`Difference project: ${pair.toString()}`);
    }
    return `${projectUrl(pair.old.project)}/${pair.old.version}&${pair.new.version}`;
}

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
        "ApiDifference": ApiDifference,
        "Report": Report,
        "ApiEntry": ApiEntry,
        "ModuleEntry": ModuleEntry,
        "ClassEntry": ClassEntry,
        "FunctionEntry": FunctionEntry,
        "AttributeEntry": AttributeEntry,
        "Location": Location,
        "Parameter": Parameter,
        "ParameterKind": ParameterKind,
        "DiffEntry": DiffEntry,
        "BreakingRank": BreakingRank,
    });
}

export async function compress(inString: string) {
    const compressedStream = new Response(inString).body!.pipeThrough(new CompressionStream('gzip'));
    return await new Response(compressedStream).arrayBuffer();
}

export async function decompress(bytes: ArrayBuffer) {
    const decompressedStream = new Response(bytes).body!.pipeThrough(new DecompressionStream('gzip'));
    const outString = await new Response(decompressedStream).text();
    return outString;
}

export function decode(bytes: ArrayBuffer) {
    return new TextDecoder().decode(bytes);
}

export function encode(inString: string) {
    return new TextEncoder().encode(inString);
}

export async function autoDecompressAndDecode(bytes: ArrayBuffer) {
    try {
        return decode(bytes);
    } catch { }
    return await decompress(bytes);
}

export async function autoDecompressAndParse(bytes: ArrayBuffer) {
    try {
        return JSON.parse(decode(bytes));
    } catch { }
    return JSON.parse(await decompress(bytes));
}