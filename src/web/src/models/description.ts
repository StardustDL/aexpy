export class TypeInfo {
    type: string = "";
    data: any = {};

    from(data: any) {
        if (data.type != undefined) {
            this.type = data.type;
        }
        if (data.data != undefined) {
            this.data = data.data;
        }
    }
}

export class Location {
    file: string = "";
    line: number = -1;
    module: string = "";

    from(data: any) {
        if (data.file != undefined) {
            this.file = data.file;
        }
        if (data.line != undefined) {
            this.line = data.line;
        }
        if (data.module != undefined) {
            this.module = data.module;
        }
    }
}

export class ApiEntry {
    name: string = "";
    id: string = "";
    docs: string = "";
    comments: string = "";
    src: string = "";
    location?: Location;

    getType() {
        if (this instanceof ModuleEntry) {
            return "M";
        }
        else if (this instanceof ClassEntry) {
            return "C";
        }
        else if (this instanceof FunctionEntry) {
            return "F";
        }
        else if (this instanceof AttributeEntry) {
            return "A";
        }
        else if (this instanceof SpecialEntry) {
            return "S";
        }
        return "U";
    }

    from(data: any) {
        if (data.name != undefined) {
            this.name = data.name;
        }
        if (data.id != undefined) {
            this.id = data.id;
        }
        if (data.docs != undefined) {
            this.docs = data.docs;
        }
        if (data.comments != undefined) {
            this.comments = data.comments;
        }
        if (data.src != undefined) {
            this.src = data.src;
        }
        if (data.location != undefined) {
            this.location = new Location();
            this.location.from(data.location);
        }
    }
}

export class CollectionEntry extends ApiEntry {
    members: { [key: string]: string } = {};
    annotations: { [key: string]: string } = {};

    from(data: any) {
        super.from(data);
        if (data.members != undefined) {
            this.members = data.members;
        }
        if (data.annotations != undefined) {
            this.annotations = data.annotations;
        }
    }
}

export class ItemEntry extends ApiEntry {
    type?: TypeInfo;
    bound: boolean = false;

    from(data: any) {
        super.from(data);
        if (data.type != undefined) {
            this.type = new TypeInfo();
            this.type.from(data.type);
        }
        if (data.bound != undefined) {
            this.bound = data.bound;
        }
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
        if (data.kind != undefined) {
            this.kind = data.kind;
        }
        if (data.data != undefined) {
            this.data = data.data;
        }
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
        if (data.bases != undefined) {
            this.bases = data.bases;
        }
        if (data.abcs != undefined) {
            this.abcs = data.abcs;
        }
        if (data.mro != undefined) {
            this.mro = data.mro;
        }
        if (data.slots != undefined) {
            this.slots = data.slots;
        }
    }
}

export class AttributeEntry extends ItemEntry {
    rawType: string = "";

    from(data: any) {
        super.from(data);
        if (data.rawType != undefined) {
            this.rawType = data.rawType;
        }
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

export function getParameterKindName(kind: ParameterKind) {
    switch (kind) {
        case ParameterKind.Positional:
            return "Positional";
        case ParameterKind.PositionalOrKeyword:
            return "PositionalOrKeyword";
        case ParameterKind.VarPositional:
            return "VarPositional";
        case ParameterKind.Keyword:
            return "Keyword";
        case ParameterKind.VarKeyword:
            return "VarKeyword";
        case ParameterKind.VarKeywordCandidate:
            return "VarKeywordCandidate";
        default:
            return "Unknown";
    }
}

export class Parameter {
    kind: ParameterKind = ParameterKind.PositionalOrKeyword;
    name: string = "";
    annotation: string = "";
    default?: string;
    optional: boolean = false;
    source: string = "";
    type?: TypeInfo;

    from(data: any) {
        if (data.kind != undefined) {
            this.kind = data.kind;
        }
        if (data.name != undefined) {
            this.name = data.name;
        }
        if (data.annotation != undefined) {
            this.annotation = data.annotation;
        }
        if (data.default != undefined) {
            this.default = data.default;
        }
        if (data.optional != undefined) {
            this.optional = data.optional;
        }
        if (data.source != undefined) {
            this.source = data.source;
        }
        if (data.type != undefined) {
            this.type = new TypeInfo();
            this.type.from(data.type);
        }
    }
}

export class FunctionEntry extends ItemEntry {
    returnAnnotation: string = "";
    parameters: Parameter[] = [];
    annotations: { [key: string]: string } = {};
    returnType?: TypeInfo;

    from(data: any) {
        super.from(data);
        if (data.returnAnnotation != undefined) {
            this.returnAnnotation = data.returnAnnotation;
        }
        if (data.parameters != undefined) {
            (<any[]>data.parameters).forEach(element => {
                let para = new Parameter();
                para.from(element);
                this.parameters.push(para);
            });
        }
        if (data.annotations != undefined) {
            this.annotations = data.annotations;
        }
        if (data.returnType != undefined) {
            this.returnType = new TypeInfo();
            this.returnType.from(data.returnType);
        }
    }
}

export function loadApiEntry(data: any): ApiEntry {
    switch (data.schema) {
        case "attr":
            {
                let entry = new AttributeEntry();
                entry.from(data);
                return entry;
            }
        case "class":
            {
                let entry = new ClassEntry();
                entry.from(data);
                return entry;
            }
        case "func":
            {
                let entry = new FunctionEntry();
                entry.from(data);
                return entry;
            }
        case "module":
            {
                let entry = new ModuleEntry();
                entry.from(data);
                return entry;
            }
        case "special":
            {
                let entry = new SpecialEntry();
                entry.from(data);
                return entry;
            }
        default:
            {
                throw new Error("Unknown schema: " + data.schema);
            }
    }
}