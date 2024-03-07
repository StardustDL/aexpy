import { NTree, NInput, NFlex, TreeOption, NButton, NTooltip, NText, PaginationProps } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import ApiEntryLink from '../components/links/ApiEntryLink.vue'
import ApiEntryTypeTag from '../components/metadata/ApiEntryTypeTag.vue'
import ApiEntryMetadataTag from '../components/metadata/ApiEntryMetadataTag.vue'
import { ApiDescription } from '../models'
import { hashedColor, apiUrl } from './utils';
import { ApiEntry, AttributeEntry, ClassEntry, FunctionEntry, ModuleEntry } from '../models/description'

function buildApiTreeOption(tree: Map<string, string[]>, current: string, api: ApiDescription, entryUrl: string | undefined = undefined): {
    option: TreeOption,
    count: {
        module: number,
        class: number,
        function: number,
        attribute: number,
    }
} {
    let childrenOptions: TreeOption[] = [];
    let count = {
        module: 0,
        class: 0,
        function: 0,
        attribute: 0,
    }
    if (tree.has(current)) {
        let children = tree.get(current)!;
        for (let item of children) {
            let child = buildApiTreeOption(tree, item, api, entryUrl);
            childrenOptions.push(child.option);
            count.module += child.count.module;
            count.class += child.count.class;
            count.function += child.count.function;
            count.attribute += child.count.attribute;
        }
    }

    let countStrs: string[] = [];
    if (childrenOptions.length > 0) {
        if (count.module > 0)
            countStrs.push(`${count.module} module${count.module > 1 ? 's' : ''}`);
        if (count.class > 0)
            countStrs.push(`${count.class} class${count.class > 1 ? 'es' : ''}`);
        if (count.function > 0)
            countStrs.push(`${count.function} func${count.function > 1 ? 's' : ''}`);
        if (count.attribute > 0)
            countStrs.push(`${count.attribute} attr${count.attribute > 1 ? 's' : ''}`);
    }

    let entry = api.entry(current)!;
    if (entry instanceof ModuleEntry) count.module += 1;
    else if (entry instanceof ClassEntry) count.class += 1;
    else if (entry instanceof FunctionEntry) count.function += 1;
    else if (entry instanceof AttributeEntry) count.attribute += 1;

    return {
        option: {
            label: entry.name,
            key: current,
            children: childrenOptions,
            isLeaf: childrenOptions.length == 0,
            prefix: () => h(
                ApiEntryTypeTag,
                { entry: entry },
                {}
            ),
            suffix: () =>
                h(NFlex, { align: 'center' }, {
                    default: () => [h(NText, { depth: 3 }, { default: () => countStrs.join(", ") }), h(
                        ApiEntryMetadataTag,
                        { entry: entry },
                        {}
                    ), h(
                        ApiEntryLink,
                        { url: entryUrl ?? apiUrl(api.distribution.release), entry: current, text: false, icon: true },
                        {}
                    )]
                })
        },
        count
    };
}

export function buildApiTreeOptions(api: ApiDescription, entryUrl: string | undefined = undefined) {
    let tree = new Map<string, string[]>();
    let roots: string[] = [];
    let sorter = (a: ApiEntry, b: ApiEntry) => {
        if (a.id < b.id) {
            return -1;
        } else if (a.id > b.id) {
            return 1;
        } else {
            return 0;
        }
    }
    let entries = (<ApiEntry[]>[]).concat(
        Object.values(api.modules).sort(sorter),
        Object.values(api.classes).sort(sorter),
        Object.values(api.functions).sort(sorter),
        Object.values(api.attributes).sort(sorter),
        Object.values(api.specials).sort(sorter));
    for (let item of entries) {
        if (item.parent == "") {
            tree.set(item.id, []);
            roots.push(item.id);
            continue;
        }
        if (!tree.has(item.parent)) {
            tree.set(item.parent, []);
        }
        tree.get(item.parent)!.push(item.id);
    }
    let result: TreeOption[] = [];
    for (let item of roots) {
        let option = buildApiTreeOption(tree, item, api, entryUrl);
        result.push(option.option);
    }
    return result;
}

export function renderApiTreeLabel(api: ApiDescription, info: { option: TreeOption, checked: boolean, selected: boolean }) {
    let entry = api.entry(info.option.key?.toString() ?? "");
    if (entry && entry.docs.trim() != "") {
        return h(NTooltip, {}, { trigger: () => entry!.name, default: () => entry!.docs.trim() })
    }
    return h(NText, {}, { default: () => entry?.name ?? info.option.label ?? "" });
}

export function filterApiTreeOption(pattern: string, option: TreeOption) {
    return (option.key?.toString() ?? "").includes(pattern);
}

export const DefaultPaginationProps: PaginationProps = { pageSizes: [10, 20, 50], showQuickJumper: true, showSizePicker: true };