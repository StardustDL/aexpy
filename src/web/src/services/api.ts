import { ApiBreaking, ApiDescription, ApiDifference, Distribution, Product, Release, Report } from '../models'

export class Api {
    baseUrl: string;

    preprocessor: Preprocessor;
    extractor: Extractor;
    differ: Differ;
    evaluator: Evaluator;
    reporter: Reporter;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
        this.preprocessor = new Preprocessor(`${this.baseUrl}/preprocessing`);
        this.extractor = new Extractor(`${this.baseUrl}/extracting`);
        this.differ = new Differ(`${this.baseUrl}/diffing`);
        this.evaluator = new Evaluator(`${this.baseUrl}/evaluating`);
        this.reporter = new Reporter(`${this.baseUrl}/reporting`);
    }
}

export abstract class Producer<T extends Product> {
    baseUrl: string;

    constructor(baseUrl: string) {
        this.baseUrl = baseUrl;
    }

    abstract create(): T;

    async process(id: string, provider: string = "default") {
        let results = await fetch(`${this.baseUrl}/${id}?provider=${provider}`);
        let data = await results.json();
        let ret = this.create();
        ret.from(data);
        return ret;
    }

    async log(id: string, provider: string = "default") {
        let results = await fetch(`${this.baseUrl}/${id}?provider=${provider}&log=1`);
        return await results.text();
    }
}

export class Preprocessor extends Producer<Distribution> {
    create(): Distribution {
        return new Distribution();
    }
}

export class Extractor extends Producer<ApiDescription> {
    create(): ApiDescription {
        return new ApiDescription();
    }
}

export class Differ extends Producer<ApiDifference> {
    create(): ApiDifference {
        return new ApiDifference();
    }
}

export class Evaluator extends Producer<ApiBreaking> {
    create(): ApiBreaking {
        return new ApiBreaking();
    }
}

export class Reporter extends Producer<Report> {
    create(): Report {
        return new Report();
    }
}