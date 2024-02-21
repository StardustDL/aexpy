<script setup lang="ts">
import { NTree, NInput, NFlex, TreeOption, NButton } from 'naive-ui';
import { computed, h, onMounted, ref, watch } from 'vue';
import ApiEntryLink from '../metadata/ApiEntryLink.vue';
import ApiEntryTypeTag from '../metadata/ApiEntryTypeTag.vue';
import ApiEntryMetadataTag from '../metadata/ApiEntryMetadataTag.vue';
import { ApiDescription } from '../../models'
import { ApiEntry, FunctionEntry } from '../../models/description';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { hashedColor, apiUrl } from '../../services/utils';
import { Api } from '@vicons/tabler';

const props = defineProps<{
    api: ApiDescription,
    current?: ApiEntry,
    pattern?: string,
    entryUrl?: string,
}>();

const data = ref<TreeOption[]>([]);

function buildTreeOption(tree: Map<string, string[]>, current: string): TreeOption | null {
    let childrenOptions: TreeOption[] = [];
    if (tree.has(current)) {
        let children = tree.get(current)!;
        for (let item of children) {
            let option = buildTreeOption(tree, item);
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
            { entry: props.api.entry(current)! },
            {}
        ),
        suffix: () =>
            h(NFlex, {}, {
                default: () => [h(
                    ApiEntryMetadataTag,
                    { entry: props.api.entry(current)! },
                    {}
                ), h(
                    ApiEntryLink,
                    { url: props.entryUrl ?? apiUrl(props.api.distribution.release), entry: current, text: false, icon: true },
                    {}
                )]
            })
    };
}

function show() {
    let tree = new Map<string, string[]>();
    let roots: string[] = [];
    for (let item of props.api.entries()) {
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
    data.value = [];
    for (let item of roots) {
        let option = buildTreeOption(tree, item);
        if (option != null) data.value.push(option);
    }
}

const defaultExpandedKeys = computed(() => {
    if (!props.current) {
        return [];
    }
    let parts = props.current.id.split(".");
    let result = [];
    let current = "";
    for (let part of parts) {
        if (current == "") {
            current = part;
        } else {
            current += `.${part}`;
        }
        result.push(current);
    }
    return result;
})

watch(props, (newVal, oldVal) => {
    show();
});

onMounted(() => {
    show();
});

</script>

<template>
    <n-tree :pattern="props.pattern" :data="data" block-line :default-expanded-keys="defaultExpandedKeys" />
</template>