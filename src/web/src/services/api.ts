import { ApiBreaking, ApiDescription, ApiDifference, Distribution, ProducerOptions, Product, ProjectResult, Release, ReleasePair, Report } from '../models'

export class Api {
    baseUrl: string;

    preprocessor: Preprocessor;
    extractor: Extractor;
    differ: Differ;
    evaluator: Evaluator;
    reporter: Reporter;
    batcher: Batcher;
    generator: Generator;
    raw: Raw;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.preprocessor = new Preprocessor(`${this.baseUrl}/preprocessing`);
        this.extractor = new Extractor(`${this.baseUrl}/extracting`);
        this.differ = new Differ(`${this.baseUrl}/differing`);
        this.evaluator = new Evaluator(`${this.baseUrl}/evaluating`);
        this.reporter = new Reporter(`${this.baseUrl}/reporting`);
        this.batcher = new Batcher(`${this.baseUrl}/batching`);
        this.generator = new Generator(`${this.baseUrl}/generating`);
        this.raw = new Raw(`${this.baseUrl}/raw`);
    }
}

export class Raw {
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

    async providers() {
        let results = await fetch(`${this.baseUrl}/providers`);
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

    async process(input: TIn, provider: string = "default", options?: ProducerOptions) {
        let results = await fetch(this.getUrl(this.toId(input), provider, options));
        let data = await results.json();
        let ret = this.create();
        ret.from(data);
        return ret;
    }

    getUrl(id: string, provider: string = "default", options?: ProducerOptions, log?: boolean) {
        let rst = "";

        if (options?.redo != undefined) {
            rst += `&redo=${options?.redo ? 1 : 0}`;
        }
        if (options?.onlyCache != undefined) {
            rst += `&onlyCache=${options?.onlyCache ? 1 : 0}`;
        }
        if (options?.cached != undefined) {
            rst += `&cached=${options?.cached ? 1 : 0}`;
        }
        if (log) {
            rst += `&log=${log ? 1 : 0}`;
        }

        return `${this.baseUrl}/${id}?provider=${provider}${rst}`
    }

    async log(input: TIn, provider: string = "default", options?: ProducerOptions) {
        let results = await fetch(this.getUrl(this.toId(input), provider, options, true));
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

export class Evaluator extends PairProducer<ApiBreaking> {
    create(): ApiBreaking {
        return new ApiBreaking();
    }
}

export class Reporter extends PairProducer<Report> {
    create(): Report {
        return new Report();
    }

    async report(input: ReleasePair, provider: string = "default", options?: ProducerOptions) {
        let results = await fetch(`${this.getUrl(this.toId(input), provider, options)}&report=1`);
        return await results.text();
    }
}

export class Batcher extends Producer<string, ProjectResult> {
    create(): ProjectResult {
        return new ProjectResult();
    }

    toId(input: string): string {
        return input;
    }

    async index(id: string, provider: string = "default", options?: ProducerOptions) {
        return await this.process(`${id}/index`, provider, options);
    }

    async indexlog(id: string, provider: string = "default", options?: ProducerOptions) {
        return await this.log(`${id}/index`, provider, options);
    }
}