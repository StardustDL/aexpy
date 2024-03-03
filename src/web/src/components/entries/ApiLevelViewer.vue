<script setup lang="ts">
import { NTree, NInput, NFlex, TreeOption, NButton, NText, NTooltip } from 'naive-ui';
import { computed, h, onMounted, ref, watch } from 'vue';
import ApiEntryLink from '../links/ApiEntryLink.vue';
import ApiEntryTypeTag from '../metadata/ApiEntryTypeTag.vue';
import ApiEntryMetadataTag from '../metadata/ApiEntryMetadataTag.vue';
import { ApiDescription } from '../../models'
import { ApiEntry, FunctionEntry } from '../../models/description';
import { Network } from 'vis-network';
import { DataSet } from 'vis-data';
import { hashedColor, apiUrl } from '../../services/utils';
import { buildApiTreeOptions, renderApiTreeLabel, filterApiTreeOption } from '../../services/ui';
import { Api } from '@vicons/tabler';

const props = defineProps<{
    api: ApiDescription,
    current?: ApiEntry,
    pattern?: string,
    entryUrl?: string,
}>();

const data = computed(() => buildApiTreeOptions(props.api, props.entryUrl));

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


</script>

<template>
    <n-tree :pattern="props.pattern" :data="data" block-line :default-expanded-keys="defaultExpandedKeys"
        :show-irrelevant-nodes="false" :render-label="(info) => renderApiTreeLabel(api, info)" virtual-scroll
        :filter="filterApiTreeOption" style="height: 600px" />
</template>