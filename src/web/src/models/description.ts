export class TypeInfo {
    type: string = "";
    data: any = {};

    from(data: any) {
        if (data.type != null) {
            this.type = data.type;
        }
        if (data.data != null) {
            this.data = data.data;
        }
    }
}

export class Location {
    file: string = "";
    line: number = -1;
    module: string = "";

    from(data: any) {
        if (data.file != null) {
            this.file = data.file;
        }
        if (data.line != null) {
            this.line = data.line;
        }
        if (data.module != null) {
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

    from(data: any) {
        if (data.name != null) {
            this.name = data.name;
        }
        if (data.id != null) {
            this.id = data.id;
        }
        if (data.docs != null) {
            this.docs = data.docs;
        }
        if (data.comments != null) {
            this.comments = data.comments;
        }
        if (data.src != null) {
            this.src = data.src;
        }
        if (data.location != null) {
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
        if (data.members != null) {
            this.members = data.members;
        }
        if (data.annotations != null) {
            this.annotations = data.annotations;
        }
    }
}

export class ItemEntry extends ApiEntry {
    type?: TypeInfo;
    bound: boolean = false;

    from(data: any) {
        super.from(data);
        if (data.type != null) {
            this.type = new TypeInfo();
            this.type.from(data.type);
        }
        if (data.bound != null) {
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
        if (data.kind != null) {
            this.kind = data.kind;
        }
        if (data.data != null) {
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
        if (data.bases != null) {
            this.bases = data.bases;
        }
        if (data.abcs != null) {
            this.abcs = data.abcs;
        }
        if (data.mro != null) {
            this.mro = data.mro;
        }
        if (data.slots != null) {
            this.slots = data.slots;
        }
    }
}

export class AttributeEntry extends ItemEntry {
    rawType: string = "";

    from(data: any) {
        super.from(data);
        if (data.rawType != null) {
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

export class Parameter {
    kind: ParameterKind = ParameterKind.PositionalOrKeyword;
    name: string = "";
    annotation: string = "";
    default?: string;
    optional: boolean = false;
    source: string = "";
    type?: TypeInfo;

    from(data: any) {
        if (data.kind != null) {
            this.kind = data.kind;
        }
        if (data.name != null) {
            this.name = data.name;
        }
        if (data.annotation != null) {
            this.annotation = data.annotation;
        }
        if (data.default != null) {
            this.default = data.default;
        }
        if (data.optional != null) {
            this.optional = data.optional;
        }
        if (data.source != null) {
            this.source = data.source;
        }
        if (data.type != null) {
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
        if (data.returnAnnotation != null) {
            this.returnAnnotation = data.returnAnnotation;
        }
        if (data.parameters != null) {
            (<any[]>data.parameters).forEach(element => {
                let para = new Parameter();
                para.from(element);
                this.parameters.push(para);
            });
        }
        if (data.annotations != null) {
            this.annotations = data.annotations;
        }
        if (data.returnType != null) {
            this.returnType = new TypeInfo();
            this.returnType.from(data.returnType);
        }
    }
}

export function loadApiEntry(data: any): ApiEntry {
    switch(data.schema){
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