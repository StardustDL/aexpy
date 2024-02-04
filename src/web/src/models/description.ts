export class Location {
    file: string = "";
    line: number = -1;
    module: string = "";

    from(data: any) {
        this.file = data.file ?? "";
        this.line = data.line ?? -1;
        this.module = data.module ?? "";
    }
}

export class ApiEntry {
    name: string = "";
    id: string = "";
    alias: string[] = [];
    docs: string = "";
    comments: string = "";
    src: string = "";
    location?: Location;
    private: boolean = false;
    data: any = {};
    parent: string = "";

    from(data: any) {
        this.name = data.name ?? "";
        this.id = data.id ?? "";
        this.alias = data.alias ?? [];
        this.docs = data.docs ?? "";
        this.comments = data.comments ?? "";
        this.src = data.src ?? "";
        this.private = data.private ?? false;
        this.data = data.data ?? {};
        this.parent = data.parent ?? "";

        if (data.location) {
            this.location = new Location();
            this.location.from(data.location);
        }
    }
}

export function getTypeColor(entry: ApiEntry | string) {
    if (entry instanceof ApiEntry) {
        entry = <string>Object.getPrototypeOf(entry).constructor.name.replace("Entry", "");
    }

    switch (entry) {
        case "Module":
            return '#2080f0';
        case "Class":
            return '#f0a020';
        case "Function":
            return '#18a058';
        case "Attribute":
            return '#d03050';
        default:
            return '#666666';
    }
}

export class CollectionEntry extends ApiEntry {
    members: { [key: string]: string } = {};
    annotations: { [key: string]: string } = {};

    from(data: any) {
        super.from(data);
        this.members = data.members ?? {};
        this.annotations = data.annotations ?? {};
    }
}

export enum ItemScope {
    Static = 0,
    Class = 1,
    Instance = 2,
}

export class ItemEntry extends ApiEntry {
    type?: any;
    scope: ItemScope = ItemScope.Static;


    from(data: any) {
        super.from(data);
        this.scope = data.scope ?? ItemScope.Static;
        this.type = data.type;
    }
}

export enum SpecialKind {
    Unknown = 0,
    Empty = 1,
    External = 2,
}

export class SpecialEntry extends ApiEntry {
    kind: SpecialKind = SpecialKind.Unknown;
    data: string = "";

    from(data: any) {
        super.from(data);
        this.kind = data.kind ?? SpecialKind.Unknown;
        this.data = data.data ?? "";
    }
}

export class ModuleEntry extends CollectionEntry {
}

export class ClassEntry extends CollectionEntry {
    bases: string[] = [];
    abcs: string[] = [];
    mro: string[] = [];
    slots: string[] = [];

    from(data: any) {
        super.from(data);
        this.bases = data.bases ?? [];
        this.abcs = data.abcs ?? [];
        this.mro = data.mro ?? [];
        this.slots = data.slots ?? [];
    }
}

export class AttributeEntry extends ItemEntry {
    rawType: string = "";
    annotation: string = "";
    property: boolean = false;

    from(data: any) {
        super.from(data);
        this.rawType = data.rawType ?? "";
        this.annotation = data.annotation ?? "";
        this.property = data.property ?? false;
    }
}

export enum ParameterKind {
    Positional = 0,
    PositionalOrKeyword = 1,
    VarPositional = 2,
    Keyword = 3,
    VarKeyword = 4,
    VarKeywordCandidate = 5,
}

export class Parameter {
    kind: ParameterKind = ParameterKind.PositionalOrKeyword;
    name: string = "";
    annotation: string = "";
    default?: string;
    optional: boolean = false;
    source: string = "";
    type?: any;

    from(data: any) {
        this.kind = data.kind ?? ParameterKind.PositionalOrKeyword;
        this.name = data.name ?? "";
        this.annotation = data.annotation ?? "";
        this.default = data.default;
        this.optional = data.optional ?? false;
        this.source = data.source ?? "";
        if (data.type != undefined) {
            this.type = data.type;
        }
    }
}

export class FunctionEntry extends ItemEntry {
    returnAnnotation: string = "";
    parameters: Parameter[] = [];
    annotations: { [key: string]: string } = {};
    returnType?: any;
    callers: string[] = [];
    callees: string[] = [];
    transmitKwargs: boolean = false;

    varPositional() {
        return this.parameters.find(p => p.kind == ParameterKind.VarPositional);
    }

    varKeyword() {
        return this.parameters.find(p => p.kind == ParameterKind.VarKeyword);
    }

    from(data: any) {
        super.from(data);
        this.returnAnnotation = data.returnAnnotation ?? "";
        (<any[]>data.parameters ?? []).forEach(element => {
            let para = new Parameter();
            para.from(element);
            this.parameters.push(para);
        });
        this.annotations = data.annotations ?? {};
        if (data.returnType != undefined) {
            this.returnType = data.returnType
        }
        this.callers = data.callers ?? [];
        this.callees = data.callees ?? [];
        this.transmitKwargs = data.transmitKwargs ?? false;
    }
}

export function loadApiEntry(data: any): ApiEntry {
    let entry = undefined;
    switch (data.form) {
        case "attr":
            entry = new AttributeEntry();
            break;
        case "class":
            entry = new ClassEntry();
            break;
        case "func":
            entry = new FunctionEntry();
            break;
        case "module":
            entry = new ModuleEntry();
            break;
        case "special":
            entry = new SpecialEntry();
            break;
        default:
            throw new Error("Unknown schema: " + data.schema);
    }
    entry.from(data);
    return entry;
}