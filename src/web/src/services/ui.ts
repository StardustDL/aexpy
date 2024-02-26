import { NTree, NInput, NFlex, TreeOption, NButton, NTooltip, NText } from 'naive-ui'
import { computed, h, onMounted, ref, watch } from 'vue'
import ApiEntryLink from '../components/links/ApiEntryLink.vue'
import ApiEntryTypeTag from '../components/metadata/ApiEntryTypeTag.vue'
import ApiEntryMetadataTag from '../components/metadata/ApiEntryMetadataTag.vue'
import { ApiDescription } from '../models'
import { hashedColor, apiUrl } from './utils';

function buildApiTreeOption(tree: Map<string, string[]>, current: string, api: ApiDescription, entryUrl: string | undefined = undefined): TreeOption | null {
    let childrenOptions: TreeOption[] = [];
    if (tree.has(current)) {
        let children = tree.get(current)!;
        for (let item of children) {
            let option = buildApiTreeOption(tree, item, api, entryUrl);
            if (option) childrenOptions.push(option);
        }
    }
    let parts = current.split(".");
    return {
        label: parts[parts.length - 1],
        key: current,
        children: childrenOptions,
        isLeaf: childrenOptions.length == 0,
        prefix: () => h(
            ApiEntryTypeTag,
            { entry: api.entry(current)! },
            {}
        ),
        suffix: () =>
            h(NFlex, {}, {
                default: () => [h(
                    ApiEntryMetadataTag,
                    { entry: api.entry(current)! },
                    {}
                ), h(
                    ApiEntryLink,
                    { url: entryUrl ?? apiUrl(api.distribution.release), entry: current, text: false, icon: true },
                    {}
                )]
            })
    };
}

export function buildApiTreeOptions(api: ApiDescription, entryUrl: string | undefined = undefined) {
    let tree = new Map<string, string[]>();
    let roots: string[] = [];
    for (let item of api.entries()) {
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
    let result = [];
    for (let item of roots) {
        let option = buildApiTreeOption(tree, item, api, entryUrl);
        if (option != null) result.push(option);
    }
    return result;
}

export function renderApiTreeLabel(api: ApiDescription, info: { option: TreeOption, checked: boolean, selected: boolean }) {
    let entry = api.entry(info.option.key?.toString() ?? "");
    if (entry && entry.docs.trim() != "") {
        return h(NTooltip, {}, { trigger: () => info.option.label, default: () => entry!.docs.trim() })
    }
    return h(NText, {}, { default: () => info.option.label });
}