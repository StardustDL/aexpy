import { ApiDescription, ApiDifference, Distribution, ProduceMode, Product, BatchResult, Release, ReleasePair, Report } from '../models'

export class Api {
    baseUrl: string;

    preprocessor: Preprocessor;
    extractor: Extractor;
    differ: Differ;
    reporter: Reporter;
    batcher: Batcher;
    generator: Generator;
    data: RawData;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.preprocessor = new Preprocessor(`${this.baseUrl}/preprocessing`);
        this.extractor = new Extractor(`${this.baseUrl}/extracting`);
        this.differ = new Differ(`${this.baseUrl}/diffing`);
        this.reporter = new Reporter(`${this.baseUrl}/reporting`);
        this.batcher = new Batcher(`${this.baseUrl}/batching`);
        this.generator = new Generator(`${this.baseUrl}/generating`);
        this.data = new RawData(`${this.baseUrl}/data`);
    }
}

export class RawData {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    getUrl(path: string) {
        return `${this.baseUrl}/${path}`;
    }

    async text(path: string) {
        const response = await fetch(this.getUrl(path));
        if (response.status !== 200) {
            throw new Error(`${response.status} ${response.statusText}`);
        }
        return await response.text();
    }

    async json(path: string) {
        let response = await fetch(this.getUrl(path));
        if (response.status !== 200) {
            throw new Error(`${response.status} ${response.statusText}`);
        }
        let data: any = await response.json();
        return data;
    }
}

export class Generator {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    async releases(project: string) {
        let results = await fetch(`${this.baseUrl}/releases/${project}`);
        let data: any[] = await results.json();
        let ret: Release[] = [];
        data.forEach(value => {
            let rel = new Release();
            rel.from(value);
            ret.push(rel);
        });
        return ret;
    }

    async pairs(project: string) {
        let results = await fetch(`${this.baseUrl}/pairs/${project}`);
        let data: any[] = await results.json();
        let ret: ReleasePair[] = [];
        data.forEach(value => {
            let pair = new ReleasePair();
            pair.from(value);
            ret.push(pair);
        });
        return ret;
    }

    async pipelines() {
        let results = await fetch(`${this.baseUrl}/pipelines`);
        let data: string[] = await results.json();
        return data;
    }
}

export abstract class Producer<TIn, T extends Product> {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    abstract create(): T;

    abstract toId(input: TIn): string;

    async process(input: TIn, pipeline: string = "default", mode: ProduceMode = ProduceMode.Access) {
        let results = await fetch(this.getUrl(this.toId(input), pipeline, mode), { method: this.getMethod(mode) });
        let data = await results.json();
        let ret = this.create();
        ret.from(data);
        return ret;
    }

    getMethod(mode: ProduceMode = ProduceMode.Access, log?: boolean) {
        if (log == true) {
            return "GET";
        }
        switch (mode) {
            case ProduceMode.Access:
                return "PUT";
            case ProduceMode.Read:
                return "GET"
            case ProduceMode.Write:
                return "POST";
        }
    }

    getUrl(id: string, pipeline: string = "default", mode: ProduceMode = ProduceMode.Access, log?: boolean) {
        let rst = "";

        if (log) {
            rst += `&log=${log ? 1 : 0}`;
        }

        return `${this.baseUrl}/${id}?pipeline=${pipeline}${rst}`
    }

    async log(input: TIn, provider: string = "default", mode: ProduceMode = ProduceMode.Access) {
        let results = await fetch(this.getUrl(this.toId(input), provider, mode, true), { method: this.getMethod(mode, true) });
        return await results.text();
    }
}

export abstract class SingleProducer<T extends Product> extends Producer<Release, T> {
    toId(input: Release): string {
        return input.toString()
    }
}

export abstract class PairProducer<T extends Product> extends Producer<ReleasePair, T> {
    toId(input: ReleasePair): string {
        return input.toString()
    }
}

export class Preprocessor extends SingleProducer<Distribution> {
    create(): Distribution {
        return new Distribution();
    }
}

export class Extractor extends SingleProducer<ApiDescription> {
    create(): ApiDescription {
        return new ApiDescription();
    }
}

export class Differ extends PairProducer<ApiDifference> {
    create(): ApiDifference {
        return new ApiDifference();
    }
}

export class Reporter extends PairProducer<Report> {
    create(): Report {
        return new Report();
    }
}

export class Batcher extends Producer<string, BatchResult> {
    create(): BatchResult {
        return new BatchResult();
    }

    toId(input: string): string {
        return input;
    }

    async index(id: string, provider: string = "default", mode: ProduceMode = ProduceMode.Access) {
        let results = await fetch(`${this.getUrl(this.toId(id), provider, mode, true)}&index=1`, { method: this.getMethod(mode) });
        let data = await results.json();
        let ret = this.create();
        ret.from(data);
        return ret;
    }

    async indexlog(id: string, provider: string = "default", mode: ProduceMode = ProduceMode.Access) {
        let results = await fetch(`${this.getUrl(this.toId(id), provider, mode, true)}&index=1`, { method: this.getMethod(mode, true) });
        return await results.text();
    }
}