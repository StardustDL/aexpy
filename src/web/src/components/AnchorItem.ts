export class AnchorItem {
    title: string = "";
    href: string = "";
    children: AnchorItem[] = [];

    constructor(title: string = "", href: string = "", children?: AnchorItem[]) {
        this.title = title;
        this.href = href;
        if (children == undefined)
            children = [];
        this.children = children;
    }
}