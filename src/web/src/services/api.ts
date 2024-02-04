import { ApiDescription, ApiDifference, Distribution, ProduceMode, Product, Release, ReleasePair, Report, Info } from '../models'

export class Api {
    baseUrl: string;

    preprocessor: Preprocessor;
    extractor: Extractor;
    differ: Differ;
    reporter: Reporter;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.preprocessor = new Preprocessor(`${this.baseUrl}/preprocess`);
        this.extractor = new Extractor(`${this.baseUrl}/extract`);
        this.differ = new Differ(`${this.baseUrl}/diff`);
        this.reporter = new Reporter(`${this.baseUrl}/report`);
    }

    async info() {
        if (import.meta.env.VITE_NOSERVER) {
            return new Info(import.meta.env.VITE_COMMIT_ID ?? "unknown", new Date(import.meta.env.VITE_BUILD_DATE ?? new Date()));
        } else {
            let results = await fetch(`${this.baseUrl}/info`);
            let data = await results.json();
            return new Info(data.commitId ?? "unknown", new Date(data.buildDate ?? new Date()));
        }
    }
}

export abstract class Producer<TIn, T extends Product> {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    abstract create(): T;

    abstract toId(input: TIn): string;

    async process(input: TIn, mode: ProduceMode = ProduceMode.Access) {
        const id = this.toId(input);
        const cached = window.sessionStorage.getItem(id);
        let data = {};
        if (cached != null) {
            data = JSON.parse(cached);
        } else {
            let results = await fetch(this.getUrl(this.toId(input), mode), { method: this.getMethod(mode) });
            data = await results.json();
        }
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

    getUrl(id: string, mode: ProduceMode = ProduceMode.Access, log?: boolean) {
        let rst = "";

        if (log) {
            rst += `?log=${log ? 1 : 0}`;
        }

        return `${this.baseUrl}/${id}${rst}`
    }

    async log(input: TIn, mode: ProduceMode = ProduceMode.Access) {
        let results = await fetch(this.getUrl(this.toId(input), mode, true), { method: this.getMethod(mode, true) });
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
