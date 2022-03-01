<script setup lang="ts">
import { NSpace, NDescriptions, NDescriptionsItem, NButton } from 'naive-ui'
import { Distribution, Product } from '../../models'
import MetadataTimeViewer from './MetadataTimeViewer.vue'
import MetadataDurationViewer from './MetadataDurationViewer.vue'
import MetadataSuccessViewer from './MetadataSuccessViewer.vue'

const props = defineProps<{
    data: Distribution,
}>();

</script>

<template>
    <n-descriptions :column="1">
        <template #header>
            <n-button
                text
                tag="a"
                :href="`https://pypi.org/project/${data.release.project}/${data.release.version}/`"
                target="_blank"
                type="primary"
                style="font-size: x-large;"
            >{{ data.release }}</n-button>
        </template>
        <n-descriptions-item>
            <template #label>Python Version</template>
            {{ data.pyversion }}
        </n-descriptions-item>
        <n-descriptions-item>
            <template #label>Top Level Modules</template>
            <n-space vertical>
                <span v-for="item in data.topModules" :key="item">{{ item }}</span>
            </n-space>
        </n-descriptions-item>
    </n-descriptions>
</template>
